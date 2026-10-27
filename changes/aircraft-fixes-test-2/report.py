from pathlib import Path
import shutil,json
lab=Path(__file__).resolve().parent;repo=Path('/workspace/igraYS-Flight-Simulator');out=repo/'reports/aircraft-fixes-test-2';out.mkdir(parents=True,exist_ok=True)
for kind,folder in [('su27','su27-final-overview'),('mig29','mig29-intake-update'),('su57','su57-overview')]:
 d=out/kind;d.mkdir(exist_ok=True);src=lab/'checks'/folder
 for p in src.glob('*.png'):shutil.copy2(p,d/p.name)
 shutil.copy2(src/'results.json',d/'overview-checks.json')
for kind,folder,case in [('su27','su27-release-gear','gear'),('mig29','mig29-release-gear','gear'),('su27','su27-final-brake','brake'),('su57','su57-canopy','canopy')]:
 src=lab/'checks'/folder;d=out/kind
 shutil.copy2(src/(case+'.mp4'),d/(case+'.mp4'));shutil.copy2(src/'results.json',d/(case+'-states.json'));shutil.copy2(src/'game.log',d/(case+'-game.log'))
 for at in ['010','040','090','140','150']:
  p=src/(case+'-'+at+'.png')
  if p.exists():shutil.copy2(p,d/p.name)
for p in (lab/'checks/mig29-release-ground').glob('*.png'):shutil.copy2(p,out/'mig29'/p.name)
shutil.copy2(lab/'checks/preserved-su47/flight.png',out/'preserved-su47.png')
for fn in ['validation.json','evidence-checks.json','source-rebuild-checks.json','package-checks.json','sources-checks.json']:
 shutil.copy2(lab/fn,out/fn)
shutil.copy2(lab/'references/access.json',out/'reference-access.json');shutil.copy2(lab/'model-source/model-stats.json',out/'model-stats.json')
for fn in ['build32.log','build64.log']:shutil.copy2(lab/fn,out/fn)
(out/'REPORT.md').write_text('''# Исправления самолётов — тест №2

[**Скачать игру Windows 32-bit**](../../downloads/YSFlight_Aircraft_Fixes_Test_2_32bit.zip?raw=true) · [Исходники](../../downloads/YSFlight_Aircraft_Fixes_Test_2_Sources.zip?raw=true)

Распаковать отдельно, запустить **ysflight32_gl1.exe**. Старые версии сохранены.

- **Су-27:** переделаны складывание стоек, поворот колёс, ниши и створки. Убранные детали находятся внутри закрытых ниш и не скрываются искусственно. Створки открываются перед движением стоек; большие крышки разделены на меньшие. Укорочены тормозной щиток и его привод. Ракеты на законцовках вынесены на боковые направляющие.
- **МиГ-29:** переделаны шасси и створки, колесо убирается внутрь. В полёте воздухозаборники открыты. На земле при малой скорости действуют защитные экраны и открываются верхние жалюзи — это отдельное наземное состояние.
- **Су-57:** в эту игру действительно включена поздняя ревизия с закрытой обшивкой за креслом и четырьмя пилонами. Дополнительно расширены стыки задней площадки и подогнаны опоры пилонов.

**Су-47 сохранён без изменения файлов модели.** Авторство и лицензии включены; нового раздела в интерфейсе нет.

| Су-27: шасси убраны | МиГ-29: шасси убраны |
|---|---|
| ![](su27/gear-140.png) | ![](mig29/gear-140.png) |

**Видео реальных клавиш:** [шасси Су-27](su27/gear.mp4?raw=true) · [шасси МиГ-29](mig29/gear.mp4?raw=true) · [тормоз Су-27](su27/brake.mp4?raw=true) · [фонарь Су-57](su57/canopy.mp4?raw=true).

**Крупные планы:** [боковое крепление](su27/tip-rail.png) · [открытые воздухозаборники](mig29/intake.png) · [кабина Су-57](su57/cockpit-front.png) · [его пилоны](su57/pylons.png). На фото — штатные проверочные ракеты YSFlight.

В итоговый набор вошли общий осмотр каждого самолёта и целевые проверки исправленных мест. Выпуск/уборка и фонарь прошли **0 → 1 → 0**, включая промежуточные положения. Проверены размещение всех убранных узлов в нишах и проход колёс через проёмы; четыре видео декодированы. Все 15 файлов моделей независимо пересобраны с побайтным совпадением. ZIP проверен и отдельно распакован.

**Ограничения:** проверка игры — Win64/Wine; настоящая Windows 10 x86 здесь не проверена. Ниши, обтекатели и кинематика адаптированы для игры, заводская точность не заявляется. Повторы запросов к внешним сайтам и альтернативам дали HTTP 403; доступны авторские исходники FlightGear.

[Общие ракурсы](VIEWS.md) · [Геометрия](validation.json) · [Целевые проверки](evidence-checks.json) · [ZIP](package-checks.json) · [Исходники и лицензии](../../changes/aircraft-fixes-test-2/)
''')
s=['# Общий осмотр\n\nКадры настоящей игры на паузе. Циклы механизмов в отчёте сняты при работающей симуляции.\n\n[Вернуться к короткому отчёту](REPORT.md)\n']
for k,title in [('su27','Су-27'),('mig29','МиГ-29'),('su57','Су-57')]:
 s.append('\n## '+title+'\n\n| Сверху | Спереди |\n|---|---|\n'+f'| ![]({k}/top.png) | ![]({k}/front.png) |\n\n| Сбоку | Снизу |\n|---|---|\n| ![]({k}/side.png) | ![]({k}/bottom.png) |\n')
(out/'VIEWS.md').write_text(''.join(s));print('Short report and selected media exported')
