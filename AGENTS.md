# Актуальное указание пользователя: откат на тест5

CURRENT_VERSION.json/md закрепляют Су30СМ тест5 после явного отклонения6/7. Следующую работу начинать от полногоGame5. Старые записи о продолжении от6/7 ниже исторические и отменены.

# Project context for coding assistants

Read [CURRENT_VERSION.md](CURRENT_VERSION.md) and
[PROJECT_HANDOFF.md](PROJECT_HANDOFF.md) before changing the game.
The user explicitly selected **Su-57 test 2** as the current development
baseline. Start future work from the complete archive linked there, with
its existing Su-27, MiG-29 and Su-57. Consult CURRENT_VERSION.json for exact
paths and archive hash. Do not silently start from older releases.

Preserve previous archives, reports and source history. Make new gameplay
and aircraft changes in a separate test version. Provide real in-game
pictures/videos and a downloadable Windows 32-bit ZIP. Distinguish ideas,
automated checks and user acceptance. Keep upstream model attribution and
licenses. User instructions take precedence over this file.

The handoff distinguishes historical experiments from the still evolving
sandbox goal. Do not treat old mechanics as a fixed final design. The engine
source snapshot linked there is separate from the playable baseline ZIP.

The current aircraft task is docs/aircraft-model-upgrade/TASK_PROMPT.md.
Read it first; README.md and TASK_DETAILS.md in that directory are reference. Preserve the already published Su-47 work. Read
docs/THIRD_PARTY_LICENSE_PLAN.md: defer license UI placement; preserve
required notices and source materials now. Do not add a main-menu screen.

## Су-30СМ №2 завершён

Последний отдельный тест Су30: reports/su30sm-test-2/STATUS.json, код changes/aircraft-su30sm-test2, подробное продолжение в WORK_STATUS.md. Release432779163 оставить DRAFT. Один архив32/64, прозрачный фонарь/камера/общий обзор ЛКМ и двойнойПробел; исходники и остальные самолёты сохранены. Полные данные в начале PROJECT_HANDOFF.md. Не откатывать эти изменения ктесту1, если задача продолжает Су30.

## Су-30СМ №3 завершён

Продолжать Су30 от отдельного теста3: reports/su30sm-test-3/STATUS.json, changes/aircraft-su30sm-test3/WORK_STATUS.md. Пользователь разрешил найденную инструкцию Звезда7314, нос не менять. Исправлена выступавшая в фонарь носовая ниша, шасси/щитки, тормоз/привод, сопла/пламя; сглаживание выключено, оружие отключено по запросу. Release433034614 оставить DRAFT. Все ZIP скачаны и SHA/CRC проверены, реальный PE32 Windows проверен. Старые версии сохранять.

## Су-30СМ №4 завершён

Продолжать Су30 от отдельного теста4: reports/su30sm-test-4/STATUS.json и changes/aircraft-su30sm-test4/WORK_STATUS.md. Пользователь прислал схемы и теперь РАЗРЕШИЛ менять нос. Ниши/створки перестроены, база5,57м, колея4,10м, размах14,70м, носовой приёмник и серо-голубая окраска доработаны, сглаживание выключено. EXE3 неизменённые; полный соответствующий движок в SourcesZIP/su30sm-test3/engine. Draft433529453 оставить DRAFT. ЧистыйGLBpipeline и все5SHA совпали после канонизации внутренней панели, Windows32 фактически проверен, ZIPскачаны/SHA/CRCпрошли. Старыеархивы сохранять.

## Су-30СМ №5 завершён

Продолжать отдельный Су30 от reports/su30sm-test-5/STATUS.json, код changes/aircraft-su30sm-test5. Наклонные оси рулей, жёсткие щитки WheelCarrier, отдельные MainWheelBayShutter, семь замкнутых створок. Контуры килей сохранены по схеме/инструкции7314. Не возвращать независимый сдвиг щитков0,75м/телескопы4. Draft433727284 оставить DRAFT. Actions41823849278 успешен, модель строго воспроизведена, Windows32 фактически проверен,3ZIP скачаны/SHA/CRCпрошли. Детали в PROJECT_HANDOFF и WORK_STATUS5; CURRENT_VERSION неизменён.

## Су-30СМ №6 завершён

Продолжать отдельный Су30 от reports/su30sm-test-6/STATUS.json и changes/aircraft-su30sm-test6. Пользовательские3фото: тоньше кили(44%выше корня), фонарь43°, тормоз65°вокругоси/новаяопора, общие нижние сечения/стенкиниш/парные задние передние створки. Окраска/сглаживание0/остальные самолёты сохранены. Draft433962216 оставитьDRAFT. Actions41838636093 успешен,WindowsPE32фактически43,3с;3ZIPскачаны/SHA/CRCпрошли. ПодробнееPROJECT_HANDOFF. CURRENT_VERSION неизменён.

## Су-30СМ №7 завершён

Последний отдельныйСу30 — reports/su30sm-test-7/STATUS.json, код changes/aircraft-su30sm-test7. Исправленвырезверха крыла внишах, фонарь/каналывоздухозаборников/раздельныестворки/подвижнаячастьтормоза. Draft434030950 оставитьDRAFT. Actions41847602521 SUCCESS,WindowsPE32фактически49,2с,3ZIPскачаны/SHA/CRCпрошли. CURRENT_VERSIONсохранён. ПодробнееPROJECT_HANDOFF; пользовательскаяприёмкаожидается.
