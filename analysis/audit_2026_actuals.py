"""Audit frozen pre-result predictions against the teacher's 2026 workbook.

Inputs and outputs containing actual rates stay in gitignored data/private.
Never refit predictions or fill missing observations to report this audit.
"""
import argparse,csv,hashlib,json,math,shutil,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import openpyxl

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'data/private/2026_validation';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,default=OUT/'2026_teacher_actuals.xlsx')
SOURCE=parser.parse_args().source
sys.stdout.reconfigure(encoding='utf-8')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read_csv(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
raw=read_csv(ROOT/'data/labeled/gaokao_2026_predictions.csv')
mod=read_csv(ROOT/'data/labeled/gaokao_2026_predictions_moderate.csv')
assert [r['question_id'] for r in raw]==[r['question_id'] for r in mod]
assert len(raw)==33
stored=OUT/'2026_teacher_actuals.xlsx'
if stored.exists():assert sha(stored)==sha(SOURCE),'Source changed; preserve versions separately'
else:shutil.copy2(SOURCE,stored)
w=openpyxl.load_workbook(stored,data_only=True,read_only=True)
observed={}
for q,points,rate in list(w.active.values)[1:]:
 if q is None:continue
 key=str(q).replace('_','-');assert key not in observed
 assert points>0 and 0<=rate<=1
 observed[key]={'points':float(points),'rate':float(rate)}
aliases={'18-1a':'18-1-1','18-1b':'18-1-2','19-2a':'19-2-1','19-2b':'19-2-2','20-2a':'20-2-1','20-2b':'20-2-2'}
# Official paper totals are 100. The supplied workbook omits these two leaves.
missing_points={'17-3':2,'19-2a':3}
rows=[]
for a,b in zip(raw,mod):
 q=a['question_id'];key=aliases.get(q,q);o=observed.get(key)
 assert o is not None or q in missing_points
 pts=o['points'] if o else missing_points[q]
 rows.append({'qid':q,'workbook_key':key,'points':pts,'actual':o['rate'] if o else None,'raw':float(a['predicted_score_rate']),'adjusted':float(b['predicted_score_rate']),'type':a['question_type'],'notes':a['notes']})
assert sum(r['points'] for r in rows)==100
matched=[r for r in rows if r['actual'] is not None]
assert len(matched)==31 and sum(r['points'] for r in matched)==95
counts=Counter(r['qid'].split('-')[0] for r in rows)
totals={'15':8,'16':10,'17':9,'18':9,'19':10,'20':12}
for r in rows:
 main=r['qid'].split('-')[0]
 r['old_points']=3 if r['type']=='mcq' else totals[main]/counts[main]
 if r['actual'] is not None:
  for name in ('raw','adjusted'):
   r[name+'_error_pp']=(r[name]-r['actual'])*100
   r[name+'_score_contribution']=r['points']*(r[name]-r['actual'])

def metrics(rs,name):
 pts=sum(r['points'] for r in rs);signed=sum(r['points']*(r[name]-r['actual']) for r in rs)
 return {'count':len(rs),'points_covered':pts,'actual_score':sum(r['points']*r['actual'] for r in rs),'predicted_score':sum(r['points']*r[name] for r in rs),'signed_score_error':signed,'unweighted_mae_pp':sum(abs(r[name]-r['actual']) for r in rs)*100/len(rs),'weighted_mae_pp':sum(r['points']*abs(r[name]-r['actual']) for r in rs)*100/pts,'weighted_bias_pp':signed*100/pts,'rmse_pp':math.sqrt(sum((r[name]-r['actual'])**2 for r in rs)/len(rs))*100}

grouped={}
for kind in ('mcq','fill','solve'):
 rs=[r for r in matched if r['type']==kind]
 grouped[kind]={n:metrics(rs,n) for n in ('raw','adjusted')}
rounding=[]
for q in range(15,21):
 rs=[r for r in matched if r['qid'].split('-')[0]==str(q)];parent=observed[str(q)]
 rounding.append({'main_q':q,'parent_points':parent['points'],'official_points':totals[str(q)],'matched_points':sum(r['points'] for r in rs),'parent_score':parent['points']*parent['rate'],'leaf_score':sum(r['points']*r['actual'] for r in rs),'difference_score':parent['points']*parent['rate']-sum(r['points']*r['actual'] for r in rs)})
known_actual=sum(r['points']*r['actual'] for r in matched)
changed=[r for r in matched if abs(r['raw']-r['adjusted'])>1e-8]
unchanged=[r for r in matched if abs(r['raw']-r['adjusted'])<=1e-8]
labels_a=read_csv(ROOT/'data/labeled/gaokao_2026_v24_labels.csv')
labels_b=read_csv(ROOT/'data/labeled/gaokao_2026_v24_labels_moderate.csv')
label_changes=[]
for a,b in zip(labels_a,labels_b):
 assert a['question_id']==b['question_id']
 delta={k:{'before':a[k],'after':b[k]} for k in a if a[k]!=b[k] and k not in ('notes','score_rate')}
 if delta:label_changes.append({'qid':a['question_id'],'changes':delta})
train=read_csv(ROOT/'data/labeled/v2_4_labels.csv')
cohort=read_csv(ROOT/'data/private/cohort_calibration.csv')
paired=[(float(r['xicheng_rate']),float(r['beijing_rate'])) for r in cohort if r['xicheng_rate'] and r['beijing_rate']]
audit={'created_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':sha(stored),'source_local_path':str(SOURCE),'missing':[{'qid':r['qid'],'inferred_points_from_official_total':r['points']} for r in rows if r['actual'] is None],'population_in_workbook':None,'leaf_matched_count':31,'covered_points':95,'known_actual_score':known_actual,'full_actual_score_bounds':[known_actual,known_actual+5],'known_rate_rounding_max_score_error':95*.005,'summary':{n:metrics(matched,n) for n in ('raw','adjusted')},'full_prediction_reweighting':{n:{'old_equal_within_question_weights':sum(r['old_points']*r[n] for r in rows),'provided_points_plus_inferred_missing_points':sum(r['points']*r[n] for r in rows)} for n in ('raw','adjusted')},'groups':grouped,'changed':{n:metrics(changed,n) for n in ('raw','adjusted')},'unchanged':{n:metrics(unchanged,n) for n in ('raw','adjusted')},'changed_question_count':len(changed),'label_changes':label_changes,'training_papers':dict(Counter(r['paper_id'] for r in train)),'previous_cohort_pairs':{'count':len(paired),'mean_xicheng_minus_beijing_pp':sum(x-b for x,b in paired)*100/len(paired),'not_applied_to_2026':'Workbook does not identify population; historical difference does not identify the 2026 population effect.'},'parent_vs_leaf_rounding':rounding,'largest_adjusted_errors':sorted(matched,key=lambda r:abs(r['adjusted_error_pp']),reverse=True)[:12],'all_rows':rows,'limits':['No new fit or calibration uses 2026 outcomes. Both predictions were stored before the supplied actuals.','Missing rates are not filled. Parent totals 17 and 19 cover 7 points each, not their complete official question totals.','15-3 uses the supplied 4-point aggregate; its two finer 2-point rows are not counted again. Other parent totals are likewise excluded from the 95-point sum.','Actual score rates are rounded to 2 decimals; summary is not a reported official overall mean.','Label vs model vs population effects cannot be uniquely separated without independent teacher labels and population information.','Prediction agreement alone does not establish accuracy.']}
(OUT/'audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
 cols=['qid','points','actual','raw','adjusted','raw_error_pp','adjusted_error_pp','raw_score_contribution','adjusted_score_contribution','type','notes'];writer=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
print(json.dumps({k:audit[k] for k in ('missing','leaf_matched_count','covered_points','known_actual_score','full_actual_score_bounds','summary','full_prediction_reweighting','groups','changed','unchanged','previous_cohort_pairs','largest_adjusted_errors')},ensure_ascii=False))
