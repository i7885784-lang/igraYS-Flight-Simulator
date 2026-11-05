# Су-30СМ №5: ниши и створки — поставка проверена

Продолжена сохранённая работа после потери среды. Отдельный кандидат, CURRENT_VERSION №5+IntakeFix сохранён. Финальный DNM `08e5e8fc66098f87cd926526cf508e92d39848888c487d425a7213829465e5b4`.

Actions [42017042257](https://github.com/i7885784-lang/igraYS-Flight-Simulator/actions/runs/42017042257) SUCCESS, источник поставки a085246. [Отчёт](../../reports/su30sm-gear-bays-repair/REPORT_RU.md), [приёмка](../../reports/su30sm-gear-bays-repair/acceptance.json), [повторное скачивание](../../reports/su30sm-gear-bays-repair/download-verification.json). Release435097963 остаётся DRAFT; ссылки доступны владельцу после входа в GitHub.

- [YSFlight_Su30SM_Test5_GearBays_Game_Win32_Win64.zip](https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/untagged-e872e8ea05a63da095a3/YSFlight_Su30SM_Test5_GearBays_Game_Win32_Win64.zip) — SHA256 `ed56d7ac5fd56c2f62454591fdb6371835355b718f31a7b77cc1079dcec0e932`
- [YSFlight_Su30SM_Test5_GearBays_Sources.zip](https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/untagged-e872e8ea05a63da095a3/YSFlight_Su30SM_Test5_GearBays_Sources.zip) — SHA256 `dc2e611a1ee4096a0188e0cfdea6ad8633e3b3ccaaeb477b7bfe77af7c2525de`
- [YSFlight_Su30SM_Test5_GearBays_Report.zip](https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/untagged-e872e8ea05a63da095a3/YSFlight_Su30SM_Test5_GearBays_Report.zip) — SHA256 `727a9f4abdfc06a4d0bdd547a470cdf494151253f4b24587a08662a88c726d7f`

Проверено: 20 пар игровых кадров, родной G-цикл0→1→0 на неизменённом Windows OpenGL64 под Wine,201 расчётное положение;0 контактов в заявленной матрице,0 вырожденных треугольников изменённых/новых ресурсов,0 самопересечений8 панелей и3 облицовок. У обеих крышек0 точек и0 площади вне действительного исходного контура. Скачанные Game/Sources/Report прошли SHA/CRC,1156 прочих файлов игры и8068 прежних файлов Sources точные; сборка из скачанных ресурсов дала точный08e5e8fc SHA. Windows32 не запускался заново.

16 прежних SRF изменены,18 добавлены. Исходные траектории колёс/стоек/внешних дверей точные; лишь две внутренние крышки получили согласованные фазы. Двигатели и другие самолёты прежние. Геометрия заморожена; не запускать новую триангуляцию вместо проверенного build.py без повторной проверки.

Остаётся унаследованное пересечение основных колёс/механизма с каналами IntakeDuct в части убранного движения. Старые фасеточные швы и контрастные тени не все устранены. Это отдельная игровая реконструкция, не точная заводская CAD-модель. Не объявлять весь самолёт свободным от пересечений. Для следующей работы сперва получить пользовательскую визуальную оценку; не возвращаться к отклонённым6/7.

Стабильная5+IntakeFix17ddccbe…, предыдущая ShutterFix86455c58…, восстановленная частичная965b609b… сохранены; пути/полныеSHA в rollback-preserved.json. Исходная копия не перезаписывалась.
