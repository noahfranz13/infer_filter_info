Introduction
============

In an ideal world, we would always have the telescope filter name, telescope facility name, and the instrument name. 
However, in the real world, we might only have one or two of these things. 
In this case, we need to make assumptions to derive information about the filter, namely the effective wavelength and transmission function. 

The goal of this mini python package is to standardize the way we do this.

Installation
------------

You can install the package directly from PyPI:

.. code-block:: bash

   pip install infer-filter-info

Developer Installation
----------------------

To install the package from source for development:

.. code-block:: bash

   git clone https://github.com/noahfranz13/infer_filter_info.git
   cd infer_filter_info
   pip install -e .[dev,docs]
