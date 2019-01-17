#!/bin/bash
ScriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MayaYear="2014"
if [ ! -z "$1" ] 
    then MayaYear=$1 # if argument supplied - treat it as a maya year
fi
export zivadyn_LICENSE="/var/ziva/ziva_internal_use.lic"
python $ScriptDir/../../../CMT/bin/runmayatests.py --maya $MayaYear --path ${ScriptDir}/tests

