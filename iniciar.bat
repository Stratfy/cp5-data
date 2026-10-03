@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 --version >nul 2>nul
    if not errorlevel 1 (
        py -3 "%~dp0app.py"
        goto fim
    )
)
where python >nul 2>nul
if not errorlevel 1 (
    python --version >nul 2>nul
    if not errorlevel 1 (
        python "%~dp0app.py"
        goto fim
    )
)
if exist "C:\Users\bruno\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    "C:\Users\bruno\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" "%~dp0app.py"
    goto fim
)
echo Python nao encontrado. Instale Python 3.10 ou superior e marque a opcao de adicionar ao PATH.
echo Depois, abra novamente este arquivo.
:fim
if errorlevel 1 pause
endlocal
