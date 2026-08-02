"""生成 5 份试卷的 v4 预测得分率 vs 实际得分率数据 · 输出 HTML 可以直接嵌入.

对每份试卷:
- 按 question_id 内在顺序 (position 递增) 排序
- 计算 v4 预测得分率
- emit JSON 数据 · 用 Chart.js 渲染 line chart

Output: 单个 <script> + 5 个 <canvas> 的 HTML fragment.
"""
import csv
import json
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "labeled" / "combined_scored_v3.csv"
OUT_HTML_FRAGMENT = REPO_ROOT / "analysis" / "difficulty_curves_fragment.html"

BASE = ["concept", "reasoning", "novelty", "visual", "modeling",
        "position", "is_open", "topic_mech", "topic_em",
        "textbook_scene_degree", "textbook_pattern_degree"]

NEW = ["transfer_cost", "is_last_quarter", "earlier_load"]

ALL = BASE + NEW


def transpose(M):
    return [[M[i][j] for i in range(len(M))] for j in range(len(M[0]))]


def matmul(A, B):
    m, k, n = len(A), len(A[0]), len(B[0])
    return [[sum(A[i][p] * B[p][j] for p in range(k)) for j in range(n)] for i in range(m)]


def inv(M):
    n = len(M)
    A = [row[:] + [1 if i == j else 0 for j in range(n)] for i, row in enumerate(M)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(A[r][col]))
        A[col], A[pivot] = A[pivot], A[col]
        pv = A[col][col]
        A[col] = [x / pv for x in A[col]]
        for r in range(n):
            if r == col:
                continue
            factor = A[r][col]
            A[r] = [A[r][c] - factor * A[col][c] for c in range(2 * n)]
    return [row[n:] for row in A]


def fit_ols(X, y):
    Xb = [[1.0] + row for row in X]
    XT = transpose(Xb)
    XTX = matmul(XT, Xb)
    XTy = matmul(XT, [[v] for v in y])
    return [b[0] for b in matmul(inv(XTX), XTy)]


def load():
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            row = {"qid": r["question_id"], "paper": r["paper_id"], "y": float(r["score_rate"])}
            for f_name in BASE:
                row[f_name] = float(r[f_name])
            row["position"] = float(r["position"])
            rows.append(row)

    for r in rows:
        s = r["textbook_scene_degree"]
        p = r["textbook_pattern_degree"]
        r["transfer_cost"] = max(0.0, p - s)
        r["is_last_quarter"] = 1.0 if r["position"] > 0.75 else 0.0

    by_paper = {}
    for r in rows:
        by_paper.setdefault(r["paper"], []).append(r)
    for pdata in by_paper.values():
        s = sorted(pdata, key=lambda r: r["position"])
        for i, r in enumerate(s):
            r["earlier_load"] = mean(e["concept"] for e in s[:i]) if i else 0.0
    return rows


