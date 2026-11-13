# Упорядоченные плоскости левой обшивки

Исправляется визуально неудачная фасетизация04f7d3c0. Геометрическая база — аккуратная6f8e20b21990820dcc3aa49f91e92ef4a1771047951671f61732d111256b30c6 из su30sm-local-skin-20261111. Меняется только MainBayFixedSkin_Left.srf. Створки, правая обшивка и все узлы/анимации сохраняются дословно.

facet.py задаёт общие поперечные станции и продольные полосы. Каждый четырёхугольник разделён одной согласованной диагональю; соседние цветовые треугольники лежат в общей геометрической плоскости. Уточнение добавляет целую станцию, а не отдельные точки Delaunay. Исходная полоса40мм у края фиксирована; переход к плоскостям занимает следующие35мм. Высоты в узкой геометрии вычисляются относительно локального начала треугольника, чтобы избежать потери точности. Исходные граничные вершины закреплены явно. Створка используется только как неизменная опора высот за2-мм зазором; её PCK не записывается.

Нормали получены из реальной геометрии прежней make_panel(); ложные нормали, случайные накладки и перекраска не применяются. Сопряжения и смещение задней оболочки8мм сохранены. Частые треугольники по кромкам/цветовым границам остаются: их число не является критерием визуального качества. Цель — общие ровные плоскости в основной части.

Python3.12, зависимости changes/su30sm-local-skin/requirements.txt:

```sh
python changes/su30sm-ordered-facets/facet.py --baseline baseline/su30sm.dnm --output generated/su30sm.dnm
python changes/su30sm-ordered-facets/check.py --baseline baseline/su30sm.dnm --candidate generated/su30sm.dnm --output generated/quality.json
python changes/su30sm-ordered-facets/check_self.py generated/su30sm.dnm generated/self.json
python changes/su30sm-ordered-facets/check_motion.py baseline/su30sm.dnm generated/su30sm.dnm generated/contacts
python changes/su30sm-ordered-facets/package.py work/packages
```

Ожидаемый SHA модели:8f0b40ea8897103c9756c1b08471d1525275adc9267030b239c0d95351257422. ModelSources содержит обе модели и код локального этапа. Для полной игровой упаковки нужны два прежних ZIP из dist/su30sm-local-skin/. Источники неизменного движка с лицензиями сохранены в предыдущем публичном FullSources.

Проверка и собственная визуальная оценка трёх вариантов — reports/su30sm-ordered-facets/REPORT.md. Проверена игра x64 OpenGL под Wine; x86/нативная Windows заново не запускались. capture-used.sh сохраняет фактические параметры прежнего игрового harness и локальные пути Wine.
