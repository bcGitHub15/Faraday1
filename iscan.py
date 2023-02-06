#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IScan
An IScan is an interactive plot of data from the National Instruments
board.

@author: bcollett
"""
import numpy as np
# from datetime import datetime
#
#   PyQt5 imports for the GUI
#
# from PyQt5.QtWidgets import QApplication
# from pyqtgraph import PlotWidget, plot, setConfigOption
#
#   system imports
#
import numpy as np
import time
#
#   our imports
#
from voltagesource import VoltageSource
from threeplotwidget import ThreePlotWidget


class IScan():
    def __init__(self, src: VoltageSource):
        self.src = src
        self.plotter = None
        self.duration = 0.1      # Should be set from config

    def sendPlotsTo(self, threep: ThreePlotWidget):
        print(f'send plots to {threep}')
        self.plotter = threep

    def setDuration(self, time: float) -> None:
        self.duration = time

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
        self.n_sample = int(self.duration * self.sample_rate)
        self.data = np.zeros((3, self.n_sample), dtype=np.float64)
        self.data[2, 0] = 10
        self.data[2, 1] = -10
        self.times = np.linspace(0.0, self.duration, self.n_sample)
        print(self.n_sample, self.times)
        self.data[0, :] = np.sin(2*np.pi*self.times)
        self.data[1, :] = np.sin(3*np.pi*self.times)
        self.data[2, :] = 5*np.sin(4*np.pi*self.times)
        print(self.times[:10])
        # Build the plots
        if self.plotter:
            self.plotter.g1.clear()
            self.plotter.g2.clear()
            self.plotter.g3.clear()
            print('Using live plotter')
            self.line1 = self.plotter.g1.plot(x=self.times, y=self.data[0, :],
                                              name='V1', pen='b',
                                              symbol='o', symbolPen='b',
                                              symbolBrush='b',
                                              symbolSize=2, pxMode=True)
            self.line2 = self.plotter.g2.plot(self.times, self.data[1, :],
                                              name='V2', pen='g',
                                              symbol='o', symbolPen='g',
                                              symbolBrush='g',
                                              symbolSize=2, pxMode=True)
            self.line3 = self.plotter.g3.plot(self.times, self.data[2, :],
                                              name='Vin', pen='r',
                                              symbol='o', symbolPen='r',
                                              symbolBrush='r',
                                              symbolSize=2, pxMode=True)
        print('Start scan')
        self.scanIndex = 1
        self.v1 = np.zeros(self.n_sample)
        self.v2 = np.zeros(self.n_sample)
        self.vb = np.zeros(self.n_sample)
        self.startTime = time.monotonic()
        self._ngap = 10
        self._gap = np.zeros(self._ngap)
        self._glim = self.n_sample - self._ngap

    def stepScan(self):
        #
        # Finally, we can actually run the scan.
        #
        self.data = self.src.readOne()
        i = self.scanIndex
        ig = self.scanIndex + self._ngap
        self.v1[i] = self.data[0]
        self.v2[i] = self.data[1]
        self.vb[i] = self.data[2]
        if self.scanIndex < self._glim:
            self.v1[ig] = 0.0
            self.v2[ig] = 0.0
            self.vb[ig] = 0.0
        self.scanIndex += 1
        if self.scanIndex >= self.n_sample:
            self.scanIndex = 0
            self.v1[:self._ngap] = self._gap
            self.v2[:self._ngap] = self._gap
            self.vb[:self._ngap] = self._gap
        nread = 1
        '''
        self.data = self.src.readN(self.n_sample)
        nread = int(len(self.data)/3)
#        print(nread, self.data[2,:5])
        '''
        if nread > 0:
            if self.plotter:
                '''
                self.line1.setData(self.times, self.data[0, :])
                self.line2.setData(self.times, self.data[1, :])
                self.line3.setData(self.times, self.data[2, :])
                '''
                self.line1.setData(self.times, self.v1)
                self.line2.setData(self.times, self.v2)
                self.line3.setData(self.times, self.vb)
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

    def close(self):
        print('Close iscan')
        if self.src is not None:
            self.src.close()
        self.src = None
