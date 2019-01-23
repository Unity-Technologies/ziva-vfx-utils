@echo off

echo 'Configuring env2 virtualenv ...'
powershell -Command "Remove-Item '.\\env2' -Recurse -Force -ErrorAction Ignore"
py -2 -m pip install --user virtualenv 
py -2 -m virtualenv env2 
call .\env2\Scripts\activate
pip install -r requirements2.txt --ignore-installed
call .\env2\Scripts\deactivate
echo 'Done: configuring env2 virtualenv'

