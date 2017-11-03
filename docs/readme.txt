make clean
make html

# using napoleaon extension for docstrings, this may come with sphinx now.  I used pip to get it.
pip install sphinxcontrib-napoleon

# this generates the auto docs for the code.  Run it in 'docs' directory.
# -f forces re-do of existing docs.
sphinx-apidoc -f -o . ../zBuilder