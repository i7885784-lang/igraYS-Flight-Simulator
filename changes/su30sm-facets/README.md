# Фасеточная левая обшивка Су-30СМ

База: tag su30sm-local-skin-20261111, DNM SHA256 6f8e20b21990820dcc3aa49f91e92ef4a1771047951671f61732d111256b30c6. Меняется только MainBayFixedSkin_Left.srf. Створки, правая обшивка и все механизмы не меняются. Сглаживание уже было выключено: нужно укрупнить геометрические фасетки.

Python3.12; используйте requirements.txt предыдущего changes/su30sm-local-skin. facet.py берёт внешнюю поверхность точной базы, сохраняет все её граничные точки, адаптивно выбирает опорные точки внутри и строит кусочно-плоскую аппроксимацию. Подразделение фасеток по цветовым областям сохраняет проекции камуфляжа. Нормали вычислены из реальных окончательных граней прежним make_panel(), без специальных сглаживающих нормалей. Замкнутая задняя оболочка имеет исходное смещение 8мм. Предел подбора на исходных вершинах 8мм, предохранительный предел на новых 12мм; фактически измерено до6,294мм. Полный максимум между сетками математически не доказывается.

```sh
python changes/su30sm-facets/facet.py --baseline baseline/su30sm.dnm --output generated/su30sm.dnm
python changes/su30sm-facets/check.py --baseline baseline/su30sm.dnm --candidate generated/su30sm.dnm --output generated/quality.json
python changes/su30sm-facets/check_self.py generated/su30sm.dnm generated/self.json
python changes/su30sm-facets/check_motion.py baseline/su30sm.dnm generated/su30sm.dnm generated/contacts
python changes/su30sm-facets/package.py work/packages
```

В ModelSources.zip уже вложены baseline/, generated/ и зависимости локального этапа. package.py в репозитории берёт два подлинных исходных ZIP из dist/su30sm-local-skin/ и замороженный проверенный PCK из dist/su30sm-facets/ModelUpdate.zip; выполняет CRC/SHA/PE и проверяет сохранность остальных записей. Ожидаемый SHA256 модели 04f7d3c0b823b53990a010fcc29009d032e648b9c781fd02f44c8a86b3dfb129. Движок не пересобирается. ModelSources.zip покрывает новый этап модели; полные неизменные исходники движка с лицензиями доступны в FullSources.zip предыдущего публичного Release.

check.py/check_self.py повторно используют прежние проверенные валидаторы с allowlist только одного изменённого меша. check_motion.py проверяет только изменённую неподвижную обшивку против соседей на201 позе. Отрицательный контроль глобальной сварки10нм может разрушить намеренно разделённый граничный веер; он не применяется к модели. Игровые кадры получены x64 OpenGL под Wine; сохранённый capture-used.sh содержит фактические камеры и пути среды, требует существующий harness work/lab/capture.py. Полный новый аудит всего проекта не выполнялся.
