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

Modified 5/10/23 Move basic Fourier buttons up into main section 
and make new single-shot section that does NOT do live scans. Instead
it takes all the data before displaying any. The benefit is that it
can run at MUCH higher data rates.
Re-arrange the controls so that the section that selects which plots
to display comes first, then an interactive section, then a single-shot
section.
"""
import numpy as np
import time
from datetime import datetime
#
#
#   PyQt5 imports for the GUI
#
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QGroupBox,
                             QPushButton, QVBoxLayout, QWidget)
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
import ttimer


# class RPlotter(QWidget, WindowController):
class RPlotter(QWidget):
    def __init__(self, cfg: FConfig, *args, **kwargs):
        # Build our basic structure
        super().__init__(*args, **kwargs)
        self.cfg = cfg
        self.plotter = threeplotwidget.ThreePlotWidget()
        self.plotter.resize(cfg.graphs_get('GraphWidth'),
                            cfg.graphs_get('GraphHeight'))
#        WindowController(self).__init__(self.plotter)
        self.showPlot = False
        self.scan = None
        self.src = self._find_source(cfg)
        print(f'Create scan with source {self.src}')
        self.scan = iscan.IScan(self.src)
        #
        #   Lay controls out in the window
        #
        manLayout0 = QVBoxLayout()
        #
        # First select which traces to plot
        #
        box1 = QGroupBox('Select traces to plot')
        l1 = QVBoxLayout()
        box1.setLayout(l1)
        traceNames = ('V1', 'V2', 'Vm', 'V1 - V2',
                      'v1 + v2', 'V1 - V2/v1 + v2')
        self.trace1 = bcwidgets.NamedComboDisp('Plot 1 shows', traceNames)
        self.trace1.box.setCurrentIndex(0)
        l1.addLayout(self.trace1.layout)
        self.trace2 = bcwidgets.NamedComboDisp('Plot 2 shows', traceNames)
        self.trace2.box.setCurrentIndex(1)
        l1.addLayout(self.trace2.layout)
        self.trace3 = bcwidgets.NamedComboDisp('Plot 3 shows', traceNames)
        self.trace3.box.setCurrentIndex(2)
        l1.addLayout(self.trace3.layout)
        manLayout0.addWidget(box1)
        #
        #   Then start a section for the interactive grapher.
        #
        box2 = QGroupBox('Interactive plotting')
        l2 = QVBoxLayout()
        box2.setLayout(l2)
        #
        #   Top lines have settings and control buttons
        #
        oldSRate = cfg.inputs_get('SampleRate')
        self.srate = bcwidgets.NamedIntEdit('Sample Rate (sps)', oldSRate)
        l2.addLayout(self.srate.layout)
        #
        oldDur = cfg.inputs_get('LiveDuration')
        self.dur = bcwidgets.NamedFloatEdit('Duration (s)', oldDur)
        l2.addLayout(self.dur.layout)
        #
        oldURate = cfg.graphs_get('UpdateRate')
        self.urate = bcwidgets.NamedIntEdit('Data update Rate (sps)',
                                            oldURate)
        l2.addLayout(self.urate.layout)
        #
        oldNAvg = 30
        self.navg = bcwidgets.NamedIntEdit('Number of samples'
                                           ' to average per point',
                                           oldNAvg)
        l2.addLayout(self.navg.layout)
        #
        # Next line is for four buttons
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
        # FOURIER
        self.showBtn = QPushButton("Show Fourier")
        self.showBtn.setEnabled(False)
        self.showBtn.clicked.connect(self.on_click_show)
        line3.addWidget(self.showBtn)
        # SAVE
        self.saveBtn = QPushButton("Save Data")
        self.saveBtn.setEnabled(False)
        self.saveBtn.clicked.connect(self.on_click_save)
        line3.addWidget(self.saveBtn)
        l2.addLayout(line3)
        manLayout0.addWidget(box2)
        #
        #   Start a Single-Shot section
        #
        box3 = QGroupBox('Single-shot plotting')
        l3 = QVBoxLayout()
        box3.setLayout(l3)
        #
        #   Only duration and sample rate settings
        #
        oldFSRate = cfg.inputs_get('SampleRate')
        self.fsrate = bcwidgets.NamedIntEdit('Sample Rate (sps)', oldFSRate)
        l3.addLayout(self.fsrate.layout)
        #
        oldFDur = cfg.inputs_get('LiveDuration')
        self.fdur = bcwidgets.NamedFloatEdit('Duration (s)', oldFDur)
        l3.addLayout(self.fdur.layout)
        #
        # Next line is for four buttons
        #
        line3 = QHBoxLayout()
        # START
        self.fstrtBtn = QPushButton("RUN")
        self.fstrtBtn.clicked.connect(self.on_click_fstart)
        line3.addWidget(self.fstrtBtn)
        # FOURIER
        self.fshowBtn = QPushButton("Show Fourier")
        self.fshowBtn.setEnabled(False)
        self.fshowBtn.clicked.connect(self.on_click_fshow)
        line3.addWidget(self.fshowBtn)
        # SAVE
        self.fsaveBtn = QPushButton("Save Data")
        self.fsaveBtn.setEnabled(False)
        self.fsaveBtn.clicked.connect(self.on_click_fsave)
        line3.addWidget(self.fsaveBtn)
        l3.addLayout(line3)
        manLayout0.addWidget(box3)
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
        self.showBtn.setEnabled(True)

    @pyqtSlot()
    def on_click_close(self):
        print('Close plotter')
        self.plotter.hide()

    @pyqtSlot()
    def on_click_show(self):
        print('Show Fourier')
        self._do_fourier()

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
        self._do_single()
        self.fsaveBtn.setEnabled(True)
        self.fshowBtn.setEnabled(True)

    @pyqtSlot()
    def on_click_fshow(self):
        print('Show Fourier in Fourier')
        self._do_fourier()

    @pyqtSlot()
    def on_click_fsave(self):
        print('Save Fourier pressed')
        base_name = self._unique_file_name()
        fname = base_name + "Four.csv"
        print(f'Save Fourier to {fname}')
        darray = np.stack((self.freq, self.fv1, self.fv2, self.fvm,
                           self.fv1mv2, self.fv1pv2, self.fdiv), axis=1)
        hdr = 'freq,V1,V2,Vm,V1-V2,V1+V2,Vdiv'
        np.savetxt(fname, darray, header=hdr, delimiter=', ')
        self.scan.saveTo(base_name + '.csv')

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
    # _do_fourier transforms all data and updates displayed traces.
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
        fmax = 0.5/(self.scan.times[1] - self.scan.times[0])
        print('Fourier', len(self.scan.v1), len(self.fv1), fmax)
        self.freq = np.linspace(0, fmax, len(self.fv1))
        self.plotter.g1.clear()
        self.plotter.g3.setLabel('bottom', 'Frequency (Hz)')
        self.plotter.g1.enableAutoRange()
        self.plotter.g1.plot(x=self.freq, 
                             y=np.log10(ftraces[self.plots[0]]),
                             name= iscan.IScan.plotNames[0], pen='b',
                             symbol='o', symbolPen='b',
                             symbolBrush='b',
                             symbolSize=2, pxMode=True)
        self.plotter.g2.clear()
        self.plotter.g2.enableAutoRange()
        self.plotter.g2.plot(self.freq, np.log10(ftraces[self.plots[1]]),
                             name= iscan.IScan.plotNames[0], pen='g',
                             symbol='o', symbolPen='g',
                             symbolBrush='b',
                             symbolSize=2, pxMode=True)
        self.plotter.g3.clear()
        self.plotter.g3.enableAutoRange()
        self.plotter.g3.plot(self.freq, np.log10(ftraces[self.plots[2]]),
                             name= iscan.IScan.plotNames[0], pen='b',
                             symbol='o', symbolPen='r',
                             symbolBrush='r',
                             symbolSize=2, pxMode=True)
    #
    # _do_scan actually takes the data and maintains the plots.
    # It takes one argument that determines whether the scan runs
    # continuously or stops after one iteration.
    #
    def _do_scan(self, multi=True):
        # Get params from controls and send to scan
        self.scan.setDuration(self.dur.value())
        print(f'Orig sample rate {self.scan.sample_rate}')
        self.scan.setSampleRate(self.srate.value())
        print(f'Sample rate set to {self.scan.sample_rate}')
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
        #raw_step_times = np.linspace(0, self.dur.value(), n_point)
        tick_rate = ttimer.init()
        raw_step_times = np.linspace(0, self.dur.value()*tick_rate, n_point,dtype=int)
        n_plot = self.cfg.graphs_get('UpdateRate')
        t_plot = 1.0 / n_plot
        print(f't_plot = {t_plot}')
        print(raw_step_times[:5])
        print(raw_step_times[-5:])
        step_idx = 0
        running = True
        #
        # Actual Scan starts here
        #
        while running:
            #t0 = get_time()
            t0 = ttimer.now()
            step_times = raw_step_times + t0
            pt = t0
            # Do One Scan
            for step_idx in range(n_point):
                while True:
                    # ct = get_time()
                    ct = ttimer.now()
                    if ct >= step_times[step_idx]:
                        break
                # print(ct)
                if ct > pt:
                    pt = pt + t_plot
                    self.scan.stepScan(True)
                else:
                    self.scan.stepScan(False)
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
        #
        #   Scan ends here.
        #
        self.scan.stopScan()
        # execTime = (get_time() - start_time) / time_1s
        # print(f'Left scan loop. {itn} steps took {execTime} s')
        # print(f'scan avg = {s_sums/itn}  process avg = {p_sums/itn}')
        self.scan.dump()

    #
    #   Run a fast single scan. This is MUCH simpler.
    #
    def _do_single(self) -> None:
        # Clean plotter and connect to scan
        self.plotter.clear()
        self.scan.sendPlotsTo(self.plotter)
        self.plots = [self.trace1.value(), self.trace2.value(),
                 self.trace3.value()]
        print(f'plots = {self.plots}')
        self.scan.plotInPanes(self.plots)
        self.plotter.show()
        QApplication.processEvents()
        # Get params from controls
        dur = self.fdur.value()
        print(f'Single sample duration {dur}')
        rate = self.fsrate.value()
        print(f'Single sample rate set to {rate}')
        self.scan.singleScan(dur, rate)
        # Update statistics
        idx = self.trace1.value()
        self.trace1.show(self.scan.get_avg(idx), self.scan.get_err(idx))
        idx = self.trace2.value()
        self.trace2.show(self.scan.get_avg(idx), self.scan.get_err(idx))
        idx = self.trace3.value()
        self.trace3.show(self.scan.get_avg(idx), self.scan.get_err(idx))


