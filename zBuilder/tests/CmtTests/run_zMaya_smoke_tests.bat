@echo off
: default maya version is 2018 unless overriden by a parameter
if "%~1"=="" (
    set mayaYear=2018
) else (
    set mayaYear=%1
)

python %~dp0..\..\..\CMT\bin\runmayatests.py -m %mayaYear% --path %~dp0%tests