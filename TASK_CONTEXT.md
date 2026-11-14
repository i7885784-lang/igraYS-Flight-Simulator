# Су-30СМ: локальные дефекты у основной ниши

Задача: убрать подтверждённые нижний зуб/складку и полосы корпуса внутри чёрной ниши; исследовать соседние стыки. Не делать глобальную переделку. Пользователь14ноября разрешил исправления после диагностики.

Рабочая копия /workspace/work/su30sm-local-skin, ветка fix/su30sm-confirmed-defects-20261114. База и откат work/large-panels/su30sm.dnm SHA91a201f3ca02d7c69345d197827b1567cedcc87edb51409ffc0006b8cc0ae61c. Старыйпубличныйrelease su30sm-large-panels-20261113 не менять. Итог work/confirmed-defects/release2.dnm SHA0af68b56600b92d45f5bdd41f7775a6787af38aa13f1887ab3f5c3c5bd936003. Предыдущие9d97/7114 и полные исходные оболочки ОТКЛОНЕНЫ: чёрная щель/незамкнутый микроторец. НЕ выпускать их, native43562108151 относится к пробе9d97.

Точные изменения: два MainBayFixedSkin — пространственный loft в передних25см между неизменной задней кромкой со створкой и реальным передним контуром F4. front_profile.py трассирует связанную3Dкромку, включая нависание (не Y(X,Z)). Внутренний профиль согласован со смещением кромки; вогнутый торец TrianglePSLG, численные микро-выемки исправлены. F4:6669face-блоков отсечены только в передней полосе и проёмах наружных основных створок, ниже настоящего потолка GearWell с12ммзащитой.113208face-блоков и все исходные вершиныF4 точные; новые куски — доказанные подмножества исходных. Другие159PCK,все162узла/STA/POS/родители точные, включая ВСЕ створки, стойки, колёса, ниши, впуск и анимации. Палитра/материалы сохранены.


Пути GitHub i7885784-lang/igraYS-Flight-Simulator:
- changes/su30sm-confirmed-defects/repair.py build_panel()/run(), front_profile.py extract(), bay_cut.py cut() — новый исходный алгоритм.
- changes/su30sm-large-panels/facet.py exterior()/Projected и changes/su30sm-local-skin/repair.py make_panel(), model-source/ — неизменные зависимости. Требования в local-skin/requirements.txt.
- check.py: сохранность + нормали/топология; check_self.py: самопересечения; прежний large-panels/check_motion.py:201поза.
- freeze.py: точные3патча; F4малыйface-deltaZIP, безповторнойзагрузкивсего23МБмеша. package.py: разныеPE32/PE32+архивы отпредыдущихLargePanelsZIP.
- windows_prepare.py/windows_check.py/windows-start.yfs — реальный запуск обоих PE на Windows2022, x86штатные LANDINGGEAR бездиагностическихкоманд.
- dist/su30sm-confirmed-defects/:3patchZIP+metadata. reports/su30sm-confirmed-defects/:отчёт/PNG/проверки.

Команды /workspace/work/venv/bin/python:
repair.py --baseline work/large-panels/su30sm.dnm --output work/confirmed-defects/release2.dnm
check.py --baseline BASE --candidate FINAL --output JSON
check_self.py FINAL JSON
changes/su30sm-large-panels/check_motion.py BASE FINAL OUTDIR
freeze.py BASE FINAL work/confirmed-defects/reproduced.audit.json dist/su30sm-confirmed-defects
package.py work/confirmed-packages work/large-downloaded

Проверки: итог0af68: обе оболочки замкнуты/Эйлер2/согласованы/0дублей/0вырожденных/0самопересечений (quality-release2/self-release2).201поза:808контактныхключейкакбыло,0новых/удалённых. Побайтоваяперегенерацияподтверждена. x64Wine:11парракурсов+живойGцикл, реальныеPNGоткрываютсядлясравнения. Промежуточныеполныереставрации и нормальнаяэкструзияотклонены, невыпускать. Нижнийзуб/полосы исчезли; тонкая фасеточная линия исходного корпуса местами видна, не объявлять весьсамолёт бездефектным. Опорастойки соединена — еёподъём не обоснован.

GitHubлокальныйGH_TOKENистёк: использовать подключённыеGitHubtools длязаписи; publicAPI/downloadчерезurllib/curl доступны. Созданаудалённаяветка;база8bac3003d73a20cf96ba829aaa805c6552071a59,tree f7b5765bf2f28c0ef92b3faf11d16dc598cb00b1. GitDataupdate_ref НЕ запускалActions; послеисходников создатьworkflow черезContentscreate_file.

Осталось: NativeWindows32/64 CI, открытькадры; окончательныепаспортасборок/ZIP;публикацияновогоrelease su30sm-confirmed-defects-20261114, скачать/проверитьархивы, датьдвепрямыессылки. Wine32неподдержанэтойсредой(syswow64 ntdll.dll c0000135);этоограничениесреды,неархитектурыигры.


Текущий статус: идёт свежая съёмка0af68 work/confirmed-defects/capture-publish.sh (до91a повторятьне надо). Новыйчёрныйтреугольникпробы9d97обнаруженприоткрытииclosedPNG иисправленнастоящим3Dстыком, некраской. Финальныеquality/selfуже0дефектов; motion-release иfreeze-release проверяются. Послезаморозкипатчей загрузитьтолькоизменённыефайлы; удалённыйheadb3009874c307519d3ed2e6f8ab0153c7dc33109d, создатьНОВЫЙworkflow native-final черезContents. Проверитьновый0af68 наWindows32/64, скачатьоткрытьPNG, затем package REQUIRE_NATIVE_CHECKS=1 иpublish. ТекущиефайлыREADME актуальны, package.py принимаетnative-32/64-results.json ивыпускблокируетсябезнихприREQUIRE_NATIVE_CHECKS=1.
