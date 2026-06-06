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
if not defined PY goto NO_PYTHON
echo [OK] Python detectado: %PY%

REM ---------------------------------------------------------------
REM  2. Crear entorno virtual .venv  [solo la primera vez]
REM ---------------------------------------------------------------
if exist ".venv\Scripts\python.exe" goto VENV_OK
echo [1/6] Creando entorno virtual .venv ...
%PY% -m venv .venv
if errorlevel 1 goto ERR_VENV
goto VENV_DONE
:VENV_OK
echo [1/6] Entorno virtual .venv ya existe.
:VENV_DONE

set "VPY=.venv\Scripts\python.exe"
set "VRS=.venv\Scripts\radarsalud.exe"

REM ---------------------------------------------------------------
REM  3. Instalar / actualizar dependencias
REM ---------------------------------------------------------------
echo [2/6] Instalando dependencias. La primera vez puede tardar varios minutos...
"%VPY%" -m pip install --upgrade pip >nul
"%VPY%" -m pip install -e ".[dev]"
if errorlevel 1 goto ERR_PIP
echo [OK] Dependencias instaladas.

REM ---------------------------------------------------------------
REM  4. Crear base de datos SQLite y sembrar el catalogo de fuentes
REM ---------------------------------------------------------------
echo [3/6] Inicializando base de datos y catalogo de fuentes...
"%VRS%" init-db
if errorlevel 1 goto ERR_DB

REM ---------------------------------------------------------------
REM  5. Ingesta de datos reales abiertos. Requiere internet.
REM     Si falla por red, continuamos: el sistema sigue siendo usable.
REM ---------------------------------------------------------------
echo [4/6] Ingesta de datos reales abiertos. Requiere internet...
"%VRS%" ingest-all
if errorlevel 1 echo [AVISO] La ingesta no se completo. Posible falta de internet. Se continua.

REM ---------------------------------------------------------------
REM  6. Deteccion de anomalias sobre datos reales
REM ---------------------------------------------------------------
echo [5/6] Detectando anomalias en datos reales...
"%VRS%" analyze --mode real
if errorlevel 1 echo [AVISO] El analisis no genero resultados todavia. Se continua.

REM ---------------------------------------------------------------
REM  7. Abrir el navegador y arrancar el servidor local
REM ---------------------------------------------------------------
echo [6/6] Arrancando servidor en http://127.0.0.1:8000 ...
echo.
echo  Se abrira el navegador automaticamente en unos segundos.
echo  Paginas:
echo    Panel    http://127.0.0.1:8000/
echo    Mapa     http://127.0.0.1:8000/map
echo    Simular  http://127.0.0.1:8000/simulation
echo    Fuentes  http://127.0.0.1:8000/sources
echo    API      http://127.0.0.1:8000/docs
echo.
echo  Para DETENER el servidor: pulsa Ctrl+C en esta ventana o cierrala.
echo ================================================================

REM Abrir el navegador con un pequeno retardo, en una ventana aparte,
REM mientras el servidor arranca en primer plano.
start "" cmd /c "timeout /t 5 >nul & start http://127.0.0.1:8000/"

"%VRS%" serve

echo.
echo Servidor detenido.
goto END

REM ===============================================================
REM  Rutas de error. Mantienen la ventana abierta con pause.
REM ===============================================================
:NO_PYTHON
echo [ERROR] No se encontro Python.
echo         Instala Python 3.11 o superior desde:
echo         https://www.python.org/downloads/
echo         y marca la casilla "Add Python to PATH" al instalar.
goto END

:ERR_VENV
echo [ERROR] No se pudo crear el entorno virtual.
goto END

:ERR_PIP
echo [ERROR] Fallo la instalacion de dependencias.
goto END

:ERR_DB
echo [ERROR] Fallo la inicializacion de la base de datos.
goto END

:END
echo.
pause
endlocal
