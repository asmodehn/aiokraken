# DEVELOP

This is a README for developers.

# PIPENV
This repository relies on pipenv for managing its virtual environment.

We also advise to setup direnv for seamless interaction with your shell.

# Python & tests from the Terminal

## Rest interface


## Websocket interface




# Jupyter & visual tests

We rely on Jupyter and Jupytext (to only have one .py file to care about) for quick visual interactivity.

Make sure you install a kernel with the current virtual environment.

From inside your virtualenv:

    pipenv install ipykernel
    python -m ipykernel install --user --name=$(basename $VIRTUAL_ENV)


 



