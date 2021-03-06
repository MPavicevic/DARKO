![Image of License](https://img.shields.io/badge/license-EUPL%20v1.2-blue)
[![Build Status](https://travis-ci.com/MPavicevic/DARKO.svg?branch=master)](https://travis-ci.com/MPavicevic/DARKO)
[![codecov](https://codecov.io/gh/MPavicevic/DARKO/branch/master/graph/badge.svg)](https://codecov.io/gh/MPavicevic/DARKO)


DARKO
=======
**DARKO** is acronim for **D**ay-**a**head M**rk**et **O**ptimization package. It is based in Python and solved in GAMS. 

Description
-----------
DARKO is a small energy market analysis project (mostly day ahead, but can also be multi day, weekly, monthly or anual). Main features:

- Demand orders
- Simple orders
- Block orders
- Flexible orders
- NTC's (ramping limits: both hourly and per period)
- Net positions (ramping limits: both hourly and per period)

The main purpose of this package is simmulation of energy markets with multiple players and interconnected zones  

Quick start
===========

Prerequisites
-------------
If you want to download the latest version from github for use or development purposes, make sure that you have git and the [anaconda distribution](https://www.anaconda.com/distribution/) or [miniconda distribution](https://docs.conda.io/en/latest/miniconda.html) installed and type the following:

Anaconda Prompt
---------------
```bash
git clone https://github.com/MPavicevic/DARKO.git
cd ..Documents\git\DARKO
conda env create  # Automatically creates environment based on environment.yml
conda activate DARKO # Activate the environment
pip install -e . # Install editable local version
```

The above commands create a dedicated environment so that your anaconda configuration remains clean from the required dependencies installed.

Projects
========
Release date: TBD

Get involved
============
This project is an open-source project. Interested users are therefore invited to test, comment or [contribute](CONTRIBUTING.md) to the tool. Submitting issues is the best way to get in touch with the development team, which will address your comment, question, or development request in the best possible way. We are also looking for contributors to the main code, willing to contibute to its capabilities, computational-efficiency, formulation, etc. Finally, we are willing to collaborate with national agencies, reseach centers, or academic institutions on the use on the model for different data sets relative to EU countries.

Main developers
===============
Currently the main developers of the DARKO package are the following:

- Matija Pavičević  (KU Leuven, Belgium)


