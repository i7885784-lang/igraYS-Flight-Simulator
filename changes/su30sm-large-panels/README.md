# Крупные грани четырёх подтверждённых поверхностей

После дополнительного разрешения пользователя исправляются MainBayFixedSkin_Left/Right и MainWheelBayShutter_Left/Right. Первая фотография показывает левую створку; наземная — правые панели. Все остальные158PCK и162 записи узлов неизменны. Геометрическая база6f8e20b2, сравнение/откат8f0b40ea.

facet.py строит согласованные крупные плоскости по сечениям, сохраняет исходные кромки и цветовые области. Берёт все окрашенные передние треугольники: прежний фильтр площади пропускал тонкие грани и оставлял микроскопические пробелы расчётной проекции. Они ошибочно считались внутренними краями и вызывали рябь. Теперь учитывается настоящий внешний контур; заполняются только численные пробелы площадью менее1e-7м², не функциональные отверстия.

Створки подгоняются целыми плоскостями к неизменному Fuselage_0_4. Линейные ограничения задаются на пересечениях проекций реальных треугольников панели и тела, включая почти вертикальные грани. OSQP перемещает станции, а не отдельные случайные вершины. Исходные кромки закреплены. Толщина поY прежняя:8мм неподвижная обшивка,1мм створки. Нормали получены из реальных граней; искусственного сглаживания/накладок нет.

Python3.12, зависимости changes/su30sm-local-skin/requirements.txt:

```sh
python changes/su30sm-large-panels/facet.py --baseline baseline/su30sm.dnm --output generated/su30sm.dnm
python changes/su30sm-large-panels/check.py --baseline previous/su30sm.dnm --candidate generated/su30sm.dnm --output generated/quality.json
python changes/su30sm-large-panels/check_self.py generated/su30sm.dnm generated/self.json
python changes/su30sm-large-panels/check_motion.py previous/su30sm.dnm generated/su30sm.dnm generated/contacts
python changes/su30sm-large-panels/package.py work/packages work/previous-zips
```

Ожидаемый SHA256 модели91a201f3ca02d7c69345d197827b1567cedcc87edb51409ffc0006b8cc0ae61c. ModelSources содержит baseline6f8, previous8f и generated91a, код и данные проверок. Игровая упаковка требует двух предыдущих OrderedFacets ZIP в последнем аргументе, доступных в GitHub Release su30sm-ordered-facets-20261113. Патчи4PCK и их SHA — dist/su30sm-large-panels/metadata.json. Полный неизменный движок/лицензии сохранены в прежнем публичном FullSources.

Скрипты capture-used.sh и capture-lit-used.sh сохраняют фактические камеры/пути среды. validation/capture*.py — использованный Wine harness; требует существующего resize_capture.exe и среды Wine/Xvfb, не является нативным тестом Windows. В освещённом наземном сравнении меняется только курс временного fixture:270° вместо0°, одинаково до/после. Краска, LIGHTSRCD и файлы конфигурации поставки не изменяются.
