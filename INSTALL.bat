@echo off

REM Step 1: Check for Python installation between versions 3.10.0 and 3.10.15
echo Checking for existing Python installation between versions 3.10.0 and 3.10.15...

for /f "tokens=2 delims= " %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
if not defined PYTHON_VERSION (
    echo Python is not installed. Proceeding to install Python 3.10.11...
    goto INSTALL_PYTHON
)

REM Python version has been retrieved, now check the version range
for /f "tokens=1,2,3 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
    set PYTHON_PATCH=%%c
)

if %PYTHON_MAJOR% neq 3 (
    echo Python version is outside the required range. Proceeding to install Python 3.10.11...
    goto INSTALL_PYTHON
)

if %PYTHON_MINOR% neq 10 (
    echo Python version is outside the required range. Proceeding to install Python 3.10.11...
    goto INSTALL_PYTHON
)

if %PYTHON_PATCH% lss 0 if %PYTHON_PATCH% gtr 15 (
    echo Python version is outside the required range. Proceeding to install Python 3.10.11...
    goto INSTALL_PYTHON
)

echo Python version is acceptable.
goto CHECK_GPU

:INSTALL_PYTHON
echo Installing Python 3.10.11...
set PYTHON_VERSION=3.10.11
set PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe
set PYTHON_INSTALLER=python-%PYTHON_VERSION%-amd64.exe

echo Downloading Python %PYTHON_VERSION% installer...
powershell -Command "Start-BitsTransfer -Source '%PYTHON_INSTALLER_URL%' -Destination '%PYTHON_INSTALLER%'" > NUL 2>&1

echo Installing Python...
start /wait "" %PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 > NUL 2>&1

set "PYTHON_DIR=C:\Program Files\Python310"
set "PATH=%PYTHON_DIR%;%PYTHON_DIR%\Scripts;%PATH%"
set "PYTHON_EXEC=%PYTHON_DIR%\python.exe"

echo Python installed. Proceeding to GPU check...
goto CHECK_GPU

:CHECK_GPU
echo Checking for CUDA-compliant GPU using PowerShell...
powershell -Command "Get-WmiObject Win32_VideoController | Where-Object { $_.Name -like '*NVIDIA*' }" > NUL 2>&1
if %ERRORLEVEL% equ 0 (
    echo NVIDIA GPU detected.
    set CUDA_GPU=1
) else (
    echo No NVIDIA GPU detected.
    set CUDA_GPU=0
)

where nvcc > NUL 2>&1
if %ERRORLEVEL% equ 0 (
    echo CUDA is already installed.
    set CUDA_INSTALLED=1
) else (
    echo CUDA is not installed.
    set CUDA_INSTALLED=0
)

if %CUDA_GPU% equ 1 if %CUDA_INSTALLED% equ 0 (
    goto INSTALL_CUDA
)

goto INSTALL_TORCH

:INSTALL_CUDA
echo Downloading and installing CUDA 11.7...
set CUDA_INSTALLER_URL=https://developer.download.nvidia.com/compute/cuda/11.7.0/local_installers/cuda_11.7.0_516.01_windows.exe
set CUDA_INSTALLER=cuda_11.7.0_516.01_windows.exe

powershell -Command "Start-BitsTransfer -Source '%CUDA_INSTALLER_URL%' -Destination '%CUDA_INSTALLER%'" > NUL 2>&1

echo Running CUDA 11.7 installer...
start /wait "" %CUDA_INSTALLER% -s > NUL 2>&1

set CUDA_INSTALLED=1
goto INSTALL_TORCH

:INSTALL_TORCH
echo Installing Torch...
if %CUDA_GPU% equ 1 if %CUDA_INSTALLED% equ 1 (
    echo Installing GPU-enabled Torch...
    "%PYTHON_EXEC%" -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/test/cu118 > NUL 2>&1
) else (
    echo Installing CPU-only Torch...
    "%PYTHON_EXEC%" -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/test/cpu > NUL 2>&1
)

goto INSTALL_PADDLE

:INSTALL_PADDLE
echo Installing PaddlePaddle...
if %CUDA_GPU% equ 1 if %CUDA_INSTALLED% equ 1 (
    echo Installing PaddlePaddle-GPU...
    "%PYTHON_EXEC%" -m pip install paddlepaddle-gpu==2.6.1.post117 -f https://www.paddlepaddle.org.cn/whl/windows/mkl/avx/stable.html > NUL 2>&1
) else (
    echo Installing CPU-only PaddlePaddle...
    "%PYTHON_EXEC%" -m pip install paddlepaddle==2.6.1 -f https://www.paddlepaddle.org.cn/whl/windows/mkl/avx/stable.html > NUL 2>&1
)

goto INSTALL_REQUIREMENTS

:INSTALL_REQUIREMENTS
echo Installing dependencies from requirements.txt...
"%PYTHON_EXEC%" -m pip install -r requirements.txt > NUL 2>&1

echo Installation complete.
pause
