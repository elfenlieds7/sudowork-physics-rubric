"""Generate the architecture, module details and API references from one JSON source."""
import argparse
import asyncio
from html import escape
import json
from pathlib import Path
import re

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'deliverables/architecture'


def read_model():
    data = json.loads((BASE / 'local-training.data.json').read_text(encoding='utf-8'))
    modules = {module['id']: module for module in data['modules']}
    if len(modules) != len(data['modules']) or data['document']['initial_module'] not in modules:
        raise ValueError('Module IDs must be unique and include the initial selection')
    endpoints = set(modules) | {'actor'}
    for module in modules.values():
        if not re.fullmatch(r'[a-z_]+', module['id']):
            raise ValueError('Unsafe module ID')
        if any(ref not in data['references'] for ref in module['sources'] + [item['ref'] for item in module['reuse']]):
            raise ValueError('Unknown component/source reference: ' + module['id'])
    seen = set()
    for api in data['interfaces']:
        if api['id'] in seen or api['owner'] not in modules or any(ref not in modules for ref in api['related']):
            raise ValueError('Invalid API reference: ' + api['id'])
        seen.add(api['id'])
    if any(edge['from'] not in endpoints or edge['to'] not in endpoints for edge in data['edges']):
        raise ValueError('Graph edge references an unknown module')
    if any(ref not in modules for phase in data['phases'] for ref in phase['modules']):
        raise ValueError('Implementation phase references an unknown module')
    return data, modules


def module_button(module, label=None, index=False, selected=False):
    text, code = escape(label or module['short_title']), escape(module['code'])
    content = f'<span>{code}</span>{text}' if index else f'{code} · {text}'
    return (f'<button type="button" class="{"module-select" if index else "module-ref"}" '
            f'data-select-module="{module["id"]}" aria-controls="panel-{module["id"]}"'
            + (f' aria-pressed="{str(selected).lower()}"' if index else '') + f'>{content}</button>')


def source_link(ref):
    return f'<a href="{escape(ref["url"], quote=True)}" target="_blank" rel="noopener">{escape(ref["title"])}</a>'


def graph_source(data):
    lines = ['%% Generated from local-training.data.json; edit the JSON source.', 'flowchart TB',
             '    actor["研发 AI／研究人员"]', '    subgraph LAN["本地可信环境 · DGX Spark 等算力"]']
    for module in data['modules']:
        libraries = list(dict.fromkeys(data['references'][item['ref']]['label'] for item in module['reuse']))
        owned = [api['id'] for api in data['interfaces'] if api['owner'] == module['id']]
        label = [f'{module["code"]} · {module["title"]}']
        if libraries:
            label.append(' · '.join(libraries))
        label.append(' / '.join(owned) if owned else module['diagram_note'])
        label.append(module['short_status'])
        text = '\n'.join(label).replace('"', '&quot;')
        lines.append(f'      {module["id"]}["{text}"]')
    lines.append('    end')
    for edge in data['edges']:
        arrow = '<-->' if edge.get('bidirectional') else '-->'
        label = '|"' + edge['label'] + '"|' if edge.get('label') else ''
        lines.append(f'    {edge["from"]} {arrow}{label} {edge["to"]}')
    lines += ['    classDef compute fill:#e6f0eb,stroke:#33715a,color:#183c2c',
              '    classDef private fill:#f7eddb,stroke:#ac8745,color:#654a1c']
    for kind in ('compute', 'private'):
        lines.append('    class ' + ','.join(m['id'] for m in data['modules'] if m['kind'] == kind) + ' ' + kind)
    return '\n'.join(lines) + '\n'


def list_items(items):
    return '<ul>' + ''.join('<li>' + escape(text) + '</li>' for text in items) + '</ul>'


def module_panels(data, modules):
    panels = []
    for module in data['modules']:
        key = module['id']
        hidden = '' if key == data['document']['initial_module'] else ' hidden'
        parts = [f'<section id="panel-{key}" class="module-panel" data-module-panel="{key}" '
                 f'data-node-id="architecture/module/{key}"{hidden}>',
                 f'<span class="module-code">{escape(module["code"])}</span><h3>{escape(module["title"])}</h3>',
                 f'<span class="module-status">{escape(module["status"])}</span>',
                 f'<p class="purpose">{escape(module["purpose"])}</p>']
        if module['reuse']:
            parts.append('<h4>可以复用</h4><ul>')
            parts.extend('<li>' + source_link(data['references'][item['ref']]) + '：' + escape(item['text']) + '</li>' for item in module['reuse'])
            parts.append('</ul>')
        else:
            parts.append('<p class="module-note">本模块按已约定的职责补齐；目前没有确认可直接替代整个模块的现成组件。</p>')
        parts.extend(['<h4>需要补齐或验证</h4>', list_items(module['requirements'])])
        owned = [api for api in data['interfaces'] if api['owner'] == key]
        if owned:
            parts.append('<h4>本模块接口 · 拟定职责，尚未部署</h4>')
            for api in owned:
                parts.append(f'<details class="api-card" data-api="{api["id"]}" open>'
                             f'<summary><code>{escape(api["id"])}</code></summary><dl>'
                             f'<dt>输入</dt><dd>{escape(api["input"])}</dd>'
                             f'<dt>返回证据</dt><dd>{escape(api["output"])}</dd></dl></details>')
        related = [api for api in data['interfaces'] if key in api['related']]
        if related:
            parts.append('<h4>相关接口 · 点击查看负责模块的定义</h4><div class="api-references">')
            parts.extend(module_button(modules[api['owner']], api['id']) for api in related)
            parts.append('</div>')
        parts.extend('<p class="module-note">' + escape(note) + '</p>' for note in module['notes'])
        if module['sources']:
            parts.append('<h4>公开依据</h4><div class="source-links">')
            parts.extend(source_link(data['references'][ref]) for ref in module['sources'])
            parts.append('</div>')
        parts.append('</section>')
        panels.append(''.join(parts))
    return '\n'.join(panels)


