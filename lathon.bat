@echo off
set VERSION=v1.0.1
set RELEASE_NAME=Lathon_%VERSION%

echo [1/4] Cleaning...
if exist bin rd /s /q bin
if exist release rd /s /q release

echo [2/4] Structuring...
mkdir bin
mkdir release\Lathon\miktex

echo [3/4] Building lathon.exe...
pyinstaller --noconfirm --workpath ./bin --distpath ./release/Lathon lathon.spec

echo [4/4] Packaging and Cleaning...

:: Tenta copiar ReadMe com ou sem extensão .txt
if exist ReadMe copy ReadMe release\Lathon\ReadMe.txt >nul
if exist ReadMe.txt copy ReadMe.txt release\Lathon\ReadMe.txt >nul

:: Entra na pasta release para zipar
cd release
tar -a -c -f %RELEASE_NAME%.zip Lathon

:: Remove a pasta Lathon temporária
rd /s /q Lathon
cd ..

echo ==========================================
echo DONE! Only %RELEASE_NAME%.zip remains in /release
echo ==========================================
pause