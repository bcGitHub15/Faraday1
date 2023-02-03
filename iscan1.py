#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IScan
An IScan is an interactive plot of data from the National Instruments
board.

@author: bcollett
"""
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
#
#   PyQt5 imports for the GUI
#
from PyQt5.QtWidgets import QApplication
from pyqtgraph import PlotWidget, plot, setConfigOption
#
#   NI imports
#
import nidaqmx as ni
from nidaqmx.constants import Edge
#from nidaqmx.stream_readers import AnalogSingleChannelReader
from nidaqmx.stream_readers import AnalogMultiChannelReader
import numpy as np
#
#   our imports
#
from threeplotwidget import ThreePlotWidget

class IScan():
    def __init__(self):
        self.board = 'Dev1'    # Should be set from config file
        self.livePlotter = None
        self.duration = 1      # Should be set from config

    def sendPlotsTo(self, p: PlotWidget):
        print(f'send plots to {p}')
        self.livePlotter = p

    
#
    #   A scan broken up into steps for live use.
    #
    #
    #   Can specify scan by either number of points or dz between
    #   readings. If you specify both then the number of steps will
    #   override.
    #   NOTE that the number of steps is the number of times that the
    #   mapper moves. The complete scan will have n_step + 1 measurements.
    #
    def startScan(self, rate: int):
        #
        #   Validate state and arguments.
        #   Note any previous data will be silently deleted.
        #
        self.sample_rate = int(rate)
        self.n_sample = self.duration * self.sample_rate
        self.data = np.zeros((3, self.n_sample), dtype=np.float64)
        self.data[2,0]=10
        self.data[2,1] = -10
        self.times = np.linspace(0.0, 1.0, self.n_sample)
        self.data[0,:] = np.sin(2*np.pi*self.times)
        self.data[1,:] = np.sin(3*np.pi*self.times)
        self.data[2,:] = 5*np.sin(4*np.pi*self.times)
        print(self.times[:10])
        # Build the plots
        if self.livePlotter:
            print('Using live plotter')
            self.livePlotter.addLegend() # Must come BEFORE you plot the lines
            self.line1 = self.livePlotter.plot(x=self.times, y=self.data[0, :],
                                                name='V1', pen='b', 
                                                symbol='o', symbolPen='b', 
                                                symbolBrush='b',
                                                symbolSize=2, pxMode=True)
            self.line2 = self.livePlotter.plot(self.times, self.data[1, :], 
                                                name='V2', pen='g', 
                                                symbol='o', symbolPen='g',
                                                symbolBrush='g',
                                                symbolSize=2, pxMode=True)
            self.line3 = self.livePlotter.plot(self.times, self.data[2, :],
                                                name='Vin', pen='r', 
                                                symbol='o', symbolPen='r', 
                                                symbolBrush='r',
                                                symbolSize=2, pxMode=True)
        print('Start scan')
        
        # Build the ni reader
        self.task = ni.Task()
        # Add the input channels. Set all to high voltage for now.
        self.task.ai_channels.add_ai_voltage_chan("Dev2/ai0", 
                                          max_val=10.0, min_val=-10.0)
        self.task.ai_channels.add_ai_voltage_chan("Dev2/ai1", 
                                          max_val=10.0, min_val=-10.0)
        self.task.ai_channels.add_ai_voltage_chan("Dev2/ai2", 
                                          max_val=10.0, min_val=-10.0)
        # specify internal clocking at sample_rate
        self.task.timing.cfg_samp_clk_timing(self.sample_rate,
                                      active_edge=Edge.RISING,
                                      samps_per_chan=self.n_sample)
        self.reader = AnalogMultiChannelReader(self.task.in_stream)
        
    
    def stepScan(self):
        #
        # Finally, we can actually run the scan.
        #
        
        self.task.start()
        nread = self.reader.read_many_sample(self.data, 
                                number_of_samples_per_channel=self.n_sample,
                                timeout=2)
        self.task.stop()
        print(nread, self.data[2,:5])
        
        if nread > 0:
            print('+')
            if self.livePlotter:
                self.line1.setData(self.times, 100*self.data[0, :])
                self.line2.setData(self.times, 100*self.data[1, :])
                self.line3.setData(self.times, self.data[2, :])
        else:
            print('Data read failed!')
            raise RuntimeError('Data read failed!')

    #
    #   Plot as a set of four graphs
    #
    def plot(self):
        pass

    #
    #   Draw an individual sub-plot. Changes here will affect all four
    #   sub-plots identically
    #
    def _plotOn(self, axis, array, errors, name='B Field'):
        pass
