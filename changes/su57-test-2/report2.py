from pathlib import Path
import shutil,json,hashlib
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
lab=Path(__file__).resolve().parent;repo=Path('/workspace/igraYS-Flight-Simulator');dst=repo/'reports/su57-test-2';dst.mkdir(parents=True,exist_ok=True)
checks=json.loads((lab/'checks.json').read_text());assert checks['passed']
for mode in ['views','cockpit-detail','lighting','ground','gear-detail','exhaust-ab','controls','real-gear','real-canopy']:
 for p in (lab/f'captures/su57/after/{mode}').glob('*.png'):shutil.copy2(p,dst/(mode+'-'+p.name))
for name in ['flaps','brake']:shutil.copy2(lab/f'captures/su57/after/live-controls/{name}.png',dst/f'live-{name}.png')
for p in (lab/'videos').glob('*.mp4'):shutil.copy2(p,dst/p.name)
shutil.copy2(lab/'orbit/orbit-360.mp4',dst/'orbit-360.mp4')
for name in ['comparison-orthos.png','model-orthos.png','orbit-contact.jpg','orbit-upper-all.jpg','checks.json','package-checks.json','model-stats.json','source-rebuild-checks.json']:shutil.copy2(lab/name,dst/name)
for src,name in [(lab/'videos/checks.json','video-checks.json'),(lab/'orbit/results.json','orbit-checks.json'),(lab/'captures/su57/after/real-gear/results.json','gear-checks.json'),(lab/'captures/su57/after/real-canopy/results.json','canopy-checks.json'),(lab/'captures/su57/after/live-controls/results.json','keyboard-checks.json')]:shutil.copy2(src,dst/name)
md='''# Су-57 — переделанная тестовая модель №2

[**Скачать игру — Windows 32-бит**](../../downloads/YSFlight_Su57_Test_2_32bit.zip?raw=true) · [**Скачать фотоотчёт PDF**](../../downloads/Su57_Test_2_Photo_Report.pdf?raw=true) · [**Осмотр 360° — видео**](orbit-360.mp4?raw=true)

Распаковать в новую папку → **ysflight32_gl1.exe** → **«Су-57: тест модели»**. Су-27 и МиГ-29 сохранены.

## Главное сравнение: сверху и спереди

Первый тест слева, новая геометрия справа. Одинаковый масштаб, без перспективы; это проекции фактических игровых моделей. Крыло перенесено назад, изменены носовая часть и фонарь, форма воздухозаборников, взаимное положение двигателей, килей и стабилизаторов.

![До и после — сверху и спереди](comparison-orthos.png)

## Новая модель в игре

Дальше — настоящие кадры YSFlight.

![Общий вид](views-front-quarter.png)

| Спереди | Сверху |
|---|---|
| ![](views-front.png) | ![](views-top.png) |

| Сбоку | Сзади |
|---|---|
| ![](views-right.png) | ![](views-rear.png) |

| Слева | Снизу |
|---|---|
| ![](views-left.png) | ![](views-bottom.png) |

![Задний ракурс](views-rear-quarter.png)

## Круговой осмотр

[**Скачать видео осмотра 360°**](orbit-360.mp4?raw=true). Оно собрано из 36 кадров штатной камеры игры с шагом 10°. Самолёт поставлен на паузу для проверки формы; это не видео полёта. Дополнительно просмотрены 12 ракурсов снизу. Ниже выборка через 30° сверху и все нижние ракурсы.

![Круговой осмотр сверху и снизу](orbit-contact.jpg)

[Все 36 верхних ракурсов одним листом](orbit-upper-all.jpg?raw=true).

## Нос, фонарь и пропорции

Понижен и изменён профиль фонаря, передняя часть корпуса получила более характерные грани. Размеры модели: около **20,10 × 14,10 м**, высота с шасси **4,60 м**. Для контроля использовались три ортографические проекции готовой геометрии.

![Три проекции без перспективы](model-orthos.png)

![Фонарь крупно](cockpit-detail-cockpit-close.png)

## Шасси и фонарь в движении

[**Видео: выпуск и уборка шасси**](gear.mp4?raw=true) · [**Видео: открытие и закрытие фонаря**](canopy.mp4?raw=true)

Ниши вырезаны в нижней поверхности корпуса; внутренние стенки и потолки подогнаны к новой форме. Последовательность открытия створок и движения стоек сохранена. Проверены промежуточные положения и полный обратный ход.

| Начало выпуска | Середина |
|---|---|
| ![](real-gear-out-1.png) | ![](real-gear-out-2.png) |

| Выпущено | Убрано |
|---|---|
| ![](real-gear-out-4.png) | ![](real-gear-back-4.png) |

![Шасси крупно сзади](gear-detail-rear-close.png)

![Самолёт на земле](ground-gear-side.png)

| Фонарь открывается | Фонарь открыт |
|---|---|
| ![](real-canopy-out-2.png) | ![](real-canopy-out-4.png) |

## Управление, сопла и торможение

[**Видео: реальные нажатия клавиш в полёте**](controls.mp4?raw=true)

Анимации привязаны к новым деталям: поверхности крыла и наплывов, стабилизаторы, цельноповоротные кили, сопла. Стыки сопел перекрыты внутренними кольцами, воздухозаборники имеют тёмные внутренние стенки. Отдельного тормозного щитка за кабиной нет; B включает игровое торможение с отклонением поверхностей.

Кадры ниже показывают фиксированные проверочные положения для осмотра деталей. Видео выше записано с клавиатурой без принудительных визуальных поз.

| Тангаж вверх | Тангаж вниз |
|---|---|
| ![](controls-pitch-up.png) | ![](controls-pitch-down.png) |

| Крен влево | Крен вправо |
|---|---|
| ![](controls-roll-left.png) | ![](controls-roll-right.png) |

| Рыскание влево | Рыскание вправо |
|---|---|
| ![](controls-rudder-left.png) | ![](controls-rudder-right.png) |

| Закрылки | Торможение |
|---|---|
| ![](controls-flaps-down.png) | ![](live-brake.png) |

![Форсаж и сопла](exhaust-ab-nozzles-quarter.png)

| Нижняя сторона в тени | Нижняя сторона к солнцу |
|---|---|
| ![](lighting-shaded-bottom.png) | ![](lighting-inverted-bottom.png) |

## Что проверено и откуда геометрия

- Круговой осмотр: 36 верхних + 12 нижних ракурсов.
- Полные циклы шасси и фонаря, шесть направлений управления, закрылки и торможение.
- Размеры, наклон килей, траектории колёс в проёмах, связи деталей и солнечное освещение.
- Су-27/МиГ-29 сохранены; ZIP проверен, содержит один Win32 GUI EXE.
- Включённые исходники повторно собраны отдельно: все пять файлов модели совпали побайтно.

Открытая геометрическая основа — [**ShFsn/Su-57 для FlightGear**](https://github.com/ShFsn/Su-57), файл Models/Su-57.ac, версия e7015f490233e78c59331f01cfbab7c5edf584b3, **GPL-3.0**. Адаптация включает окраску, анимационные узлы YSFlight, шасси и ниши, внутренние поверхности, стыки сопел и форму столкновений. [Исходники и лицензия](../../changes/su57-test-2/model-source/NOTICE.txt) также лежат в архиве: aircraft/su57-source. Это адаптация открытой модели, а не полностью самостоятельно созданная геометрия.

Проверки и три видео механизмов выполнены в **Win64/Wine**. В архиве Win32 EXE из первого теста; менялись данные модели. Прямой запуск на Windows 10 x86 здесь не проверялся. Аэродинамика и движения остаются игровым приближением, новая кабина с кнопками и внешние подвески в этот тест не входят.

[Проверки](checks.json) · [Клавиатура](keyboard-checks.json) · [Видео](video-checks.json) · [Круговой осмотр](orbit-checks.json) · [Целостность ZIP](package-checks.json)
'''
(dst/'REPORT.md').write_text(md)
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DVB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pages=[('Су-57: переделанная модель №2','Сравнение фактической геометрии в одном масштабе.', ['comparison-orthos.png']),('Пропорции: сверху, спереди, сбоку','Ортографические проекции готовой игровой модели.', ['model-orthos.png']),('Су-57 в игре','Настоящие кадры YSFlight: общий вид и вид сверху.', ['views-front-quarter.png','views-top.png']),('Спереди и сбоку','Изменены нос, фонарь, крыло, кили и воздухозаборники.', ['views-front.png','views-right.png']),('Сзади и снизу','Осмотр замыкания корпуса и соединения деталей.', ['views-rear.png','views-bottom.png']),('Круговой осмотр','Шаг 30° на листе; видео — шаг 10°, всего 48 осмотров.', ['orbit-contact.jpg']),('Шасси: выпуск и уборка','Промежуточные положения и возврат внутрь проёмов.', ['real-gear-out-1.png','real-gear-out-2.png','real-gear-out-4.png','real-gear-back-4.png']),('Механизмы и стоянка','Реальные ниши в нижней поверхности корпуса.', ['gear-detail-rear-close.png','ground-gear-side.png']),('Нос и фонарь','Форма закрытого фонаря и его открытие.', ['cockpit-detail-cockpit-close.png','real-canopy-out-4.png']),('Тангаж и сопла','Фиксированные проверочные положения для осмотра.', ['controls-pitch-up.png','controls-pitch-down.png']),('Крен и рыскание','Фиксированные проверочные положения для осмотра.', ['controls-roll-left.png','controls-roll-right.png','controls-rudder-left.png','controls-rudder-right.png']),('Закрылки и торможение','Привязаны к геометрии; отдельного щитка за кабиной нет.', ['controls-flaps-down.png','live-brake.png']),('Сопла и освещение','Форсаж; нижняя сторона, повёрнутая к солнцу.', ['exhaust-ab-nozzles-quarter.png','lighting-inverted-bottom.png'])]
pdf=repo/'downloads/Su57_Test_2_Photo_Report.pdf';c=canvas.Canvas(str(pdf),pagesize=(1000,800));c.setTitle('Су-57 — переделанная тестовая модель №2')
for i,(title,desc,images) in enumerate(pages):
 c.setFillColorRGB(.055,.075,.105);c.rect(0,0,1000,800,fill=1,stroke=0);c.setFillColorRGB(.96,.97,.99);c.setFont('DVB',22);c.drawString(25,762,title);c.setFont('DV',12);c.drawString(25,735,desc)
 boxes=[(25,383,465,320),(510,383,465,320),(25,45,465,320),(510,45,465,320)] if len(images)==4 else ([(25,390,950,325),(25,52,950,325)] if len(images)==2 else [(25,65,950,640)])
 for image,box in zip(images,boxes):c.drawImage(ImageReader(str(dst/image)),*box,preserveAspectRatio=True,anchor='c')
 c.setFont('DV',9);c.drawString(25,20,'Основа: ShFsn/Su-57 • GPL-3.0 • адаптация YSFlight • проверки Win64/Wine');c.drawRightString(975,20,f'{i+1}/{len(pages)}');c.showPage()
