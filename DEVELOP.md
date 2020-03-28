# DEVELOP

This is a README for developers.

# PIPENV
This repository relies on pipenv for managing its virtual environment.

We also advise to setup direnv for seamless interaction with your shell.

# Python & tests from the Terminal

## Rest interface


## Websocket interface




# Jupyter & visual tests

Jupyter lab is probably a good solution, but in the mean time we sitkc with a specific way to manipulate notebooks.

We rely on Jupyter and Jupytext (to only have one .py file to care about) for quick visual interactivity.

Juyter and extensions should be installed in your user virtualenv (with --user).
No point having them in the application venv, and jupyter configuration is per user anyway.
You then need to start the Jupyter notebook server with the the root notebook directory as argument:

    jupyter notebook Projects/aiokraken

This is necessary so that:
- your virtual env for the app remains isolated in a kernel
- the jupyter server has access to all extension modules

We advise installing contrib extensions as well from https://jupyter-contrib-nbextensions.readthedocs.io/en/latest/install.html
Install hte extension configurator for better usage:
    
    pip install jupyter_nbextensions_configurator --user
    jupyter nbextensions_configurator enable --user

To make the application venv available from jupyter, you need to install a kernel with the current virtual environment.

From inside your application virtualenv:

    pipenv install ipykernel
    python -m ipykernel install --user --name=$(basename $VIRTUAL_ENV)


 



