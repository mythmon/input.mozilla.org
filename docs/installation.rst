============
Installation
============

Note: The bulk of installation is covered in the `README.md` file.

Vendor Library
--------------

Input uses a vendor library to manage its dependencies.  It i s a git submodule. Either clone this repository with `--recurseive`, or after you already have a checkout out, run::

    git submodule sync
    git submodule update --init --recursive
