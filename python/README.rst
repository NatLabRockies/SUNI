Welcome to PySUNI!
==================

Installation instructions
-------------------------

1. From a desired code directory, download this repository using ``git clone git@github.com:NREL/SUNI.git``

2. Create ``suni`` environment and install package
    1) Create a conda env: ``conda create -n suni python=3.11``
    2) Activate the newly-created environment using the command: ``conda activate suni``
    3) cd into the repo cloned in 1.
    4) Install ``suni`` and its dependencies by running: ``pip install .``

3. Check that ``suni`` was installed successfully
    1) From any directory, run the following command. This should return the
       help pages for the CLI.

        - ``suni --help``

You can now use the `sample config <https://github.com/NREL/SUNI/blob/main/python/tests/data/basic_run/sample_config.json>`_
as a template to set up your own runs and then execute them using

``suni config.json``

