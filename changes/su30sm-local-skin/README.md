# Локальное исправление обшивки Су-30СМ

База: work@3d463be98234aed309c08e7f5767badf95eea61c. Изменяются только MainBayFixedSkin_Left/Right и MainWheelBayShutter_Left/Right, по отдельному разрешению пользователя. Все 162 узла DNM и 158 прочих PCK сохраняются дословно.

## Воспроизведение

Python 3.12, зависимости из requirements.txt. Базовый DNM взять из dist/su30sm-rear-seams/Su30SM_RearSeams_Windows_64bit.zip: runtime/aircraft/su30sm.dnm (SHA256 bfabbd8ff2728ca417cbb9bb948fff27c750de297a156c718aafb51705d4ce83). В Sources ZIP он также находится в baseline/.

```sh
python -m pip install -r changes/su30sm-local-skin/requirements.txt
python changes/su30sm-local-skin/repair.py --baseline baseline/su30sm.dnm --output generated/su30sm.dnm
python changes/su30sm-local-skin/verify.py --baseline baseline/su30sm.dnm --candidate generated/su30sm.dnm --output generated/quality.json
python changes/su30sm-local-skin/validation/triangles.py
python changes/su30sm-local-skin/validation/self_intersections.py generated/su30sm.dnm generated/self-intersections.json
```

Ожидаемый SHA256 результата: 6f8e20b21990820dcc3aa49f91e92ef4a1771047951671f61732d111256b30c6. repair.py отказывается работать с другой базой.

## Алгоритм

fit_field.py строит общее непрерывное искривлённое поле высот на сторону: кубический тензорный B-сплайн, опорные точки исходной нижней обшивки и створок до ошибочной подгонки. QP/OSQP ограничивает поверхность относительно неизменных соседей. Регуляризация кривизны устраняет скачки между независимыми треугольниками. Внешние края привязаны к исходной геометрии; 2-мм параметрический зазор сохраняется. Это локальная реконструкция, а не заводская CAD-поверхность.

repair.py сохраняет проекции цветовых областей и строит согласованный PSLG с Triangle на целочисленной микрометровой решётке. Получается общий индексированный граф поверхности. Задняя поверхность имеет смещение по Y 8 мм для неподвижной обшивки и 1 мм для створок; закрываются только настоящие края. Индексный разрыв одного защемлённого граничного веера разделён без перемещения вершин. Координаты округляются до вычисления нормалей.

source-data/original-hull.srf и provenance.json извлечены extract_reference.py из сохранённого source-stage.dnm теста4. source-data/curved-shutters.dnm — точная историческая reference-source.dnm стадии rear-seams. Используются только опорные поверхности, чужие механизмы и трансформации не переносятся. model-source содержит существующие парсеры проекта.

verify.py проверяет сохранность PCK/узлов, палитру, вырожденность, нормали, связность и замкнутость фактической индексированной сетки. Дополнительное глобальное сваривание 10 нм — отрицательный контроль: оно повторно сливает намеренно разделённый веер и может нарушить топологию; к поставляемой модели оно не применяется. validation/triangles.py использует знаковые расстояния до рёбер и проверку плоскости, с аналитическими контрольными примерами.

Полный отчёт и настоящие игровые кадры: reports/su30sm-local-skin/REPORT.md. Игра запускается штатным BAT из соответствующего Windows ZIP; движок не пересобирался. Полные предшествующие исходники и лицензии сохранены в Sources ZIP, в legacy/.

Проверка движения: `python changes/su30sm-local-skin/validation/motion_compare.py baseline/su30sm.dnm generated/su30sm.dnm generated/motion`. FCL использует решётку 1 мкм; проверка самопересечений отдельно использует реальные записанные координаты. Сохранённый игровой harness и параметры: validation/game-capture/.
