# Су-30СМ: глубокие впускные каналы

Продолжение ECEE, не переделка самолёта. Изменены только два IntakeDuct SRF.
Все узлы, состояния анимаций, окраска внешней обшивки и прочие поверхности сохранены.

`baseline/su30sm.dnm` — точная ECEE из поставки IntakeDepth. Сохранена в FullSources.
`python build.py` — точная сборка по проверенным SRF и SHA.
`python repair.py` — генерация по измеренным 19 сечениям Fuselage_0_4 (Shapely2.1).
`python check.py` — 201 положение; `python validate.py` — топология/нормали/дубликаты.
Отчёт и реальные снимки игры: ../../reports/su30sm-natural-pass.
