from pathlib import Path
import shutil,json,hashlib,html
from PIL import Image,ImageDraw
r=Path('/workspace/igraYS-Flight-Simulator');b=Path(__file__).parent;out=r/'reports/su30sm-natural-pass';out.mkdir(exist_ok=True);(out/'images').mkdir(exist_ok=True);(out/'checks').mkdir(exist_ok=True);comps=[]
for group in ['ground','air','overview']:
 cases=[v[0] for v in json.loads((b/'checks'/f'after-{group}'/'results.json').read_text())['frames']] if False else json.loads((b/'checks'/f'after-{group}'/'results.json').read_text())['frames']
 for name in cases:
  if group=='air' and name in ['canopy-open','brake-open']:continue # These legacy names actually set flap/elevator, not canopy/brake; use real native cycles instead.
  rec={'id':group+'-'+name}
  for variant,key in [('old-gap','old'),('before','before'),('after','after')]:
   f=b/'checks'/f'{variant}-{group}'/f'{name}.png'
   if f.exists():
    rel=f'images/{variant}-{group}-{name}.png';shutil.copy2(f,out/rel);rec[key]=rel
  comps.append(rec)
for group in ['old-gap-ground','before-ground','after-ground','old-gap-air','before-air','after-air','before-overview','after-overview','after-gear','after-canopy','after-brake','after-engine','after-orbit']:
 dest=out/'checks'/group;dest.mkdir(exist_ok=True)
 for f in (b/'checks'/group).iterdir():
  if f.suffix in ['.json','.log','.script','.yfs','.mp4'] or (group.startswith('after-') and group.split('-',1)[1] in ['gear','canopy','brake','engine','orbit'] and f.suffix=='.png'):shutil.copy2(f,dest/f.name)
for name in ['validation.json','repair-audit.json','motion.json','global-audit.json','surface-symmetry.json','whole-symmetry.json','rotate-scan.json','rotate-fine-scan.json','torque-radius-scan.json']:
 shutil.copy2(b/name,out/name)
for f in ['intakes-review.jpg','cycles-review.jpg']:shutil.copy2(b/f,out/f)
(out/'comparisons.json').write_text(json.dumps(comps,ensure_ascii=False,indent=2)+'\n')
hero=Image.new('RGB',(1950,380),'#e8edef');d=ImageDraw.Draw(hero)
for j,(v,label) in enumerate([('old-gap','Old: light gaps'),('before','Before: short close cap'),('after','After: deep dark channel')]):
 im=Image.open(b/'checks'/f'{v}-ground'/'left-match.png').crop((0,200,650,545));hero.paste(im,(650*j,35));d.text((650*j+10,12),label,fill='black')
hero.save(out/'intake-comparison.jpg',quality=93)
body='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Су-30СМ — глубокие каналы</title><style>body{font:16px system-ui;max-width:1400px;margin:30px auto;padding:0 20px;background:#edf1f4;color:#132431}img{width:100%;height:auto}section{background:white;padding:18px;margin:20px 0;border-radius:8px}.row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}figure{margin:0}video{max-width:100%}a{color:#1756a9}@media(max-width:760px){.row{grid-template-columns:1fr}}</style><h1>Су-30СМ: более глубокий впускной канал</h1><p>Изменены только два IntakeDuct. Внешняя окраска и все анимационные узлы сохранены. Это улучшение впуска, а не заявление об устранении всех старых дефектов самолёта.</p><p><a href="REPORT_RU.md">Технический отчёт</a> · <a href="Su30SM_NaturalIntake_Report_RU.pdf">PDF</a> · <a href="validation.json">Проверка геометрии</a> · <a href="global-audit.json">Общий осмотр</a></p><p>Слева — старая EA3d с просветами, по центру — текущая ECEE, справа — новая c71a. Это реальные игровые кадры Win64/OpenGL под Wine, без ретуши.</p><img src="intake-comparison.jpg">'''
for c in comps:
 body+='<section><h2>'+html.escape(c['id'])+'</h2><div class="row">'
 for k,label in [('old','Старая с просветом'),('before','До'),('after','После')]:
  if k in c:body+=f'<figure><a href="{c[k]}"><img loading="lazy" src="{c[k]}"></a><figcaption>{label}</figcaption></figure>'
 body+='</div></section>'
body+='<h2>Реальные циклы в игре</h2><p>G — выпуск/уборка; Alt+5 — фонарь; B — аэротормоз; сопла/форсаж — изменение тяги. Посмотрены последовательности кадров, логи и крупные планы. Расчёт 201 позы не заменяет непрерывную проверку всех возможных условий.</p>'
for c in ['gear','canopy','brake','engine','orbit']:body+=f'<section><h3>{c}</h3><video controls preload="metadata" src="checks/after-{c}/{c}.mp4"></video></section>'
body+='</html>';(out/'index.html').write_text(body)
print('comparison sets',len(comps),'images',len(list((out/'images').glob('*.png'))))