c.save()
changes=repo/'changes/su57-test-2';changes.mkdir(parents=True,exist_ok=True);shutil.copytree(lab/'runtime/aircraft/su57-source',changes/'model-source',dirs_exist_ok=True)
for name in ['verify_su57.py','capture.py','orbit.py','real-cycle.py','live_controls.py','video_su57.py','projections.py','report2.py','package_game.py']:shutil.copy2(lab/name,changes/name)
for name in ['su57.dnm','su57_coarse.dnm','su57coll.srf','su57.dat','su57cockpit.srf']:shutil.copy2(lab/'runtime/aircraft'/name,changes/name)
(dst/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dst.iterdir()) if p.is_file() and p.name!='manifest.json'},indent=2))
p=repo/'README.md';s=p.read_text();lead='**[Су-57 — переделанная модель №2: сравнение сверху/спереди, осмотр 360°](reports/su57-test-2/REPORT.md)** · [Скачать Windows 32-бит](downloads/YSFlight_Su57_Test_2_32bit.zip?raw=true)\n\n';s=s.replace('**[Су-57 — новая отдельная тестовая сборка, фото и видео]', '**[Су-57 — предыдущий тест №1, фото и видео]');lines=s.splitlines(True);
if lead not in s:lines.insert(2,lead)
p.write_text(''.join(lines))
print('REPORT ready:',len(pages),'PDF pages;',len(list(dst.glob('*.png'))),'pictures; 4 videos')
