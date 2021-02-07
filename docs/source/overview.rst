.. _overview:

Overview
========

:Version: |version| (|release|)
:Date: |today|


Features
--------

- Demand orders
- Simple orders
- Block orders
- Flexible orders
- Storage orders
- NTC's (ramping limits: both hourly and per period)
- Net positions (ramping limits: both hourly and per period)


Libraries used and requirements
-------------------------------

* `Python 3.7`_
* `pandas`_ for input and result data handling
* `matplotlib`_ for plotting
* `GAMS_api`_ for the communication with GAMS

the above are auto installed in a conda environment if you follow the instructions of the Quick start.

DARKO in the scientific literature
--------------------------------------

* Micro-scale heat market  [1]_.


Ongoing developments
--------------------
The DARKO project is relatively recent, and a number of improvements will be brought to the project in a close future:

- Results analysis (outputs, plots...)


Licence
-------
DARKO is a free software licensed under the “European Union Public Licence" EUPL v1.2. It
can be redistributed and/or modified under the terms of this license.

Main Developers
---------------
- Matija Pavičević  (KU Leuven, Belgium)


References
----------
.. [1] Sebestyén, T.T. and Pavičević, M. and Dorotić, H. and Krajačić, G. (2020). The establishment of a micro-scale heat market using a biomass-fired district heating system. *Energy, Sustainability and Society*, doi:10.1186/s13705-020-00257-2


.. _Python 3.7: https://www.anaconda.com/distribution/
.. _matplotlib: http://matplotlib.org
.. _pandas: http://pandas.pydata.org
.. _GAMS_api: https://github.com/kavvkon/gams-api