def main():
    rows = load()

    # Fit v4 全数据模型
    y = [r["y"] for r in rows]
    X = [[r[f] for f in ALL] for r in rows]
    beta = fit_ols(X, y)

    # 预测
    for r in rows:
        x = [r[f] for f in ALL]
        r["pred"] = beta[0] + sum(beta[i+1] * x[i] for i in range(len(ALL)))
        r["pred"] = max(0.0, min(1.05, r["pred"]))  # clip 到合理范围

    # 每份试卷 · 按 position 排序
    papers_data = {}
    for paper in sorted({r["paper"] for r in rows}):
        pdata = sorted([r for r in rows if r["paper"] == paper], key=lambda r: r["position"])
        papers_data[paper] = [{
            "qid": r["qid"],
            "actual": round(r["y"], 3),
            "pred": round(r["pred"], 3),
            "resid": round(r["y"] - r["pred"], 3),
        } for r in pdata]

    # 找 MCQ / 实验题 / 大题 分界
    # MCQ (is_open=0): 通常 qid 是 "1"-"14"
    # 15-16 大概 15-1, 15-2, 16-1, 16-2 ... (实验题, 有分问)
    # 17-20 是大题 (17-1, 17-2, 17-3 ... 20-1, 20-2, 20-3)
    # 用 qid 首字符判断段:
    def segment_boundaries(items):
        """返回 (选择题末尾index, 实验题末尾index) 的 position 值"""
        mcq_end, exp_end = None, None
        for i, it in enumerate(items):
            qid = it["qid"]
            head = qid.split("-")[0]
            try:
                num = int(head)
            except:
                continue
            if num == 14 and mcq_end is None:
                mcq_end = i
            if num == 16:
                exp_end = i  # 每次更新, 结果是最后一个 16
        return mcq_end, exp_end

    for paper, items in papers_data.items():
        mcq_end, exp_end = segment_boundaries(items)
        # 用 (i + 0.5) / total 做界线, 让线画在两点之间
        n = len(items)
        papers_data[paper] = {
            "items": items,
            "seg_mcq_end": mcq_end + 0.5 if mcq_end is not None else None,
            "seg_exp_end": exp_end + 0.5 if exp_end is not None else None,
        }

    # Emit HTML
    html_parts = ['<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>']
    html_parts.append('<style>.chart-wrap{margin:16px 0;padding:12px;background:#fff;border:1px solid #d0ccc0;border-radius:4px}.chart-wrap h4{margin:0 0 8px;font-size:14px;color:#2b5a8b}.chart-canvas{width:100%!important;height:280px!important}</style>')

    paper_labels = {
        "gaokao_2024": "高考 2024",
        "gaokao_2025": "高考 2025",
        "xicheng_2024": "西城 2024 一模",
        "xicheng_2025": "西城 2025 一模",
        "xicheng_2026": "西城 2026 一模 (您本届)",
    }

    for i, paper in enumerate(sorted(papers_data.keys())):
        d = papers_data[paper]
        canvas_id = f"chart_{paper}"
        html_parts.append(f'<div class="chart-wrap"><h4>{paper_labels[paper]}</h4><canvas id="{canvas_id}" class="chart-canvas"></canvas></div>')

    # 一个大的 <script> 生成所有 charts
    charts_config = {}
    for paper, d in papers_data.items():
        items = d["items"]
        charts_config[paper] = {
            "labels": [it["qid"] for it in items],
            "actual": [it["actual"] for it in items],
            "pred": [it["pred"] for it in items],
            "seg_mcq_end": d["seg_mcq_end"],
            "seg_exp_end": d["seg_exp_end"],
        }

    script = f"""<script>
(function() {{
  var configs = {json.dumps(charts_config, ensure_ascii=False)};
  function makeChart(canvasId, cfg) {{
    var ctx = document.getElementById(canvasId).getContext('2d');
    var annotations = [];
    // 三段递增分界线
    if (cfg.seg_mcq_end != null) {{
      annotations.push({{ type: 'line', xMin: cfg.seg_mcq_end, xMax: cfg.seg_mcq_end,
        borderColor: 'rgba(200,65,15,0.4)', borderWidth: 1.5, borderDash: [4,4] }});
    }}
    if (cfg.seg_exp_end != null && cfg.seg_exp_end != cfg.seg_mcq_end) {{
      annotations.push({{ type: 'line', xMin: cfg.seg_exp_end, xMax: cfg.seg_exp_end,
        borderColor: 'rgba(200,65,15,0.4)', borderWidth: 1.5, borderDash: [4,4] }});
    }}
    new Chart(ctx, {{
      type: 'line',
      data: {{
        labels: cfg.labels,
        datasets: [
          {{ label: '实际得分率', data: cfg.actual, backgroundColor: '#c8410f',
             borderColor: 'rgba(200,65,15,0.5)', borderWidth: 1, pointRadius: 3.5,
             pointStyle: 'circle', tension: 0, spanGaps: true, fill: false }},
          {{ label: 'v4 预测得分率', data: cfg.pred, backgroundColor: 'transparent',
             borderColor: '#2b5a8b', borderWidth: 2, pointRadius: 2, pointBackgroundColor: '#2b5a8b',
             tension: 0.15, fill: false, borderDash: [] }},
        ]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false, animation: false,
        plugins: {{
          legend: {{ position: 'top', labels: {{ font: {{ size: 11 }}, boxWidth: 20 }} }},
          tooltip: {{ mode: 'index', intersect: false }},
        }},
        scales: {{
          x: {{ title: {{ display: true, text: '题号 (按卷面顺序)', font: {{ size: 11 }} }},
                ticks: {{ font: {{ size: 10 }}, maxRotation: 60, minRotation: 45 }} }},
          y: {{ min: 0, max: 1.05, title: {{ display: true, text: '得分率', font: {{ size: 11 }} }},
                ticks: {{ font: {{ size: 10 }}, stepSize: 0.2 }} }},
        }},
      }}
    }});
    // 红色分界线 (Chart.js 4 需要 annotation plugin, 简化: 手绘用 canvas 事件)
  }}
  Object.keys(configs).forEach(function(k) {{
    makeChart('chart_' + k, configs[k]);
  }});
}})();
</script>"""
    html_parts.append(script)

    OUT_HTML_FRAGMENT.write_text("\n".join(html_parts), encoding="utf-8")
    print(f"Wrote {OUT_HTML_FRAGMENT.relative_to(REPO_ROOT)}")

    # 打一些统计: 每份试卷预测是否符合 三段递增
    print("\n每份试卷 · 三段递增结构 · 预测得分率检查:")
    for paper in sorted(papers_data.keys()):
        items = papers_data[paper]["items"]
        mcq_end = papers_data[paper]["seg_mcq_end"]
        exp_end = papers_data[paper]["seg_exp_end"]
        if mcq_end is None or exp_end is None:
            continue
        mcq_end_int = int(mcq_end)
        exp_end_int = int(exp_end)
        seg1 = items[:mcq_end_int+1]  # 选择题
        seg2 = items[mcq_end_int+1:exp_end_int+1]  # 15-16 实验
        seg3 = items[exp_end_int+1:]  # 17-20 大题
        pred_mean = lambda seg: mean(x["pred"] for x in seg) if seg else 0
        actual_mean = lambda seg: mean(x["actual"] for x in seg) if seg else 0
        print(f"  {paper}")
        print(f"    选择题 (1-14): 实际均 {actual_mean(seg1):.2f} / 预测均 {pred_mean(seg1):.2f}")
        print(f"    实验题 (15-16): 实际均 {actual_mean(seg2):.2f} / 预测均 {pred_mean(seg2):.2f}")
        print(f"    大题 (17-20): 实际均 {actual_mean(seg3):.2f} / 预测均 {pred_mean(seg3):.2f}")


if __name__ == "__main__":
    main()
