Faraday1
========

A simple control program for the Faraday Rotation system at Hamilton.

Main Branch
-----------

Main Branch adds  new pane to the live plot tab that runs a separate
data loop collecting one full (uninteruptible) set of data which it then
subjects to Fourier analysis. This is being created but has no functionality
yet (3/30/23).

PreFourier Branch
--------------

PreFourier branch has basic working code for live plotting with user selecting which
traces are plotted. You can start and stop a plot and you can save the most recent
data run into a .csv file. The whole system is controlled by a set of params
stored in Faraday.toml, read using fconfig.py and presented to the user 
with configurator.py.
