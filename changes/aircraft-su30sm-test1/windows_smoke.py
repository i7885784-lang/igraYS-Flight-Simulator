from pathlib import Path
import subprocess, tempfile, zipfile, time, json, hashlib

repo = 'i7885784-lang/igraYS-Flight-Simulator'
tag = 'personal-su30sm-test1-20261103'
evidence = Path('windows-evidence').resolve()
evidence.mkdir(exist_ok=True)

def gh(*args):
    return subprocess.check_output(['gh', *args])

with tempfile.TemporaryDirectory() as td:
    temp = Path(td)
    gh('release', 'download', tag, '--repo', repo, '--pattern', 'YSFlight_Su30SM_Test_1_Game_32bit.zip', '--pattern', 'YSFlight_Su30SM_Test_1_Report.zip', '--pattern', 'STATUS.json', '--dir', str(temp))
    status = json.loads((temp / 'STATUS.json').read_text())
    archive = temp / 'YSFlight_Su30SM_Test_1_Game_32bit.zip'
    expected = next(a['sha256'] for a in status['assets'] if a['name'] == archive.name)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
    with zipfile.ZipFile(archive) as z:
        z.extractall(temp)
    game = temp / 'YSFlight_Su30SM_Test_1_Game'
    script = ('WAITFOR:GUI\nSLEEP:500\n' + 'GUI:CLOSEMODAL\n' * 4 +
              'SLEEP:1500\nFILE:OPEN Su30SM_Play.yfs\nGUI:CLICK mainDlg flyNow\n'
              'WAITFOR:FLYING\nBTNFUNC:OUTSIDEPLAYERVIEW\nBTNFUNC:LANDINGGEAR\n'
              'SLEEP:9000\nBTNFUNC:LANDINGGEAR\nSLEEP:9000\nREM SU30_X86_FLIGHT_AND_GEAR_COMPLETE\nSLEEP:60000\n')
    (game / 'WindowsSmoke.script').write_text(script)
    log = evidence / 'windows-x86.log'
    began = time.monotonic()
    with log.open('w') as f:
        app = subprocess.Popen([str(game / 'ysflight32_gl1.exe'), '-script', 'WindowsSmoke.script'], cwd=game, stdout=f, stderr=f)
        try:
            while time.monotonic() - began < 180:
                text = log.read_text(errors='replace')
                if app.poll() is not None:
                    raise RuntimeError('Windows x86 game exited: ' + str(app.returncode) + '\n' + text[-2000:])
                if 'Script>>REM SU30_X86_FLIGHT_AND_GEAR_COMPLETE' in text:
                    break
                time.sleep(1)
            else:
                raise RuntimeError('Windows x86 flight timeout\n' + log.read_text(errors='replace')[-2000:])
            # Capture the real Windows desktop; visual review remains separate from the launch assertion.
            ps = ('Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; '
                  '$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; '
                  '$i=New-Object System.Drawing.Bitmap($b.Width,$b.Height); '
                  '$g=[System.Drawing.Graphics]::FromImage($i); '
                  '$g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size); '
                  '$i.Save("' + str(evidence / 'windows-x86.png') + '"); $g.Dispose(); $i.Dispose()')
            subprocess.run(['powershell', '-NoProfile', '-Command', ps], check=True)
            result = {'passed': True, 'platform': 'native Windows runner', 'architecture': 'PE32 i386',
                      'elapsed_seconds': round(time.monotonic() - began, 2),
                      'scope': 'Su-30SM flight loaded; two native landing gear commands; process remained running'}
            (evidence / 'result.json').write_text(json.dumps(result, indent=2))
            status['windows_x86'] = result
        finally:
            app.terminate()
            try:
                app.wait(timeout=10)
            except subprocess.TimeoutExpired:
                app.kill()
    report_zip = temp / 'YSFlight_Su30SM_Test_1_Report.zip'
    report_dir = temp / 'report-final'
    with zipfile.ZipFile(report_zip) as z:
        z.extractall(report_dir)
    report_root = report_dir / 'Su30SM_Report'
    text = (report_root / 'index.html').read_text(encoding='utf-8')
    text = text.replace('Проверка запуска Windows x86 выполняется при загрузке архивов; актуальный отдельный протокол — STATUS.json в черновике GitHub.',
                        'Запуск на настоящем Windows x86: пройден. Загружен полёт на Су-30СМ, выполнены две команды шасси, приложение продолжило работать. Это проверка запуска и команд; подробная геометрия проверена отдельно в 101 положении.')
    text = text.replace('<div id="windows-evidence"></div>', '<figure><a href="windows-x86.png"><img src="windows-x86.png" alt="Windows x86"></a><figcaption>Реальный запуск 32-битной игры на Windows. <a href="windows-result.json">Протокол</a></figcaption></figure>')
    (report_root / 'index.html').write_text(text, encoding='utf-8')
    import shutil
    shutil.copy2(evidence / 'windows-x86.png', report_root / 'windows-x86.png')
    shutil.copy2(evidence / 'result.json', report_root / 'windows-result.json')
    shutil.copy2(log, report_root / 'windows-x86.log')
    with zipfile.ZipFile(report_zip, 'w', zipfile.ZIP_DEFLATED, 6) as z:
        for p in sorted(report_root.rglob('*')):
            if p.is_file():
                z.write(p, 'Su30SM_Report/' + str(p.relative_to(report_root)))
    with zipfile.ZipFile(report_zip) as z:
        assert z.testzip() is None
    digest = hashlib.sha256(report_zip.read_bytes()).hexdigest()
    gh('release', 'upload', tag, str(report_zip), '--repo', repo, '--clobber')
    verify = temp / 'verify-report'
    verify.mkdir()
    gh('release', 'download', tag, '--repo', repo, '--pattern', report_zip.name, '--dir', str(verify))
    assert hashlib.sha256((verify / report_zip.name).read_bytes()).hexdigest() == digest
    asset = next(a for a in status['assets'] if a['name'] == report_zip.name)
    asset.update(sha256=digest, bytes=report_zip.stat().st_size, download_verified=True)
    Path('reports/su30sm-test-1/STATUS.json').write_text(json.dumps(status, indent=2))
    gh('release', 'upload', tag, 'reports/su30sm-test-1/STATUS.json', '--repo', repo, '--clobber')
    gh('release', 'upload', tag, str(evidence / 'result.json'), str(evidence / 'windows-x86.png'), str(log), '--repo', repo, '--clobber')
