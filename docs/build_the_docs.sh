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
# Note: Don't build scenePanel module, it causes error.
sphinx-apidoc --force -o . ../zBuilder

# To build the HTML documentation into a folder "_build"
# -W           : Turn warnings into errors
# --keep-going : With -W, Keep going when getting warnings
# -b BUILDER   : Builder to use (default: html)
rm -rf _build
sphinx-build -W --keep-going -b html . _build
