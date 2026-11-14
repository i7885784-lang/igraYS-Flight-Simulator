# Локальное сопряжение передней обшивки основной ниши

База91a201f3, результат9d97ef82. Ровно три PCK: две неподвижные MainBayFixedSkin и удаление150остаточных полигонов Fuselage_0_4 в проёмах наружных основных створок. Все движущиеся меши и анимационные записи сохранены.

`repair.py build_panel()` соединяет измеренные неизменные крайние сечения в передней полосе длиной25см плоскими гранями. Предыдущая узкая подгонка к границе создавала складку; локальная коррекция достигает349мм внутри полосы, а не смещения всего фюзеляжа. Исправлены численный2мкмвыступ передней границы и внутренний торец. `bay_cut.py` использует реальные потолочные треугольники неизменённой GearWell и прежние контуры наружных створок. Исключённые остатки F4 не относятся к наружной раме воздухозаборника. В итоговом F4нет новых граней/вершин — только удаление подтверждённых лишних полигонов.

Нужны существующие зависимости `changes/su30sm-local-skin/requirements.txt`. Из корня:

```sh
python changes/su30sm-confirmed-defects/repair.py --baseline baseline/su30sm.dnm --output generated/su30sm.dnm
python changes/su30sm-confirmed-defects/check.py --baseline baseline/su30sm.dnm --candidate generated/su30sm.dnm --output quality.json
python changes/su30sm-confirmed-defects/check_self.py generated/su30sm.dnm self.json
python changes/su30sm-large-panels/check_motion.py baseline/su30sm.dnm generated/su30sm.dnm motion
```

В SourcesZIP baseline — точная91a, generated — итог9d97. `freeze.py` создаёт три точных ZIPпатча, `package.py` применяет их к отдельным предыдущим LargePanels x86/x64архивам, проверяет PE, SHA/CRC и побайтово все прочие файлы. F4хранится малой дельтой удаляемых face-блоков; она восстанавливает полный меш с проверкой SHA.

Схема проверки: x64Wine — одинаковые ракурсы до/после, три положения, живые клавишиG. Настоящая Windows2022 — `windows_prepare.py 32|64`, `windows_check.py 32|64`;32 использует штатные кнопки,64 дополнительно диагностические камеры. Скриншоты надо открыть, автоматическое прохождение само по себе не заменяет визуальную оценку.

Откат в игровыхZIP: заменить runtime/aircraft/su30sm.dnm файлом runtime/rollback-local-defects/su30sm.dnm. Старые версии не изменены. Тонкая фасеточная линия исходного корпуса местами остаётся; стойку не перемещать без доказанного разрыва крепления.
