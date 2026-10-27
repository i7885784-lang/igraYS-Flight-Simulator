from pathlib import Path
import shutil,json
lab=Path(__file__).resolve().parent;repo=Path('/workspace/igraYS-Flight-Simulator');out=repo/'reports/fighters-fg-test-1';out.mkdir(parents=True,exist_ok=True)
for kind in ['su27','mig29']:
 dst=out/kind;dst.mkdir(exist_ok=True);s=lab/'checks'/(kind+'-inspect-release')
 assert json.loads((s/'results.json').read_text())['passed']
 for p in s.glob('*.png'):shutil.copy2(p,dst/p.name)
 shutil.copy2(s/'game.log',dst/'inspection-game.log')
 for case in ['gear','canopy','controls','brake','engine']:
  src=lab/'checks'/f'{kind}-{case}-release';assert json.loads((src/'results.json').read_text())['passed']
  for fn in [case+'.mp4','results.json','game.log','run.script','start.yfs']:
   target=dst/(fn if fn==case+'.mp4' else case+'-'+fn);shutil.copy2(src/fn,target)
  for p in src.glob('*.png'):shutil.copy2(p,dst/p.name)
 before=lab/'checks'/(kind+'-before')
 for fn in ['top.png','front.png','side.png','orbit-135.png']:shutil.copy2(before/fn,dst/('before-'+fn))
for ident in ['SU-47_BERKUT','SU-57_FELON']:
 src=lab/'checks'/('preserved-'+ident);assert json.loads((src/'results.json').read_text())['passed'];shutil.copy2(src/'flight.png',out/('preserved-'+ident+'.png'));shutil.copy2(src/'results.json',out/('preserved-'+ident+'.json'))
for fn in ['validation.json','evidence-checks.json','license-audit.json','source-rebuild-checks.json','package-checks.json','sources-checks.json']:
 shutil.copy2(lab/fn,out/fn)
