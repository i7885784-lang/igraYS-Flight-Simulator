# Движок теста №9

В полном архиве исходников `engine/YSFLIGHT/src` и `engine/public/src` уже содержат изменения.
Исходники и объявления об авторских правах сохранены. `engine-files.json` фиксирует SHA-256
изменённых файлов; патч проверяется на полное совпадение перед созданием ZIP.

Проверенная сборка: Linux, CMake/Ninja, MinGW-w64 i686 POSIX, Release, C++11.
Компилятор `i686-w64-mingw32-g++-posix`, C `i686-w64-mingw32-gcc-posix`, RC
`i686-w64-mingw32-windres`; toolchain задаёт `CMAKE_SYSTEM_NAME Windows`,
`CMAKE_SYSTEM_PROCESSOR x86`. Директория исходников CMake — `engine/YSFLIGHT/src`.

Параметры: `CMAKE_CXX_FLAGS=-DWIN32 -D_WINDOWS -DNOMINMAX -fpermissive -fno-delete-null-pointer-checks`,
`CMAKE_C_FLAGS=-Wno-error=incompatible-pointer-types`,
`CMAKE_EXE_LINKER_FLAGS=-static -static-libgcc -static-libstdc++ -mwindows`;
`CMAKE_SHARED_LINKER_FLAGS=-static -static-libgcc -static-libstdc++`.
`CMAKE_CXX_STANDARD_LIBRARIES=-lkernel32 -luser32 -lgdi32 -lwinspool -lshell32 -lole32 -loleaut32 -luuid -lcomdlg32 -ladvapi32 -limm32`.
Цель: `ysflight32_gl1`. Готовый EXE: `build32/main/ysflight32_gl1.exe`.
Плагины звука/голоса унаследованы из полной основы №8; их интерфейсы не менялись.

Проверочный Win64 собирается тем же кодом с компиляторами x86_64-w64-mingw32,
`CMAKE_SYSTEM_PROCESSOR x86_64`, целью `ysflight64_gl1` и дополнительным
`-DV861_VALIDATION`. Он используется только для съёмки/автопроверок и в игровой ZIP
не включается. Win32 GUI EXE проверен как PE i386, без проверочной команды MODELPOSE.
Это не заменяет прямой запуск на Windows 10 x86, который в облаке не выполнялся.

В тесте №9 native.patch применяется к полному engine/ из исходников №8. Изменены быстрые кнопки главного меню, плавность раскрытия на форсаже и обработка прозрачных граней OpenGL 1.
