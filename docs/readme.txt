
# install sphinx
pip install -U sphinx

# install sphinx rtd theme
pip install sphinx_rtd_theme


# using napoleaon extension for docstrings, this may come with sphinx now.  I used pip to get it.
pip install sphinxcontrib-napoleon

# this generates the auto docs for the code.  Run it in 'docs' directory.
# -f forces re-do of existing docs.
sphinx-apidoc -f -o . ../zBuilder

# To build the HTML documentation into a folder "_build",
sphinx-build -b html . _build
# or, if you have make:
make clean
make html
