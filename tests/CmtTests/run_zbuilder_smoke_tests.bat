@echo off
echo|set /p="activating virtual environment ..."
call %~dp0env2\Scripts\activate
echo done

@echo off
: default maya version is 2018 unless overriden by a parameter
if "%~1"=="" (
    set mayaYear=2018
) else (
    set mayaYear=%1
)

python %~dp0..\..\CMT\bin\runmayatests.py ^
    -m %mayaYear% ^
    --path %~dp0%tests ^
    --maya-script-path %~dp0..\..\scripts

echo %~dp0..\..\scripts
echo|set /p="deactivating virtual environment ..."
call %~dp0env2\Scripts\deactivate
echo done
