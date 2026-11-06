from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import re,html,json
r=Path('/workspace/igraYS-Flight-Simulator/reports/su30sm-intake-depth')
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DV-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold',italic='DV',boldItalic='DV-Bold')
s=getSampleStyleSheet()
for st in s.byName.values():st.fontName='DV';st.leading=max(getattr(st,'leading',14),14)
s['BodyText'].fontSize=9;s['BodyText'].leading=13
s.add(ParagraphStyle(name='SmallCell',fontName='DV',fontSize=7,leading=10))
def para(t,style='BodyText'):
 t=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',t);t=html.escape(t);t=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',t);t=t.replace('`','');return Paragraph(t,s[style])
story=[];lines=(r/'REPORT_RU.md').read_text().splitlines();i=0
while i<len(lines):
 line=lines[i].strip()
 if line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].strip().startswith('|'):
   cells=lines[i].strip().strip('|').split('|')
   if not all(set(c.strip())<=set('-: ') for c in cells):rows.append([para(c.strip(),'SmallCell') for c in cells])
   i+=1
  t=Table(rows,colWidths=[(487)/len(rows[0])]*len(rows[0]),repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.lightgrey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7edf0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5)]));story.extend([t,Spacer(1,10)]);continue
 if line:
  if line.startswith('#'):n=len(line)-len(line.lstrip('#'));story.append(para(line[n:].strip(),'Heading1' if n==1 else 'Heading2'))
  else:story.append(para(line))
  story.append(Spacer(1,5))
 i+=1
story.extend([PageBreak(),para('Приложение: 18 сравнений до и после','Heading1'),para('Оригинальные игровые кадры без ретуши. Следующие страницы: верхний кадр — до, нижний — после. Видео приложены отдельно в ZIP, один файл MP4.')])
for p in json.loads((r/'comparisons.json').read_text()):
 story.extend([PageBreak(),para(p['id'],'Heading2')])
 for key,label in [('before','До'),('after','После')]:story.extend([para(label),Image(str(r/p[key]),width=453.33,height=340),Spacer(1,3)])
def footer(c,d):
 c.setFont('DV',8);c.drawString(45,22,'Су-30СМ • Визуальная проверка');c.drawRightString(550,22,str(d.page))
doc=SimpleDocTemplate('/workspace/igraYS-Flight-Simulator/reports/su30sm-intake-depth/Su30SM_IntakeDepth_Report_RU.pdf',pagesize=(595,842),leftMargin=54,rightMargin=54,topMargin=32,bottomMargin=32,title='Су-30СМ — отчёт и 18 сравнений',author='Project visual verification')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
