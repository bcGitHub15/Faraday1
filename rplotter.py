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
"""
import numpy as np
import time
#
#
#   PyQt5 imports for the GUI
#
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QFormLayout, QSpacerItem, QFileDialog)
# from pyqtgraph import PlotWidget, plot, setConfigOption, ViewBox, mkPen
# from pyqtgraph import GraphicsLayoutWidget, GraphicsLayout
#
#   Support imports
#
import iscan
import threeplotwidget
from voltagesource import VoltageSource
from faradaysource import FaradaySource
from nidaqmxsource import NidaqmxSource
import bcwidgets
from fconfig import FConfig
from windowcontroller import WindowController


#class RPlotter(QWidget, WindowController):
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
        oldDur =  cfg.inputs_get('LiveDuration')
        self.dur = bcwidgets.NamedFloatEdit('Duration (s)', oldDur)
        manLayout0.addLayout(self.dur.layout)
        #
        oldURate = cfg.graphs_get('UpdateRate')
        self.urate = bcwidgets.NamedIntEdit('Graph update Rate (sps)',
                                            oldURate)
        manLayout0.addLayout(self.urate.layout)
        #
        oldNAvg = 100
        self.navg = bcwidgets.NamedIntEdit('Number of samples to average per point',
                                            oldNAvg)
        manLayout0.addLayout(self.navg.layout)
        #
        # Select which traces to plot
        #
        traceNames = ('V1', 'V2', 'Vm', 'V1 - V2', 'v1 + v2', 'V1 - V2/v1 + v2')
        self.trace1 = bcwidgets.NamedCombo('Plot 1 shows', traceNames)
        self.trace1.box.setCurrentIndex(0)
        manLayout0.addLayout(self.trace1.layout)
        self.trace2 = bcwidgets.NamedCombo('Plot 2 shows', traceNames)
        self.trace2.box.setCurrentIndex(1)
        manLayout0.addLayout(self.trace2.layout)
        self.trace3 = bcwidgets.NamedCombo('Plot 3 shows', traceNames)
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
        # CLOSE
        '''
        self.closeBtn = QPushButton("Close Plot")
        self.closeBtn.setEnabled(False)
        self.closeBtn.clicked.connect(self.on_click_close)
        line3.addWidget(self.closeBtn)
        '''
        #
        #   Assemble
        #
        manLayout0.addLayout(line3)
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
        self.closeBtn.setEnabled(False)
        self.showPlot = False

    @pyqtSlot()
    def on_click_start(self):
        print('Start pressed')
        scan = iscan.IScan(self.src)
        # Get params from controls and send to scan
        scan.setDuration(self.dur.value())
        scan.setSampleRate(self.srate.value())
        scan.setNAverage(self.navg.value())
        # Clean plotter and connect to scan
        self.plotter.clear()
        scan.sendPlotsTo(self.plotter)
        plots = [self.trace1.value(), self.trace2.value(), 
                 self.trace3.value()]
        print(f'plots = {plots}')
        scan.plotInPanes(plots)
        self.plotter.show()

        self.strtBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)
#        self.closeBtn.setEnabled(True)

        u_rate = self.urate.value()
        step_dur = 0.93 / u_rate   # Tuned at 10/sec
        print(f'Step duration {step_dur}')
#        self.plotter.p3.setXRange(0.0, 1.0)
        self.plotter.g1.setYRange(0.0, 0.2)
        self.plotter.g2.setYRange(0.0, 0.2)
        self.plotter.g3.setYRange(-5.5, 5.5)
        self.stopScan = False
        scan.startScan(u_rate)
        itn = 0
        s_sums = 0
        p_sums = 0
#        get_time = time.monotonic_ns
#        time_1s = 1_000_000_000
        get_time = time.time
        time_1s = 1
        start_time = get_time()
        step_dur = time_1s / u_rate
        n_point = int(self.dur.value() * self.urate.value())
        print(self.dur.value(), self.urate.value(), n_point)
        raw_step_times = np.linspace(0, self.dur.value(), n_point)
        print(raw_step_times[:5])
        print(raw_step_times[-5:])
        step_idx = 0
        running = True
        while running:
            t0 = get_time()
            step_times = raw_step_times + t0
            for step_idx in range(n_point):
   #             t1 = get_time()
                while get_time() < step_times[step_idx]:
                    pass
                graph_end = scan.stepScan()
  #              t2 = get_time()
                QApplication.processEvents()
 #               t3 = get_time()
                if self.stopScan:
                    running = False
                    break
#                print(t2-t1, t3-t2, t3-t1)
                
        '''
        #
        # Time trackers
        #
        t_track = [0] * 10
        t_idx = 0
        while True:
            t1 = get_time()
            graph_end = scan.stepScan()
            t2 = get_time()
            QApplication.processEvents()
            t3 = get_time()
            s_sums += t2 - t1
            p_sums += t3 - t2
            if self.stopScan:
                print('Stop scan')
                break
#            print(itn)
            itn += 1
            tend = t1 + step_dur
            t0 = 0
            while True:
                tf = get_time()
                if tf >= tend:
                    break
#                if tf != t0:
#                    t_track[t_idx] = tf
#                    t0 = tf
#                    t_idx+=1
#                    if t_idx > 9:
#                        t_idx = 0
            tf = get_time()
#            if graph_end:
            print(t1, tend-t1, tf-t1, step_dur)
        '''
        '''
        for i in range(10):
            print(t_track[i])
        for i in range(9):
            print(t_track[i+1]-t_track[i])
        '''
        execTime = (get_time() - start_time) / time_1s
        print(f'Left scan loop. {itn} steps took {execTime} s')
        print(f'scan avg = {s_sums/itn}  process avg = {p_sums/itn}')
        scan.dump()
        '''
            scan.stepScan()
            QApplication.processEvents()
            if self.stopScan:
                print('Stop scan')
                break
#                        print(itn)
            itn += 1
        print('Left scan loop')
        '''
        self.scan = None

    @pyqtSlot()
    def on_click_stop(self):
        print('Stop scan')
        self.stopScan = True
        self.strtBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)

    @pyqtSlot()
    def on_click_close(self):
        print('Close plotter')
        self.plotter.hide()
#        self.closeBtn.setEnabled(False)

    @pyqtSlot()
    def on_click_save(self):
        print('Save scan')

#
#   Internal helpers
#
    def _find_source(self, cfg: FConfig) -> VoltageSource:
        rate = cfg.inputs_get('SampleRate')
        head = cfg.inputs_get('InDev')
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
#            return FaradaySource(ch_names, rate)
            return NidaqmxSource(full_names, rate)
        return VoltageSource(ch_names, rate)
