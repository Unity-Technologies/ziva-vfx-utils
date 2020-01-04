# install sphinx
pip install -U sphinx

# install sphinx rtd theme
pip install sphinx_rtd_theme

# this generates the auto docs for the code.  Run it in 'docs' directory.
# --force        : Force overwriting of any existing generated files.
# -o .           : Put output files in `pwd`
# ../zBuilder    : The module to parse
# ../zBuilder/ui : Skip this module, because shiboken and PySide break the doc gen.
sphinx-apidoc --force -o . ../zBuilder ../zBuilder/ui*

rm -rf _build
# To build the HTML documentation into a folder "_build"
# -W           : Turn warnings into errors
# --keep-going : With -W, Keep going when getting warnings
# -b BUILDER   : Builder to use (default: html)
sphinx-build -W --keep-going -b html . _build