# Су-27 / МиГ-29: FlightGear geometry test 1

Отдельная версия от опубликованного Су-47 №1, который продолжает основу Су-57 №2.
Заменены только Су-27/МиГ-29 и их визуальные привязки. Су-47 и Су-57 сохранены.
[Короткий отчёт](../../reports/fighters-fg-test-1/REPORT.md).

`model-source/NOTICE.txt` перечисляет авторов, версии, лицензии и изменения.
Используются `Su-27.ac` и **`mesh_airframe.ac`** из закреплённых репозиториев:
именно второй файл загружается штатным `Models/Mig-29.xml` выбранной версии.
Старый `Mig-29.ac` не накладывается поверх него. Для сопел МиГ использован
`mesh_nozzleseg.ac`; свои материалы и факелы. Пилот с неопределённой CC-лицензией,
чужие текстуры, звуки, эффекты и системы FlightGear не перенесены. XML сокращены
до осей и таблиц поворота; Nasal и подключение подмоделей удалены.

## Пересборка геометрии

Python 3, `pip install -r model-source/requirements.txt`,
`python model-source/build_model.py`.
Результат — десять файлов в `model-source/runtime/aircraft/`.
Скопировать их в **новую** полную копию Су-47 №1, затем в `aircraft/aircraft.lst`
заменить ссылку `aircraft/su27coarse.dnm` на `aircraft/su27_coarse.dnm`.
Остальные записи, в том числе Су-47/Су-57, сохранить.
Исходники с лицензиями положить в `aircraft/fighters-fg-source/`.

## Движок

`native.patch` — разница от исходников **Су-47 test 1**, а не от чистого upstream.
Оригинальные/новые SHA-256 двух изменённых файлов — `engine-hashes.json`.
Не накладывать патч повторно. Полный новый архив исходников уже содержит его.
Классы: 210 — 21 положение шасси/створок, 211 — фонарь, 212 — тормоза,
214 — связанная опора тормоза Су-27, 220–229 — поверхности.
Форсаж использует прежние 110/111 и штатные условия двигателя. Отклонения сопел нет.
Су-47/Су-57 продолжают использовать собственные классы и прежнюю логику.

Сборка проверена CMake Release + Ninja + MinGW-w64 i686 POSIX GCC 14.
Цель `ysflight32_gl1`, отдельная проверочная — `ysflight64_gl1`.
Сохранённый [скрипт среды](../../reports/environment-2026-10-26/tools/build.sh)
задаёт флаги и переименование DLL. Существенные значения:

```
CMAKE_CXX_FLAGS=-DWIN32 -D_WINDOWS -DNOMINMAX -fpermissive -fno-delete-null-pointer-checks
CMAKE_C_FLAGS=-Wno-error=incompatible-pointer-types
CMAKE_EXE_LINKER_FLAGS=-static -static-libgcc -static-libstdc++ -mwindows
CMAKE_SHARED_LINKER_FLAGS=-static -static-libgcc -static-libstdc++
CMAKE_CXX_STANDARD_LIBRARIES=-lkernel32 -luser32 -lgdi32 -lwinspool -lshell32 -lole32 -loleaut32 -luuid -lcomdlg32 -ladvapi32 -limm32
```

Только проверочная Win64 сборка дополнительно определяет `V861_VALIDATION`.
Ресурсы из игрового ZIP поместить в `YSFLIGHT/runtime`, **исключив EXE**:
иначе шаг копирования CMake может затереть свежий исполняемый файл.
Пути компиляторов в toolchain настроить под свою систему. Библиотеки — сохранённые
`public/src`, не произвольный новый upstream. `libsndYsflight32.dll` и
`libvoiceYsflight32.dll` переименовать без `lib` в `plugin/`.

## Проверки и съёмка

Сценарии лаборатории `check_game.py` требуют Xvfb :99, Wine64, libX11/libXtst,
Pillow, FFmpeg и окружение из `/workspace/ysflight-dev/env.sh`.
Рядом нужны полный `runtime/`, производственный Win32 EXE и отдельный Win64 EXE.

```
AIRCRAFT_CHECK=SU-27_FLANKER CHECK_NAME=su27-inspect-delivery python3 check_game.py inspect
AIRCRAFT_CHECK=MIG-29_FULCRUM CHECK_NAME=mig29-gear-delivery python3 check_game.py gear
```

Остальные сценарии: `canopy`, `controls`, `brake`, `engine`, `smoke`.
Механизмы управляются настоящими XTest клавишами. `inspect` делает паузу и
направляет игровую камеру; её снимки не выдаются за живую аэродинамическую проверку.
`validate.py` проверяет структуру, регистрацию, освещение и сохранённые самолёты;
`reproduce.py` собирает геометрию в отдельной папке;
`check_evidence.py` проверяет журналы клавиш/переходов и декодирует видео.
`package.py` — лабораторная упаковка с явными путями текущей среды.
Прямой запуск на настоящей Windows 10 x86 здесь не подтверждён.
