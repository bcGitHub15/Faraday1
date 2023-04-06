#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rplotter.py
Faraday
This is tab for running an interactive graph of the voltages
from the machine
rplotter runs a rolling long-term view of the data and moves
the plotting to a separate Qt window from the tabbed control
interface.

Created on 1/31/2023
@author: bcollett

Modified 3/30/23 Add support for a Fourier data collection section.
4/6/23 Make Stop always complete a scan. Made rolling average mark
ONLY in graph, not in data.
Replace Fourier section with a Fourier button.
"""
import numpy as np
import time
from datetime import datetime
#
#
#   PyQt5 imports for the GUI
#
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QVBoxLayout, QWidget)
# from pyqtgraph import PlotWidget, plot, setConfigOption, ViewBox, mkPen
# from pyqtgraph import GraphicsLayoutWidget, GraphicsLayout
#
#   Support imports
#
import iscan
import threeplotwidget
from voltagesource import VoltageSource
from faradaysource import FaradaySource
import bcwidgets
from fconfig import FConfig
# from windowcontroller import WindowController


# class RPlotter(QWidget, WindowController):
class RPlotter(QWidget):
    def __init__(self, cfg: FConfig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cfg = cfg
        self.plotter = threeplotwidget.ThreePlotWidget()
        self.plotter.resize(cfg.graphs_get('GraphWidth'),
                            cfg.graphs_get('GraphHeight'))
#        WindowController(self).__init__(self.plotter)
        self.showPlot = False
        self.scan = None

        self.src = self._find_source(cfg)
        manLayout0 = QVBoxLayout()
        #
        #   Top lines have settings and control buttons
        #
        oldSRate = cfg.inputs_get('SampleRate')
        self.srate = bcwidgets.NamedIntEdit('Sample Rate (sps)', oldSRate)
        manLayout0.addLayout(self.srate.layout)
        #
        oldDur = cfg.inputs_get('LiveDuration')
        self.dur = bcwidgets.NamedFloatEdit('Duration (s)', oldDur)
        manLayout0.addLayout(self.dur.layout)
        #
        oldURate = cfg.graphs_get('UpdateRate')
        self.urate = bcwidgets.NamedIntEdit('Graph update Rate (sps)',
                                            oldURate)
        manLayout0.addLayout(self.urate.layout)
        #
        oldNAvg = 100
        self.navg = bcwidgets.NamedIntEdit('Number of samples'
                                           ' to average per point',
                                           oldNAvg)
        manLayout0.addLayout(self.navg.layout)
        #
        # Select which traces to plot
        #
        traceNames = ('V1', 'V2', 'Vm', 'V1 - V2',
                      'v1 + v2', 'V1 - V2/v1 + v2')
        self.trace1 = bcwidgets.NamedComboDisp('Plot 1 shows', traceNames)
        self.trace1.box.setCurrentIndex(0)
        manLayout0.addLayout(self.trace1.layout)
        self.trace2 = bcwidgets.NamedComboDisp('Plot 2 shows', traceNames)
        self.trace2.box.setCurrentIndex(1)
        manLayout0.addLayout(self.trace2.layout)
        self.trace3 = bcwidgets.NamedComboDisp('Plot 3 shows', traceNames)
        self.trace3.box.setCurrentIndex(2)
        manLayout0.addLayout(self.trace3.layout)
        #
        # Next line is for three buttons
        #
        line3 = QHBoxLayout()
        # START
        self.strtBtn = QPushButton("START")
        self.strtBtn.clicked.connect(self.on_click_start)
        line3.addWidget(self.strtBtn)
        # STOP
        self.stopBtn = QPushButton("STOP")
        self.stopBtn.setEnabled(False)
        self.stopBtn.clicked.connect(self.on_click_stop)
        line3.addWidget(self.stopBtn)
        # SAVE
        self.saveBtn = QPushButton("Save Data")
        self.saveBtn.setEnabled(False)
        self.saveBtn.clicked.connect(self.on_click_save)
        line3.addWidget(self.saveBtn)
        manLayout0.addLayout(line3)
        #
        #   Start a Fourier section
        #
        fsec = QLabel('Fourier Analyze Data')
        fsec.setFrameStyle(QFrame.Panel | QFrame.Raised)
        manLayout0.addWidget(fsec)
        '''
        #
        #   Top lines have settings and control buttons
        #
        oldfSRate = self.srate.value()
        self.fsrate = bcwidgets.NamedIntEdit('Fourier Sample Rate (sps)',
                                             oldfSRate)
        manLayout0.addLayout(self.fsrate.layout)
        #
        oldfDur = self.dur.value()
        self.fdur = bcwidgets.NamedFloatEdit('Data Duration (s)',
                                             oldfDur)
        manLayout0.addLayout(self.fdur.layout)
        '''
        #
        # Last line is for collect and save buttons
        #
        fline = QHBoxLayout()
        # START
        self.fstrtBtn = QPushButton("Analyze & Plot Fourier")
        self.fstrtBtn.clicked.connect(self.on_click_fstart)
        fline.addWidget(self.fstrtBtn)
        # SAVE
        self.fsaveBtn = QPushButton("Save Fourier Data")
        self.fsaveBtn.setEnabled(False)
        self.fsaveBtn.clicked.connect(self.on_click_fsave)
        fline.addWidget(self.fsaveBtn)
        manLayout0.addLayout(fline)
        #
        #
        #   Assemble
        #
        manLayout0.addStretch()
        self.setLayout(manLayout0)

    def close(self):
        print('Close rplotter')
        if self.plotter is not None:
            self.plotter.hide()
        self.plotter = None
        if self.scan is not None:
            self.scan.close()
        self.scan = None

    def closeEvent(self, event):
        print('rplotter closing')
        self.close()

    def childClosing(self):
        self.saveBtn.setEnabled(False)
        self.showPlot = False

    @pyqtSlot()
    def on_click_start(self):
        print('Start pressed')
        self._do_scan(True)
        
    @pyqtSlot()
    def on_click_stop(self):
        print('Stop scan')
        self.stopScan = True
        self.strtBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        self.saveBtn.setEnabled(True)
        self.fstrtBtn.setEnabled(True)

    @pyqtSlot()
    def on_click_close(self):
        print('Close plotter')
        self.plotter.hide()

    @pyqtSlot()
    def on_click_save(self):
        if self.scan is not None:
            fname = self._unique_file_name()
            fname = fname + ".csv"
            print(f'Save data to {fname}')
            self.scan.saveTo(fname)

    @pyqtSlot()
    def on_click_fstart(self):
        print('Collect Fourier pressed')
        self._do_fourier()
        # self._do_scan(False)
        self.fsaveBtn.setEnabled(True)
        # self.saveBtn.setEnabled(True)

    @pyqtSlot()
    def on_click_fsave(self):
        print('Save Fourier pressed')
        fname = self._unique_file_name() + "Four.csv"
        print(f'Save Fourier to {fname}')

#
#   Internal helpers
#
    def _find_source(self, cfg: FConfig) -> VoltageSource:
        print('rplotter')
        print(cfg._config)
        rate = cfg.inputs_get('SampleRate')
        head = cfg.inputs_get('InDev')
        print(head)
        print(f'len(head) = { len(head)}')
        ch_names = [cfg.inputs_get('V1Chan'),
                    cfg.inputs_get('V2Chan'),
                    cfg.inputs_get('VMChan')]
        full_names = ch_names
        for i in range(3):
            full_names[i] = head + '/' + ch_names[i]
        if len(head) < 1:
            return FaradaySource(ch_names, rate)
        print(full_names)
        if head.startswith('Dev'):
            # return FaradaySource(ch_names, rate)
            # Only import if needed!
            from nidaqmxsource import NidaqmxSource
            return NidaqmxSource(full_names, rate)
        return VoltageSource(ch_names, rate)

    def _unique_file_name(self) -> str:
        dstr = datetime.today().strftime('%m%d%y-%M%H')
        root = self.cfg.get('DataPrefix')
        return f'{root}{dstr}'

    #
    # _do_fourier does just what you think.
    #
    def _do_fourier(self):
        if self.scan is None:
            print('There are no current scan data.')
            return
        #
        # Work through the 6 data arrays
        #
        self.fv1 = np.absolute(np.fft.rfft(self.scan.v1))
        # print(self.fv1[:20])
        self.fv2 = np.absolute(np.fft.rfft(self.scan.v2))
        # print(self.fv2[:20])
        self.fvm = np.absolute(np.fft.rfft(self.scan.vm))
        # print(self.fvm[:20])
        self.fv1mv2 = np.absolute(np.fft.rfft(self.scan.v1mv2))
        # print(self.fv1mv2[:20])
        self.fv1pv2 = np.absolute(np.fft.rfft(self.scan.v1pv2))
        # print(self.fv1pv2[:20])
        self.fdiv = np.absolute(np.fft.rfft(self.scan.div))
        # print(self.fdiv[:20])
        ftraces = ( self.fv1, self.fv2, self.fvm, 
                    self.fv1mv2, self.fv1pv2, self.fdiv )
        # fmax = 1 + self.dur.value() * self.urate.value() * 0.5
        fmax = self.urate.value() * 0.5
        print(len(self.scan.v1), len(self.fv1), fmax)
        fbad = np.linspace(0, fmax, len(self.fv1))
        print(fbad[-1])
        self.plotter.g1.clear()
        self.plotter.g1.enableAutoRange()
        self.plotter.g1.plot(fbad, ftraces[self.plots[0]])
        self.plotter.g2.clear()
        self.plotter.g2.enableAutoRange()
        self.plotter.g2.plot(fbad, ftraces[self.plots[1]])
        self.plotter.g3.clear()
        self.plotter.g3.enableAutoRange()
        self.plotter.g3.plot(fbad, ftraces[self.plots[2]])
    #
    # _do_scan actually takes the data and maintains the plots.
    # It takes one argument that determines whether the scan runs
    # continuously or stops after one iteration.
    #
    def _do_scan(self, multi=True):
        self.scan = iscan.IScan(self.src)
        # Get params from controls and send to scan
        self.scan.setDuration(self.dur.value())
        self.scan.setSampleRate(self.srate.value())
        self.scan.setNAverage(self.navg.value())
        # Clean plotter and connect to scan
        self.plotter.clear()
        self.scan.sendPlotsTo(self.plotter)
        self.plots = [self.trace1.value(), self.trace2.value(),
                 self.trace3.value()]
        print(f'plots = {self.plots}')
        self.scan.plotInPanes(self.plots)
        self.plotter.show()

        self.strtBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)
        self.saveBtn.setEnabled(False)

        u_rate = self.urate.value()
        step_dur = 0.93 / u_rate   # Tuned at 10/sec
        print(f'Step duration {step_dur}')
#        self.plotter.p3.setXRange(0.0, 1.0)
        self.plotter.g1.setYRange(0.0, 0.2)
        self.plotter.g2.setYRange(0.0, 0.2)
        self.plotter.g3.setYRange(-5.5, 5.5)
        self.stopScan = False
        self.scan.startScan(u_rate)

        get_time = time.time
        time_1s = 1
#        start_time = get_time()
        step_dur = time_1s / u_rate
        n_point = int(self.dur.value() * self.urate.value())
        print(self.dur.value(), self.urate.value(), n_point)
        raw_step_times = np.linspace(0, self.dur.value(), n_point)
        # print(raw_step_times[:5])
        # print(raw_step_times[-5:])
        step_idx = 0
        running = True
        while running:
            t0 = get_time()
            step_times = raw_step_times + t0
            # Do One Scan
            for step_idx in range(n_point):
                while get_time() < step_times[step_idx]:
                    pass
#                graph_end = self.scan.stepScan()
                self.scan.stepScan(multi)
                QApplication.processEvents()
                '''
                if self.stopScan:
                    running = False
                    break
                '''
            # End of scan. Update and see if do more scans.
            idx = self.trace1.value()
            self.trace1.show(self.scan.get_avg(idx), self.scan.get_err(idx))
            idx = self.trace2.value()
            self.trace2.show(self.scan.get_avg(idx), self.scan.get_err(idx))
            idx = self.trace3.value()
            self.trace3.show(self.scan.get_avg(idx), self.scan.get_err(idx))
            if not multi or self.stopScan:
                break
        # execTime = (get_time() - start_time) / time_1s
        # print(f'Left scan loop. {itn} steps took {execTime} s')
        # print(f'scan avg = {s_sums/itn}  process avg = {p_sums/itn}')
        self.scan.dump()
