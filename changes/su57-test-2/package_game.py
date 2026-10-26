from pathlib import Path
import zipfile,hashlib,json
lab=Path(__file__).resolve().parent;rt=lab/'runtime';repo=Path('/workspace/igraYS-Flight-Simulator');checks=json.loads((lab/'checks.json').read_text());assert checks['passed'];out=repo/'downloads/YSFlight_Su57_Test_2_32bit.zip';prefix='YSFlight_Su57_Test_2_32bit/'
readme='''СУ-57 — ОТДЕЛЬНАЯ ТЕСТОВАЯ ВЕРСИЯ №2, WINDOWS 32-БИТ

1. Полностью распакуйте ZIP в новую папку.
2. Дважды нажмите ysflight32_gl1.exe.
3. В главном меню нажмите «Су-57: тест модели».
   Либо выберите SU-57_FELON при создании обычного полёта.

Су-57 готов к полёту без ручного запуска систем.
На стоянке Q увеличивает тягу, A уменьшает; Tab — форсаж.
Стрелки — тангаж и крен; Z/C — направление; X — центрирование руля.
G — выпуск/уборка шасси. F/R — закрылки вниз/вверх.
B — воздушное торможение управляющими поверхностями.
Alt+5 — открыть/закрыть фонарь на стоянке или при малой скорости.
F2 — внешний вид. ПКМ с движением мыши — камера; колесо — масштаб.

Геометрия переработана на открытой основе ShFsn/Su-57 (GPL-3.0).
Исходники, лицензия и сведения об адаптации: aircraft/su57-source.
Основные размеры: около 20,1 м в длину и 14,1 м в размахе,
разнесённые двигатели, наклонные кили, сине-белая окраска.
Работают створки и стойки шасси, колёса и передняя рулевая стойка,
флапероны, закрылки, передние кромки, наплывы, стабилизаторы,
цельноповоротные кили, отклоняемые сопла, форсаж и фонарь.
Отдельного тормозного щитка за кабиной у модели нет.
Кабина от первого лица стандартная YSFlight, без новой кнопочной панели.
Внешние подвески в этой визуальной тестовой модели не добавлены.

Су-27 и МиГ-29 из предыдущего теста сохранены.
Игровые характеристики и кинематика упрощены; это не точная динамическая
копия настоящего самолёта и не результат испытаний на реальном Су-57.
Проверки выполнены в Win64/Wine. Архив содержит Win32 GUI EXE;
EXE сохранён из теста №1; запуск непосредственно на Windows 10 32-бит здесь не проверен.

Фото, видео, описание и результаты:
https://github.com/i7885784-lang/igraYS-Flight-Simulator/blob/ysflight-center-download/reports/su57-test-2/REPORT.md
'''
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(rt.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(rt)
  if p.name in ['READ_ME_RU.txt','TEST_RESULTS.txt'] or rel.parts[0]=='netchatlog' or p.suffix in ['.log','.script','.tmp']:continue
  if p.suffix.lower()=='.exe' and p.name!='ysflight32_gl1.exe':continue
  z.write(p,prefix+rel.as_posix())
 z.writestr(prefix+'READ_ME_RU.txt',readme.encode('utf-8-sig'))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 assert [a for a in z.namelist() if a.lower().endswith('.exe')]==[prefix+'ysflight32_gl1.exe']
 assert hashlib.sha256(z.read(prefix+'aircraft/su57.dnm')).hexdigest()==checks['model_sha256']
 assert hashlib.sha256(z.read(prefix+'ysflight32_gl1.exe')).hexdigest()==checks['exe_sha256']
result={'archive':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'single_Win32_GUI_EXE':True,'CRC_verified':True,'model_sha256':checks['model_sha256'],'exe_sha256':checks['exe_sha256']};(lab/'package-checks.json').write_text(json.dumps(result,indent=2));(repo/'downloads/SHA256SUMS_Su57_Test_2.txt').write_text(result['sha256']+'  '+out.name+'\n');print(json.dumps(result,indent=2))
