# Су-30СМ: фасетки выделенной обшивки

Задача: согласовать низкополигональную гранёность выделения, без несвязанных изменений. Повторённый запрет на створки соблюдён: меняется только MainBayFixedSkin_Left, часть выделения MainWheelBayShutter_Left остаётся гладкой. Правая сторона/окраска/механизмы защищены.

База: tag su30sm-local-skin-20261111, commit0b1efe6896d3b02580cbeb0d014f4a267bf1ffe9; DNM6f8e20b21990820dcc3aa49f91e92ef4a1771047951671f61732d111256b30c6. Новая ветка fix/su30sm-facets-20261113. База и прошлые ZIP сохранены.

Нужные пути (GitHub repo i7885784-lang/igraYS-Flight-Simulator):
- changes/su30sm-facets/facet.py: run() — единственная локальная адаптивная фасеточная реконструкция; check.py/check_self.py/check_motion.py — ограниченные проверки; package.py — две архитектуры и источники модели.
- changes/su30sm-local-skin/repair.py: make_panel() — прежнее замыкание оболочки и геометрические нормали; fit_field.exterior/Projected — чтение поверхности; model-source/dnm.py — PCK/узлы. Старый глобальный генератор повторно не запускать.
- dist/su30sm-facets/ModelUpdate.zip — замороженный единственный PCK; dist/su30sm-local-skin/ — исходные полноценные x86/x64 ZIP.
- reports/su30sm-facets/ — игровые пары и численные доказательства.
- work/proposed/su30sm.dnm — база; work/facets/su30sm.dnm — результат; work/candidate/runtime — исходная игра, work/facets-probe/runtime — игра с новой моделью (диагностические цвета уже заменены настоящими).

Узлы: MainBayFixedSkin_Left CLA99/1STA разрешён. MainWheelBayShutter_Left/Right CLA210/101STA и MainBayFixedSkin_Right защищены. Подтверждение области в игре: временная цветовая диагностика facets-identification-closed; базовая модель не изменена.

Причина: плотная сетка на плавном поле; вершинных R-нормалей/специального сглаживания нет. Слишком слабая проба с ошибкой2мм отклонена визуально. Итоговая внешняя сетка22244→3286 треугольников; измерено максимум6,294мм, исходные кромки сохранены. Результат SHA04f7d3c0b823b53990a010fcc29009d032e648b9c781fd02f44c8a86b3dfb129.

Команды: Python /workspace/work/venv/bin/python; facet.py --baseline ... --output ...; check.py --baseline ... --candidate ... --output ...; check_self.py MODEL OUT; check_motion.py BASE MODEL OUTDIR; package.py OUTDIR. Зависимости прежнего requirements.txt.
Игра: source /workspace/ysflight-dev/env.sh; Xvfb1024x768; work/facets/capture-final.sh и changes/su30sm-facets/capture-used.sh. Шесть одинаковых камер/поз до/после. x64 Wine реально запускался; x86/нативная Windows заново не запускались, не заявлять обратного.

Готово: 161 прочий PCK и162 узла дословно сохранены; сетка замкнута/нормали верны/нулевые и дубликаты отсутствуют/самопересечений нет;201 поза,404 прежних контакта,0 добавленных. Открыты PNG шести окончательных ракурсов. Завершено: отчёт, упаковка, публичный Release и контроль скачанных ZIP. Не повторять весь аудит.

Публикация: https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/tag/su30sm-facets-20261113 ; Actions43446236303 SUCCESS. ТриZIP скачаны/SHA/CRC проверены, оба PE и1160 защищённых записей повторно точные; из скачанных исходников заново получен побайтовый04f7d3c0… . Протокол reports/su30sm-facets/publication-check.json. Старый локальный GH_TOKEN истёк: не повторять gh auth/push; использовать подключённые GitHub инструменты. GitData API сохранил файлы, но Actions запустился после Contents API update_file существующего workflow (с предварительным fetch SHA). Сам workflow больше не менять без необходимости.
