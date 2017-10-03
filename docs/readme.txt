make clean
make html

# this generates the auto docs for the code.  Run it in 'docs' directory.
# -f forces re-do of existing docs.
sphinx-apidoc -f -o . ../zBuilder