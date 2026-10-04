@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        py -3 "%~dp0app.py"
        goto fim
    )
)
where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        python "%~dp0app.py"
        goto fim
    )
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "%~dp0app.py"
    goto fim
)
echo Python 3.10 ou superior nao encontrado.
echo Instale uma versao compativel e marque a opcao de adicionar ao PATH.
echo Depois, abra novamente este arquivo.
pause
exit /b 1
:fim
if errorlevel 1 pause
endlocal
