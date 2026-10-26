#!/bin/bash
set -euo pipefail
repo=/workspace/igraYS-Flight-Simulator
dev=/workspace/ysflight-dev
bundle=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$dev/apt/lists/partial" "$dev/apt/archives/partial" "$dev/tools"
cat > "$dev/apt/sources.list" <<'EOF'
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://deb.debian.org/debian trixie main
deb [signed-by=/usr/share/keyrings/debian-archive-keyring.gpg] https://security.debian.org/debian-security trixie-security main
EOF
apt_opts=(-o Dir::State::lists="$dev/apt/lists" -o Dir::Cache::archives="$dev/apt/archives" -o Dir::Etc::parts=- -o Dir::Etc::sourcelist="$dev/apt/sources.list" -o Dir::Etc::sourceparts=- -o Debug::NoLocking=1)
/usr/bin/apt-get "${apt_opts[@]}" update
/usr/bin/apt-get "${apt_opts[@]}" --download-only --no-install-recommends -y install cmake ninja-build g++-mingw-w64-i686-posix g++-mingw-w64-x86-64-posix wine64 xvfb xauth
sha256sum "$dev"/apt/archives/*.deb > "$dev/apt/deb-manifest.new"
if ! cmp -s "$dev/apt/deb-manifest.new" "$dev/tools/deb-manifest.txt"; then
  for p in "$dev"/apt/archives/*.deb; do dpkg-deb -x "$p" "$dev/tools"; done
  cp "$dev/apt/deb-manifest.new" "$dev/tools/deb-manifest.txt"
fi
for arch in i686 x86_64; do
  ln -sfn "$arch-w64-mingw32-gcc-posix" "$dev/tools/usr/bin/$arch-w64-mingw32-gcc"
  ln -sfn "$arch-w64-mingw32-g++-posix" "$dev/tools/usr/bin/$arch-w64-mingw32-g++"
done
# Adapt Debian's launcher and data lookup to the private prefix, without touching game code.
cat > "$dev/tools/usr/lib/wine/wineserver" <<'EOF'
#!/bin/sh
exec /workspace/ysflight-dev/tools/usr/lib/wine/wineserver64 -p120 "$@"
EOF
ln -sfn . "$dev/tools/usr/share/wine/wine"
ln -sfn ../../../../x86_64-w64-mingw32/lib/zlib1.dll "$dev/tools/usr/lib/x86_64-linux-gnu/wine/x86_64-windows/zlib1.dll"
if [ "$bundle" != "$dev" ]; then
  for f in env.sh build.sh start.sh capture.py package.py; do cp "$bundle/$f" "$dev/$f"; done
fi
python3 - <<'PY'
from pathlib import Path
import hashlib, zipfile, shutil, json
r=Path('/workspace/igraYS-Flight-Simulator');d=Path('/workspace/ysflight-dev')
for name,sha in [('YSFlight_Su57_Test_2_32bit','ad8fa53419f06532e25d65669d83b785d6d4c5568ee6fbf0d530d00bab038697'),('YSFlight_Su57_Test_2_Engine_Source','378c67577ae088fbe7b38cf3847d78f985639665ddebc4840e9db7b9ea78e6c5')]:
    p=r/'downloads'/(name+'.zip');assert hashlib.sha256(p.read_bytes()).hexdigest()==sha
    if not (d/name).exists():
        with zipfile.ZipFile(p) as z: assert z.testzip() is None;z.extractall(d)
s=d/'YSFlight_Su57_Test_2_Engine_Source'
manifest=json.loads((s/'SOURCE_MANIFEST.json').read_text())
assert all(hashlib.sha256((s/p).read_bytes()).hexdigest()==sha for p,sha in manifest.items())
p=s/'YSFLIGHT/scripts/runtime_timestamp.py';p.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(r/'downloads/YSFlight_v8_6_2_Sources.zip') as z:
    p.write_bytes(z.read('YSFlight_v8_6_2_Sources/YSFLIGHT/scripts/runtime_timestamp.py'))
if not (s/'YSFLIGHT/runtime').exists():shutil.copytree(d/'YSFlight_Su57_Test_2_32bit',s/'YSFLIGHT/runtime')
for p in (s/'YSFLIGHT/runtime').glob('*.exe'): p.unlink()
if not (d/'model-source').exists():shutil.copytree(r/'changes/su57-test-2/model-source',d/'model-source')
(d/'mingw64.cmake').write_text((s/'mingw32.cmake').read_text().replace('x86','x86_64').replace('i686','x86_64'))
PY
python3 -c 'import numpy,scipy,PIL'
bash "$dev/build.sh" 32
bash "$dev/build.sh" 64
bash "$dev/start.sh"
