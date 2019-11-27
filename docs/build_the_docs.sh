#!/bin/bash
# Build the docs into '_build' in the same directory as the source.

set -euo pipefail # http://redsymbol.net/articles/unofficial-bash-strict-mode/
IFS=$'\n\t'

# https://stackoverflow.com/questions/59895/get-the-source-directory-of-a-bash-script-from-within-the-script-itself
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd ${SCRIPT_DIR}

# sphinx-apidoc:
# --force        : Force overwriting of any existing generated files.
# -o .           : Put output files in `pwd`
# ../zBuilder    : The module to parse
# ../zBuilder/ui : Skip this module, because shiboken and PySide break the doc gen.
sphinx-apidoc --force -o . ../zBuilder ../zBuilder/ui*

rm -rf _build
sphinx-build -W --keep-going -b html . _build