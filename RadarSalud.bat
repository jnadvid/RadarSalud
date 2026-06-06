@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================================
echo    RadarSalud - instalacion y arranque automatico (Windows)
echo ================================================================
echo.
echo  Vigilancia poblacional con datos abiertos agregados.
echo  No usa datos personales. No diagnostica. No sustituye a
echo  profesionales sanitarios.
echo.

REM ---------------------------------------------------------------
REM  1. Detectar Python 3.11+
REM ---------------------------------------------------------------
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [ERROR] No se encontro Python.
  echo         Instala Python 3.11 o superior desde:
  echo         https://www.python.org/downloads/
  echo         y marca la casilla "Add Python to PATH" durante la instalacion.
  echo.
  pause
  exit /b 1
)
echo [OK] Python detectado: %PY%

REM ---------------------------------------------------------------
REM  2. Crear entorno virtual .venv (solo la primera vez)
REM ---------------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo [1/6] Creando entorno virtual .venv ...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
  )
) else (
  echo [1/6] Entorno virtual .venv ya existe.
)

set "VPY=.venv\Scripts\python.exe"
set "VRS=.venv\Scripts\radarsalud.exe"

REM ---------------------------------------------------------------
REM  3. Instalar / actualizar dependencias
REM ---------------------------------------------------------------
echo [2/6] Instalando dependencias (la primera vez puede tardar varios minutos)...
"%VPY%" -m pip install --upgrade pip >nul
"%VPY%" -m pip install -e ".[dev]"
if errorlevel 1 (
  echo [ERROR] Fallo la instalacion de dependencias.
  pause
  exit /b 1
)
echo [OK] Dependencias instaladas.

REM ---------------------------------------------------------------
REM  4. Crear base de datos SQLite y sembrar el catalogo de fuentes
REM ---------------------------------------------------------------
echo [3/6] Inicializando base de datos y catalogo de fuentes...
"%VRS%" init-db
if errorlevel 1 (
  echo [ERROR] Fallo la inicializacion de la base de datos.
  pause
  exit /b 1
)

REM ---------------------------------------------------------------
REM  5. Ingesta de datos reales abiertos (requiere internet).
REM     Si falla por red, continuamos: el sistema sigue siendo usable.
REM ---------------------------------------------------------------
echo [4/6] Ingesta de datos reales abiertos (requiere internet)...
"%VRS%" ingest-all
if errorlevel 1 (
  echo [AVISO] La ingesta no se completo (posible falta de internet). Se continua.
)

REM ---------------------------------------------------------------
REM  6. Deteccion de anomalias sobre datos reales
REM ---------------------------------------------------------------
echo [5/6] Detectando anomalias en datos reales...
"%VRS%" analyze --mode real
if errorlevel 1 (
  echo [AVISO] El analisis no genero resultados (puede que aun no haya datos). Se continua.
)

REM ---------------------------------------------------------------
REM  7. Abrir el navegador y arrancar el servidor local
REM ---------------------------------------------------------------
echo [6/6] Arrancando servidor en http://127.0.0.1:8000 ...
echo.
echo  Se abrira el navegador automaticamente en unos segundos.
echo  Paginas:  Panel    http://127.0.0.1:8000/
echo            Mapa     http://127.0.0.1:8000/map
echo            Simular  http://127.0.0.1:8000/simulation
echo            Fuentes  http://127.0.0.1:8000/sources
echo            API      http://127.0.0.1:8000/docs
echo.
echo  Para DETENER el servidor: pulsa Ctrl+C en esta ventana o cierrala.
echo ================================================================

REM Abrir el navegador con un pequeno retardo, en una ventana aparte,
REM mientras el servidor arranca en primer plano.
start "" cmd /c "timeout /t 5 >nul & start http://127.0.0.1:8000/"

"%VRS%" serve

echo.
echo Servidor detenido.
endlocal
pause