shutil.copy2(lab/'model-source/model-stats.json',out/'model-stats.json')
for fn in ['build32-final.log','build64-final.log']:shutil.copy2(lab/fn,out/fn)
text='''# Су-27 и МиГ-29 — новая геометрия, тест №1

[**Скачать игру — Windows 32-bit**](../../downloads/YSFlight_Fighters_FG_Test_1_32bit.zip?raw=true) · [**Полные исходники**](../../downloads/YSFlight_Fighters_FG_Test_1_Sources.zip?raw=true)

Распаковать всю папку отдельно, запустить **ysflight32_gl1.exe**. В «Новом полёте» выбрать **SU-27_FLANKER** или **MIG-29_FULCRUM**. Можно загрузить включённые `su27_Test.yfs` / `mig29_Test.yfs` для воздушного старта.

Заменены геометрия и внешние механизмы обоих самолётов. Основа этой отдельной версии — **Су-47 №1**, продолжающий **Су-57 №2**. Су-47 и Су-57 сохранены: их пять основных файлов совпали побайтно, оба отдельно загружены в полёт. Старые сборки и закреплённый указатель основы не перезаписаны. Раздел лицензий в интерфейс не добавлен.

| Су-27 в игре | МиГ-29 в игре |
|---|---|
| ![](su27/orbit-135.png) | ![](mig29/orbit-135.png) |

Геометрия взята из **FGMEMBERS/Su-27** и **FGMEMBERS/MiG-29**, точные версии — в [реестре ресурсов](license-audit.json). Окраска, полигонные звёзды и материалы свои. Чужие текстуры, звуки, эффекты и игровые системы FlightGear не используются. Вариант МиГ-29 — **9-12A**: взят `mesh_airframe.ac`, который действительно подключён в `Mig-29.xml` выбранного репозитория; старый `Mig-29.ac` поверх него не накладывается.

Работают шасси и створки, фонари, рули и закрылки, воздушные тормоза, включение/выключение форсажа. У Су-27 подключены флапероны и цельноповоротные стабилизаторы, у МиГ-29 — отдельные элероны, закрылки, предкрылки и стабилизаторы. Су-27 имеет спинной щиток с связанной опорой, МиГ-29 — верхний и нижний тормозные щитки. Сопла обычные, без неподтверждённого отклонения.

Исправлены неподвижные дубликаты подвижных деталей Су-27, пропавшее стекло фонаря, положение сложенных основных стоек без отрыва от шарниров, сквозные участки кабины и сопел, расположение звёзд и ссылка на дальнюю модель Су-27. У Су-27 вырезаны реальные ниши и добавлены створки из снятой обшивки; у МиГ-29 использованы исходные отдельные ниши/створки. Низ освещается солнцем; светятся только факелы.

| Видео реальных клавиш | Су-27 | МиГ-29 |
|---|---|---|
| Шасси и створки, полный цикл **G** | [Смотреть](su27/gear.mp4?raw=true) | [Смотреть](mig29/gear.mp4?raw=true) |
| Фонарь, **Alt+5** на земле | [Смотреть](su27/canopy.mp4?raw=true) | [Смотреть](mig29/canopy.mp4?raw=true) |
| Рули и закрылки, стрелки / Z / C / F / R | [Смотреть](su27/controls.mp4?raw=true) | [Смотреть](mig29/controls.mp4?raw=true) |
| Воздушный тормоз, **B** | [Смотреть](su27/brake.mp4?raw=true) | [Смотреть](mig29/brake.mp4?raw=true) |
| Газ и форсаж, **Q / Tab / A** | [Смотреть](su27/engine.mp4?raw=true) | [Смотреть](mig29/engine.mp4?raw=true) |

[**Все ракурсы, сверху/спереди/сбоку, сравнение до/после и положения механизмов**](INSPECTION.md)

Проверены круговые виды сверху и снизу, крайние и промежуточные положения в обе стороны, реальные клавиши и стоянка на земле. Журналы подтвердили циклы **0 → 1 → 0**, оба знака рулей, включение и выключение форсажа. Видео полностью декодированы, десять файлов моделей независимо пересобраны с побайтным совпадением; ZIP прошёл CRC и отдельную распаковку.

**Границы проверки:** игровые проверки выполнены Win64 EXE под **Wine/Xvfb**. ZIP содержит производственный **Win32 GUI EXE**; запуск на настоящей **Windows 10 x86 здесь не подтверждён**. Кинематика, аэродинамика и форма столкновений — игровые приближения; осмотр не доказывает отсутствие любых пересечений во всех условиях. Сопла в этой версии имеют фиксированную геометрию; отдельная анимация раскрытия лепестков не заявляется. Первая персона использует штатные приборы, новой интерактивной кабины нет; дальняя геометрия совпадает с основной. Полный старый набор сценариев ИИ не повторялся.

**Авторство и GPL-2.0:** Су-27 — Lee Elliott, StuartC, VooDoo; МиГ-29 — Detlef Faber, Gary R. Neely. Лицензии, редактируемые оригиналы и конвертер включены в `aircraft/fighters-fg-source/` и [GitHub](../../changes/fighters-fg-test-1/model-source/NOTICE.txt). Неопределённый CC-пилот Су-27 исключён. Проверка происхождения опирается на опубликованные сведения авторов, без независимой экспертизы каждого элемента. Су-47/Су-57 сохраняют свои лицензии.

[Проверки геометрии](validation.json) · [Клавиши и видео](evidence-checks.json) · [ZIP](package-checks.json) · [Пересборка](source-rebuild-checks.json) · [Исходники движка](sources-checks.json) · [Как повторить](../../changes/fighters-fg-test-1/README.md)
'''
(out/'REPORT.md').write_text(text)
parts=['# Игровые снимки: Су-27 / МиГ-29\n\nВсе кадры получены из игры. Круговые виды и сравнение сняты на паузе игровой камерой; кадры механизмов — во время живых циклов реальными клавишами.\n\n[Короткий отчёт и ZIP](REPORT.md).\n']
for k,title in [('su27','Су-27'),('mig29','МиГ-29')]:
 parts+=['\n## '+title+'\n\n','| Вид | До: прежняя модель | После: новая геометрия |\n|---|---|---|\n']
 for fn,label in [('top','Сверху'),('front','Спереди'),('side','Сбоку'),('orbit-135','Общий вид')]:parts.append(f'| {label} | ![]({k}/before-{fn}.png) | ![]({k}/{fn}.png) |\n')
 parts+=['\n### Круговой осмотр\n\n','| Направление | Сверху | Снизу |\n|---|---|---|\n']
 for h in range(0,360,45):parts.append(f'| {h}° | ![]({k}/orbit-{h}.png) | ![]({k}/lower-{h}.png) |\n')
 parts+=['\n### Механизмы\n\n','| Состояние | Кадр |\n|---|---|\n']
 for case,label,at in [('gear','Выпуск: промежуточно','010'),('gear','Выпущено','040'),('gear','Уборка: промежуточно','090'),('gear','Убрано','140'),('canopy','Фонарь открыт, колёса на земле','040'),('canopy','Фонарь закрыт','150'),('brake','Тормоз выпущен','040'),('brake','Тормоз убран','140'),('engine','Форсаж включён','070'),('engine','Форсаж выключен','140')]:parts.append(f'| {label} | ![]({k}/{case}-{at}.png) |\n')
 parts+=['\n### Солнечное освещение\n\n',f'| Низ в тени | После переворота к солнцу |\n|---|---|\n| ![]({k}/bottom.png) | ![]({k}/inverted.png) |\n']
parts+=['\n## Сохранённые самолёты\n\n| Су-47 | Су-57 |\n|---|---|\n| ![](preserved-SU-47_BERKUT.png) | ![](preserved-SU-57_FELON.png) |\n']
(out/'INSPECTION.md').write_text(''.join(parts));print('Report exported',len(list(out.rglob('*'))),'paths')
