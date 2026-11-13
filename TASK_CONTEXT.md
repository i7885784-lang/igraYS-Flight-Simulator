# Су-30СМ: исправление неудачной фасетизации

Текущая цель: исправить «помятую» обшивку после собственной отрицательной оценки предыдущей поставки. Менять только MainBayFixedSkin_Left. Все створки, шасси, ниши, правая обшивка, окраска и анимации защищены; MainWheelBayShutter_Left внутри выделения остаётся гладкой.

Геометрическая база — аккуратная6f8e20b21990820dcc3aa49f91e92ef4a1771047951671f61732d111256b30c6, tag su30sm-local-skin-20261111. Не брать отклонённую04f7d3c0 из su30sm-facets-20261113 как геометрическую основу. Отдельная ветка fix/su30sm-ordered-facets-20261113; все прежние поставки сохранены.

Нужные пути в i7885784-lang/igraYS-Flight-Simulator:
- changes/su30sm-ordered-facets/facet.py: run(), StableProjected, локальный Strips — регулярные станции/полосы, фиксированный40-мм край, переход35мм. Единственная запись PCK: MainBayFixedSkin_Left.srf. Створка только читается как опора за2-мм зазором.
- check.py/check_self.py/check_motion.py — прежние узкие валидаторы; package.py — отдельные настоящие архитектуры, источники модели, CRC/SHA/PE/неизменность1160 прочих записей.
- changes/su30sm-local-skin/repair.py make_panel(), fit_field.exterior, model-source/dnm.py — существующие зависимости, не изменены. Не повторять прежний глобальный QP.
- dist/su30sm-ordered-facets/ModelUpdate.zip — проверенный единичный PCK. Игровая упаковочная база dist/su30sm-local-skin/.
- reports/su30sm-ordered-facets/ — шесть ракурсов в трёх версиях before/rejected/after; generator/quality/self/contacts/shape-distance JSON и REPORT.md.
- work/proposed/su30sm.dnm —6f8база; work/ordered-facets/su30sm.dnm — новый8f0b40ea8897103c9756c1b08471d1525275adc9267030b239c0d95351257422; work/facets-probe/runtime — уже новая настоящая модель, диагностические цвета отсутствуют.

Принятый результат:17 поперечных/15 продольных станций. Отклонённые:04f7d3c0 (вмятины),52b73982 (частые узкие полосы). Открыты все6 окончательных игровых PNG и сопоставлены с обеими предыдущими версиями: новый лучше04f7, ровные продольные грани вместо случайных вмятин. Контур закреплён; максимум проверенного смещенияY18,275мм; расстояния новых вершин до исходных треугольников max14,997мм/RMS1,201мм. Это локальная аппроксимация формы, не утверждать неизменность всех вершин разрешённой обшивки.

161 прочий PCK/162 узла дословно сохранены. Замкнутость/нормали/вырожденность/дубликаты/самопересечения проверены.201 поза ×156 соседей:404 прежних контактных ключа,0 добавленных/удалённых. Очищенный код заново создал побайтовый8f0b. Нового живого циклаG нет; статические позы сравнения. Реальная игра — x64 OpenGL под Wine; x86/нативная Windows не запускались, не заявлять иное.

Команды: /workspace/work/venv/bin/python changes/su30sm-ordered-facets/facet.py --baseline BASE --output MODEL; check.py --baseline BASE --candidate MODEL --output JSON; check_self.py MODEL OUT; check_motion.py BASE MODEL OUTDIR; package.py OUTDIR. Зависимости прежнего requirements.txt. Источники модели содержат baseline/generated и оба локальных этапа; полный неизменный движок в прежнем публичном FullSources.
Game: source /workspace/ysflight-dev/env.sh; Xvfb1024x768; capture-used.sh сохраняет фактические камеры и пути. Новые PNG work/lab/checks/ordered-after/ с SHA8f0b.

Доставка: локальный GH_TOKEN истёк, не повторять gh push/auth. Подключённые GitHub инструменты действуют. Для двоичных файлов create_blob(base64), create_tree(base_tree), create_commit, update_ref с lease; это сохраняет файлы, но не запускало Actions. Contents API create_file/update_file существующего workflow запускает Actions. Прежняя удалённая основа0b101a0afe8a94f1b951b56fadd22d7ab1572078. Новый workflow создавать Contents API после публикации исходников, затем скачивать публичные ZIP для проверки. Не запрашивать то же разрешение на створки повторно.

Готово: исправление, самостоятельное визуальное решение, численные проверки, исходники/отчёт и локальная упаковка. Осталось: GitHub-публикация нового Release su30sm-ordered-facets-20261113 и контроль скачанных файлов; обновить этот пункт по завершении. Не выполнять полный аудит заново.
