# Су-30СМ: локальные дефекты у основной ниши

Задача: убрать подтверждённые нижний зуб/складку и полосы корпуса внутри чёрной ниши; исследовать соседние стыки. Не делать глобальную переделку. Пользователь14ноября разрешил исправления после диагностики.

Рабочая копия /workspace/work/su30sm-local-skin, ветка fix/su30sm-confirmed-defects-20261114. База и откат work/large-panels/su30sm.dnm SHA91a201f3ca02d7c69345d197827b1567cedcc87edb51409ffc0006b8cc0ae61c. Старыйпубличныйrelease su30sm-large-panels-20261113 не менять. Итог work/confirmed-defects/final.dnm SHA9d97ef82d00577cc257013b730350873d46c5b86d502ed114599500a107a85ad.

Точные изменения: MainBayFixedSkin_Left/Right — только передняя полоса absX1.03..1.87,Z-.66..-.41, плавное сопряжение по неизменным переднему/заднему сечениям вместо узкой складки; плоская триангуляция, внутренний край отведён назад8мм. Убран численный передний выступ контура2мкм. Fuselage_0_4 — удалены150остаточных исходных полигонов только в проёмах наружных основных створок absX1.87..2.4,Z-3.38..-.41, ниже настоящего потолка GearWell с12ммзащитой. Новых полигоновF4нет,всеегоисходныевершиныточные. Другие159PCK и все162узла/STA/POS/родители точные, включая ВСЕ створки, стойки, колёса, ниши, воздухозаборники, материалы/анимации.

Пути GitHub i7885784-lang/igraYS-Flight-Simulator:
- changes/su30sm-confirmed-defects/repair.py build_panel()/run(), bay_cut.py cut() — новый исходный алгоритм.
- changes/su30sm-large-panels/facet.py exterior()/Projected и changes/su30sm-local-skin/repair.py make_panel(), model-source/ — неизменные зависимости. Требования в local-skin/requirements.txt.
- check.py: сохранность + нормали/топология; check_self.py: самопересечения; прежний large-panels/check_motion.py:201поза.
- freeze.py: точные3патча; F4малыйface-delta1954байтаZIP, безповторнойзагрузкивсего23МБмеша. package.py: разныеPE32/PE32+архивы отпредыдущихLargePanelsZIP.
- windows_prepare.py/windows_check.py/windows-start.yfs — реальный запуск обоих PE на Windows2022, x86штатные LANDINGGEAR бездиагностическихкоманд.
- dist/su30sm-confirmed-defects/:3patchZIP+metadata. reports/su30sm-confirmed-defects/:отчёт/PNG/проверки.

Команды /workspace/work/venv/bin/python:
repair.py --baseline work/large-panels/su30sm.dnm --output work/confirmed-defects/final.dnm
check.py --baseline BASE --candidate FINAL --output JSON
check_self.py FINAL JSON
changes/su30sm-large-panels/check_motion.py BASE FINAL OUTDIR
freeze.py BASE FINAL work/confirmed-defects/reproduced.audit.json dist/su30sm-confirmed-defects
package.py work/confirmed-packages work/large-downloaded

Проверки: обе оболочки замкнуты/Эйлер2/согласованы/0дублей/0вырожденных/0самопересечений.201поза:808контактныхключейкакбыло,0новых/удалённых. Побайтоваяперегенерацияподтверждена. x64Wine:11парракурсов+живойGцикл, реальныеPNGоткрываютсядлясравнения. Промежуточныеполныереставрации и нормальнаяэкструзияотклонены, невыпускать. Нижнийзуб/полосы исчезли; тонкая фасеточная линия исходного корпуса местами видна, не объявлять весьсамолёт бездефектным. Опорастойки соединена — еёподъём не обоснован.

GitHubлокальныйGH_TOKENистёк: использовать подключённыеGitHubtools длязаписи; publicAPI/downloadчерезurllib/curl доступны. Созданаудалённаяветка;база8bac3003d73a20cf96ba829aaa805c6552071a59,tree f7b5765bf2f28c0ef92b3faf11d16dc598cb00b1. GitDataupdate_ref НЕ запускалActions; послеисходников создатьworkflow черезContentscreate_file.

Осталось: NativeWindows32/64 CI, открытькадры; окончательныепаспортасборок/ZIP;публикацияновогоrelease su30sm-confirmed-defects-20261114, скачать/проверитьархивы, датьдвепрямыессылки. Wine32неподдержанэтойсредой(syswow64 ntdll.dll c0000135);этоограничениесреды,неархитектурыигры.