def interactive_svg(svg, modules, initial):
    found = set()
    # Preserve Mermaid's foreignObject HTML. XML reserialization would prefix
    # HTML tags and break line breaks when this SVG is embedded into an HTML page.
    def annotate(match):
        attributes = match['attributes']
        classes = re.search(r'\bclass="([^"]*)"', attributes)
        identity = re.search(r'\bid="([^"]*)"', attributes)
        if not classes or 'node' not in classes[1].split() or not identity:
            return match[0]
        node = re.search(r'(?:^|-)flowchart-([a-z_]+)-\d+$', identity[1])
        if not node or node[1] not in modules:
            return match[0]
        key = node[1]
        found.add(key)
        if key == initial:
            attributes = attributes[:classes.start(1)] + classes[1] + ' is-selected' + attributes[classes.end(1):]
        extra = {'data-module': key, 'tabindex': '0', 'role': 'button', 'aria-controls': 'panel-' + key,
                 'aria-label': modules[key]['code'] + ' ' + modules[key]['title'] + '，查看组件与接口详情',
                 'aria-pressed': str(key == initial).lower()}
        return '<g' + attributes + ''.join(f' {attr}="{escape(value, quote=True)}"' for attr, value in extra.items()) + '>'
    result = re.sub(r'<g\b(?P<attributes>[^>]*)>', annotate, svg)
    if found != set(modules):
        raise ValueError(f'Generated SVG modules differ: found={sorted(found)}')
    return result


async def build(args):
    data, modules = read_model()
    source = graph_source(data)
    template = (BASE / 'local-training.template.html').read_text(encoding='utf-8')
    async with async_playwright() as p:
        launch = {'headless': True}
        if args.browser:
            launch['executable_path'] = str(args.browser)
        browser = await p.chromium.launch(**launch)
        page = await browser.new_page()
        await page.goto('about:blank')
        await page.add_script_tag(path=str(args.mermaid_js.resolve()))
        await page.evaluate('''() => mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'base',fontFamily:'PingFang SC,Microsoft YaHei,sans-serif',themeVariables:{fontSize:'17px',primaryColor:'#f0f3ee',primaryBorderColor:'#688574',primaryTextColor:'#21372f',lineColor:'#71877b',clusterBkg:'#fafbf8',clusterBorder:'#c3cfc2',edgeLabelBackground:'#ffffff'},flowchart:{htmlLabels:false,curve:'basis',nodeSpacing:24,rankSpacing:34}})''')
        svg = await page.evaluate('''async source => (await mermaid.render('local-training-diagram', source)).svg''', source)
        await browser.close()
    phases = []
    for index, phase in enumerate(data['phases'], 1):
        buttons = ''.join(module_button(modules[key]) for key in phase['modules'])
        phases.append(f'<article class="phase"><h3><span class="phase-number">0{index}</span>{escape(phase["title"])}</h3>'
                      f'<p>{escape(phase["text"])}</p><div>{buttons}</div></article>')
    document = data['document']
    replacements = {'TITLE': document['title'], 'VERSION': document['version'], 'UPDATED': document['updated'],
                    'LEAD': document['lead'], 'STATUS': document['status'], 'EVIDENCE_DATE': document['evidence_reviewed'],
                    'INITIAL_MODULE': document['initial_module']}
    replacements = {key: escape(value) for key, value in replacements.items()}
    replacements.update({'DIAGRAM': interactive_svg(svg, modules, document['initial_module']),
                         'MODULE_INDEX': ''.join(module_button(m, index=True, selected=m['id'] == document['initial_module']) for m in data['modules']),
                         'MODULE_OPTIONS': ''.join(f'<option value="{m["id"]}">{escape(m["code"] + " · " + m["short_title"])}</option>' for m in data['modules']),
                         'MODULE_PANELS': module_panels(data, modules), 'PHASES': ''.join(phases)})
    for key, value in replacements.items():
        token = '__' + key + '__'
        if token not in template:
            raise ValueError('Template does not reference generated field: ' + key)
        template = template.replace(token, value)
    if re.search(r'__[A-Z_]+__', template):
        raise ValueError('Unfilled template field')
    (BASE / 'local-training.mmd').write_text(source, encoding='utf-8')
    args.output.write_text(template, encoding='utf-8')
    print(f'Rendered v{document["version"]}: {len(modules)} modules, {len(data["interfaces"])} API contracts, one JSON source')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mermaid-js', type=Path, required=True)
    parser.add_argument('--browser', type=Path)
    parser.add_argument('--output', type=Path, default=BASE / 'local-training.html')
    asyncio.run(build(parser.parse_args()))


if __name__ == '__main__':
    main()
