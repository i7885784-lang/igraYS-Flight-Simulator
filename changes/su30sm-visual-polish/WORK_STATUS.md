# Су-30СМ: точечная доводка — поставка завершена

6ноября2026. Отдельная копия предыдущей GearBays08e5e8fc; стабильная CURRENT_VERSION5+IntakeFix сохранена. Новый ресурс: `1a10d466acf32d9647ee7fe2963b47419b94d44f34ed32229544eb72ad1bb032`, cockpit `59e8226dede7a10d526e48332043d9d2f4dc27c018b6f3b732b188b567274b31`.

Actions [42162588062](https://github.com/i7885784-lang/igraYS-Flight-Simulator/actions/runs/42162588062) SUCCESS. Источник поставки6a68463813e20e21b13367b44f39b57ca90b60ab. Release436099010/tagpersonal-su30sm-polish-20261106 остаётся DRAFT, прямые ссылки требуют входа владельцаGitHub.

- [YSFlight_Su30SM_Test5_VisualPolish_Game_Win32_Win64.zip](https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/untagged-85ce924581c27cd3b259/YSFlight_Su30SM_Test5_VisualPolish_Game_Win32_Win64.zip) — SHA256 `2fcefe0f6df49e2b4c57db100ce1679e6ae50fa21b1309a3268ff1be1a051e03`
- [YSFlight_Su30SM_Test5_VisualPolish_Sources.zip](https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/untagged-85ce924581c27cd3b259/YSFlight_Su30SM_Test5_VisualPolish_Sources.zip) — SHA256 `3a80c7836c1b753d68b8f8c3891e2eb5bc544ed9853c29b56a588a027c8a7238`
- [YSFlight_Su30SM_Test5_VisualPolish_Report.zip](https://github.com/i7885784-lang/igraYS-Flight-Simulator/releases/download/untagged-85ce924581c27cd3b259/YSFlight_Su30SM_Test5_VisualPolish_Report.zip) — SHA256 `5b5648e6399b5b75d0ebe8452f463236546c85888452a67d690b9b5f53bbf065`

Изменены только2игровыхфайла — su30sm.dnm и su30smcockpit.dnm;1155 прочих файлов побайтно точные. В основнойDNM4SRF(F13/2IntakeDuct/DoorHingeForks),17STAузлов; вкабине2STAфонаря. Полная историяSources/движок/GLB/лицензии сохранены. ZIPповторно скачаны SHA/CRCпройдены, обаDNMточно собраны из скачанныхSources. Полные доказательства: ../../reports/su30sm-visual-polish/download-verification.json и STATUS.json.

Результат:70→30мм сдвига внешних дверей (углы/фазы прежние),короче вилки; фонарь55→43°,тормоз60→50° и согласованный привод;2внутренних конусных пика F13 утоплены за горловины,128вершинныхэкземпляров;4наружных обратных грани каждой стенкиIntakeDuct удалены, физические стенки/вентиляторы сохранены. Общая окраска прежняя. Никаких новых узлов/мешей. Колёса,стойки,внутренниеMainWheelBayShutter,лепестки/эффектысопел,физика иEXEточные прежние.

Проверка:201позашасси0контактов в заявленнойматрице;201позапривода maxошибка0,356мм,перекрытие≥252,9мм;4нативныхWindowsOpenGL64цикла Wine/Xvfb (G,Alt+5,B,газ/форсаж),15сравнений до/после ивидео. Выбранныеигровыекадры реально открыты;полныевидеоцеликом не просмотрены. Windows32 заново не запускался.

Ограничения: углы подобраны пофото,не заводскойзамер. Фасеточныеполосынаисходныхстворках/обшивкеместамиостаются. Старыйmainwheel/IntakeDuctstow-overlap остаётся;его не скрывали удалением механизма. Не заявлятьвесьсамолётсвободнымотпересечений. Геометриязамороженадлявизуальнойприёмки,старыеархивынеперезаписывались,CURRENT_VERSIONнепереключатьавтоматически. Не переноситьотклонённые6/7.
