#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IScan
An IScan is an interactive plot of data from the National Instruments
board.

NOTE that the scan inherently support three channels
of data, two voltages corresponding to photo inputs and
one to a modulation voltage and supplies in addition
the sum, difference, and difference ratio of the two
photo inputs. These are expected to be returned by
the voltage source in the rows
row 0 is voltage 0
row 1 is voltage 1
row 2 is the modulation voltage.

The big limitation of the interactive scan is the time needed to start
and stop a nidaqmx task, more than 17ms per occurrence. This ends up
limiting the useable maximum update rate to 20 samples per second regardless
of the underlying sample clock.

Moral is don't us iscan for high data rates.
NOTE there are commented out relics of several attempts to beat this
rate limitation, none markedly successful yet.

5/10/23 Extend IScan to support single scans so that the
rplotter always talks to a scan and the data are always
organized in a scan.
@author: bcollett
"""
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
import ttimer
import nipy


class IScan():
    plotNames = ['PD1 voltage (V)',
                 'PD2 voltage (V)',
                 'Modulation voltage (V)',
                 'PD1 - PD2 (V)',
                 'PD1 + PD2 (V)',
                 '(PD1-PD2)/(PD1+PD2)']
    nInstance = 0

    def __init__(self, src: VoltageSource):
        IScan.nInstance += 1
        self.instance = IScan.nInstance
        print(f'Create IScan {self.instance}')
        self.src = src
        self.plotter = None
        self.duration = 0.1      # Will be reset when built
        self.sample_rate = 100_000
        self.n_sample = int(self.sample_rate * self.duration)
        self.update = 1
        self.nAverage = 100
        # These control what gets plotted in each pane
        self.pane1 = 0
        self.pane2 = 1
        self.pane3 = 2
        self.v1 = np.zeros(self.n_sample)
        self.v2 = np.zeros(self.n_sample)
        self.vm = np.zeros(self.n_sample)
        self.v1mv2 = np.zeros(self.n_sample)
        self.v1pv2 = np.zeros(self.n_sample)
        self.div = np.zeros(self.n_sample)
        self.traces = (self.v1, self.v2, self.vm,
                       self.v1mv2, self.v1pv2, self.div)
        self.gvals = [1.0, 1.0, 0.0, 0.0, 0.0, 0.0]   # Starting averages
        self.gerrs = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]   # and std. devs.

    def sendPlotsTo(self, threep: ThreePlotWidget):
        print(f'send plots to {threep}')
        self.plotter = threep

    def setDuration(self, time: float) -> None:
        self.duration = time

    def setSampleRate(self, rate: int) -> None:
        self.sample_rate = rate
        self.src.setDataRate(rate)

    def setUpdateRate(self, rate: int) -> None:
        self.update_rate = time

    def setNAverage(self, nAvg: int) -> None:
        self.nAverage = nAvg
        print(f'In setNAverage nAvg = {self.nAverage}')

    def plotInPane1(self, idx: int):
        if idx > 5:
            raise RuntimeError(f'Plot index {idx} out of range 0-5.')
        print(f'Trace {idx} in pane 1')
        self.pane1 = idx
        self.plotter.g1.setLabel('left', IScan.plotNames[idx])

    def plotInPane2(self, idx: int):
        if idx > 5:
            raise RuntimeError(f'Plot index {idx} out of range 0-5.')
        print(f'Trace {idx} in pane 2')
        self.pane2 = idx
        self.plotter.g2.setLabel('left', IScan.plotNames[idx])

    def plotInPane3(self, idx: int):
        if idx > 5:
            raise RuntimeError(f'Plot index {idx} out of range 0-5.')
        print(f'Trace {idx} in pane 3')
        self.pane3 = idx
        self.plotter.g3.setLabel('left', IScan.plotNames[idx])

    def plotInPanes(self, indices):
        self.plotInPane1(indices[0])
        self.plotInPane2(indices[1])
        self.plotInPane3(indices[2])

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
    def startScan(self, update_rate: int):
        #
        #   Validate state and arguments.
        #   Note any previous data will be silently deleted.
        #
        self.update_rate = update_rate
        self.n_sample = int(self.duration * self.update_rate)
        print('nsamp', self.n_sample, self.duration, self.update_rate)
        self.data = np.zeros((3, self.n_sample), dtype=np.float64)
        self.data[2, 0] = 10
        self.data[2, 1] = -10
        self.times = np.linspace(0.0, self.duration, self.n_sample)
        print(self.n_sample, self.times[-10:])
        self.data[0, :] = np.sin(2*np.pi*self.times)
        self.data[1, :] = np.sin(3*np.pi*self.times)
        self.data[2, :] = 5*np.sin(4*np.pi*self.times)
#        print(self.times[:10])
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
        self.tick_rate = ttimer.init()
        self.scanIndex = 0
        self.v1 = np.zeros(self.n_sample)
        self.v2 = np.zeros(self.n_sample)
        self.vm = np.zeros(self.n_sample)
        self.v1mv2 = np.zeros(self.n_sample)
        self.v1pv2 = np.zeros(self.n_sample)
        self.div = np.zeros(self.n_sample)
        self.startTime = time.monotonic()
        self._ngap = 5  # Number of samples in gap between old and new data
        # self._glim = self.n_sample - self._ngap    # REMOVE?

        # self.rdTime = 0
        # self.calcTime = 0
        # self.plotTime = 0
        # self.cnt = 0
        # self.src.single_init()

    #
    #   Take and plot one more data point.
    #   Argument determines whether we maintain the running gap that makes
    #   it easier to watch in multi-scan mode.
    #
    # def stepScan(self, do_gap=True) -> bool:
    def stepScan(self, do_plot=True) -> bool:
        st = ttimer.now()
        graph_end = False
        #
        # Finally, we can actually run the scan.
        #
        #        self.data = self.src.readOne()
        t1 = time.monotonic()
        # nit1 = ttimer.now()
        # This line takes 60ms!!
        tdata = self.src.readAvg(self.nAverage)
        # tdata = self.src.single_read()
        # tdata = (0.0, 0.1, 3.4)
        # tdata = nipy.read(self.nAverage)
        # nit2 = ttimer.now()
        # print('iscan ', (nit2-nit1)/self.tick_rate)
        # self.data = self.src.readOne()
        # t2 = time.monotonic()
        i = self.scanIndex
        # ig = self.scanIndex + self._ngap
        self.times[i] = t1 - self.startTime
        self.v1[i] = tdata[0]
        self.v2[i] = tdata[1]
        self.vm[i] = tdata[2]
        self.v1mv2[i] = tdata[0]-tdata[1]
        self.v1pv2[i] = tdata[0]+tdata[1]
        self.div[i] = self.v1mv2[i]/self.v1pv2[i]
        self.traces = (self.v1, self.v2, self.vm,
                       self.v1mv2, self.v1pv2, self.div)

#            self.v1[ig] = self.gval1
#            self.v2[ig] = self.gval2
#            self.vm[ig] = self.gval3
        self.scanIndex += 1
        #
        #   Check for end of scan and process if found
        #
        if self.scanIndex >= self.n_sample:  # End of graph, reset
            # print(self.times)
            # print('')
            graph_end = True
            #
            #   Compute ranges of visible traces and use to set
            #   graph limits
            #
            mx1 = np.max(self.traces[self.pane1])
            mn1 = np.min(self.traces[self.pane1])
            r1 = 0.55*(mx1-mn1)
            a1 = 0.5*(mx1+mn1)
            self.plotter.g1.setYRange(a1-r1, a1+r1)
            mx2 = np.max(self.traces[self.pane2])
            mn2 = np.min(self.traces[self.pane2])
            r2 = 0.55*(mx2-mn2)
            a2 = 0.5*(mx2+mn2)
            self.plotter.g2.setYRange(a2-r2, a2+r2)
            mx3 = np.max(self.traces[self.pane3])
            mn3 = np.min(self.traces[self.pane3])
            r3 = 0.55*(mx3-mn3)
            a3 = 0.5*(mx3+mn3)
            self.plotter.g3.setYRange(a3-r3, a3+r3)
            # Save averages and std. devs.
            for i in range(6):
                self.gvals[i] = np.average(self.traces[i])
                self.gerrs[i] = np.std(self.traces[i])
#            self.gvals[1] = np.average(self.v2[:-5])
            self.scanIndex = 0
            self.startTime = time.monotonic()
        #
        #   Update plots
        #
        if do_plot:
            # print('Update live plot')
            t1c = self.traces[self.pane1].copy()
            t2c = self.traces[self.pane2].copy()
            t3c = self.traces[self.pane3].copy()
            if self.scanIndex > 0:
                t1c[self.scanIndex:self.scanIndex+self._ngap] = self.gvals[self.pane1]
                t2c[self.scanIndex:self.scanIndex+self._ngap] = self.gvals[self.pane2]
                t3c[self.scanIndex:self.scanIndex+self._ngap] = self.gvals[self.pane3]
            if self.plotter:
                self.line1.setData(self.times, t1c)
                self.line2.setData(self.times, t2c)
                self.line3.setData(self.times, t3c)
            # print('Update done')
        # t4 = time.monotonic()
        # self.rdTime += t2 - t1
        # self.calcTime += t3 - t2
        # self.plotTime += t4 - t3
        # self.cnt += 1
        #print((ttimer.now() - st)/self.tick_rate)
        return graph_end
    
    def stopScan(self):
        # self.src.single_close()
        pass
    
    #
    #   A monolithic scan.
    #   NOTE that this may take time so we show a please
    #   wait box.
    #
    def singleScan(self, duration, rate):
        self.setSampleRate(rate)
        self.duration = duration
        print(f'Single sample duration {duration}')
        print(f'Single sample rate set to {rate}')
        npoint = int(duration * rate)
        print(f'Single collect {npoint} points')
        d = self.src.readN(npoint, tmax=duration+1)
        self.times = np.linspace(0, duration, npoint)
        self.v1 = d[0, :]
        self.v2 = d[1, :]
        self.vm = d[2, :]
        self.v1mv2 = self.v1 - self.v2
        self.v1pv2 = self.v1 + self.v2
        self.div = self.v1mv2/self.v1pv2
        self.traces = (self.v1, self.v2, self.vm,
                       self.v1mv2, self.v1pv2, self.div)
        #
        #   Get scaling
        #
        mx1 = np.max(self.traces[self.pane1])
        mn1 = np.min(self.traces[self.pane1])
        r1 = 0.55*(mx1-mn1)
        a1 = 0.5*(mx1+mn1)
        self.plotter.g1.setYRange(a1-r1, a1+r1)
        mx2 = np.max(self.traces[self.pane2])
        mn2 = np.min(self.traces[self.pane2])
        r2 = 0.55*(mx2-mn2)
        a2 = 0.5*(mx2+mn2)
        self.plotter.g2.setYRange(a2-r2, a2+r2)
        mx3 = np.max(self.traces[self.pane3])
        mn3 = np.min(self.traces[self.pane3])
        r3 = 0.55*(mx3-mn3)
        a3 = 0.5*(mx3+mn3)
        self.plotter.g3.setYRange(a3-r3, a3+r3)
        self.plotter.setXRangeLabel(0.0, duration, 'Time (s)')
        # Save averages and std. devs.
        for i in range(6):
            self.gvals[i] = np.average(self.traces[i])
            self.gerrs[i] = np.std(self.traces[i])
        #
        #   Plot with titles and styles
        #
        if self.plotter:
            self.plotter.g1.clear()
            self.plotter.g2.clear()
            self.plotter.g3.clear()
            print('Using 3-trace plotter')
            print(self.pane1, self.pane2, self.pane3)
            self.plotter.g1.plot(x=self.times,
                                 y=self.traces[self.pane1],
                                 name= IScan.plotNames[0], pen='b',
                                 symbol='o', symbolPen='b',
                                 symbolBrush='b',
                                 symbolSize=2, pxMode=True)
            self.plotter.g2.plot(x=self.times,
                                 y=self.traces[self.pane2],
                                 name= IScan.plotNames[1], pen='g',
                                 symbol='o', symbolPen='g',
                                 symbolBrush='g',
                                 symbolSize=2, pxMode=True)
            self.plotter.g3.plot(x=self.times,
                                 y=self.traces[self.pane3],
                                 name= IScan.plotNames[2], pen='r',
                                 symbol='o', symbolPen='r',
                                 symbolBrush='r',
                                 symbolSize=2, pxMode=True)

    def get_err(self, idx: int) -> float:
        return self.gerrs[idx]

    def get_avg(self, idx: int) -> float:
        # print(self.gvals[idx])
        return self.gvals[idx]

    def dump(self):
        pass
        # self.src.close()
        # print(f'Avg read {self.rdTime/self.cnt},'
        #       ' calc {self.calcTime/self.cnt},'
        #       ' plot {self.plotTime/self.cnt}')

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

    #
    #   Send data in text form to a .csv file
    #
    def saveTo(self, fname: str):
        darray = np.stack((self.times, self.v1, self.v2, self.vm,
                           self.v1mv2, self.v1pv2, self.div), axis=1)
        hdr = 't,V1,V2,Vm,V1-V2,V1+V2,Vdiv'
        np.savetxt(fname, darray, header=hdr, delimiter=', ')

    def close(self):
        print(f'Close iscan instance {self.instance}')
        self.instance = -1
        if self.src is not None:
            print('Close source')
            self.src.close()
        self.src = None

    #
    #   Helpers
    #
