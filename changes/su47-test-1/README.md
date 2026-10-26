# Su-47 Berkut test 1

Experimental addition to the complete Su-57 test 2 baseline; this does not change CURRENT_VERSION.

- `model-source/`: editable GPL-3.0 MLOD, memory/selections configuration, license, portable reader/converter and pinned Python dependencies.
- `native.patch`: production integration for the new identifier, animation driver and program title. Apply once to the preserved Su-57 engine source snapshot. Existing aircraft branches remain unchanged.
- `setup.sh`: tested cloud setup using the existing checkout and /workspace/ysflight-dev; verifies engine hashes before applying the patch, preserves unrelated engine edits by stopping rather than overwriting them.
- `check_game.py`: actual Wine/X11 game screenshots and native XTest keyboard scenarios. Copies/runs under /workspace/ysflight-dev/su47-test-1 via setup.sh.
- `validate.py`, `package.py`: validate current scenario outputs and assemble the independent Win32 game/source archives.

See [the report](../../reports/su47-test-1/REPORT.md) for evidence and limitations. The Win64 diagnostic build is for testing only and is not shipped in the game ZIP. The runtime is a game approximation, not a certified Su-47 simulator.
