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
#
#
#   PyQt5 imports for the GUI
#
from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QFormLayout, QSpacerItem, QFileDialog)
from PyQt5.QtGui import QStaticText
from pyqtgraph import PlotWidget, plot, setConfigOption, ViewBox, mkPen
from pyqtgraph import GraphicsLayoutWidget, GraphicsLayout
#
#   Support imports
#
import iscan
from threeplotwidget import ThreePlotWidget

class RPlotter(QWidget):
    def __init__(self, pw: ThreePlotWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plotter = pw
        manLayout0 = QVBoxLayout()
        #
        #   Top lines have settings and control buttons
        #
        line1 = QHBoxLayout()
        rateLab = QLabel('Sample Rate (sps)')
        self.rate = QLineEdit('10000')
        line1.addWidget(rateLab)
        line1.addWidget(self.rate)

        line2 = QHBoxLayout()
        durLab = QLabel('Duration (s)')
        self.dur = QLineEdit('5.0')
        line2.addWidget(durLab)
        line2.addWidget(self.dur)
#        u2Lab = QLabel('Unused')
#        self.u2 = QLineEdit('0.2')
#        topLine.addWidget(u2Lab)
#        topLine.addWidget(self.u2)

        line3 = QHBoxLayout()
        self.strtBtn = QPushButton("START")
        self.strtBtn.clicked.connect(self.on_click_start)
#        self.pauseBtn = QPushButton("PAUSE")
#        self.pauseBtn.setEnabled(False)
#        self.pauseBtn.clicked.connect(self.on_click_pause)
        self.stopBtn = QPushButton("STOP")
        self.stopBtn.setEnabled(False)
        self.stopBtn.clicked.connect(self.on_click_stop)
#        secLine.addWidget(rateLab)
#        secLine.addWidget(self.rate)
        line3.addWidget(self.strtBtn)
#        secLine.addWidget(self.pauseBtn)
        line3.addWidget(self.stopBtn)
        #
        #   Next comes the live plot
        #
#        vb = ViewBox(border=mkPen('b'))
#        self.plotter = PlotWidget(viewBox=vb)
#        self.plotter = ThreePlotWidget(self)
#        self.plotter = ThreePlotWidget(parent_view=None)
        '''
        #
        #   The description and the save button
        #
        botLine = QHBoxLayout()
        self.desc = QLineEdit('')
        self.saveBtn = QPushButton("SAVE SCAN")
        self.saveBtn.setEnabled(False)
        botLine.addWidget(self.saveBtn)
        self.saveBtn.clicked.connect(self.on_click_save)
        botLine.addWidget(self.desc)
        botLine.addWidget(self.saveBtn)
        '''
        #
        #   Assemble
        #
        manLayout0.addLayout(line1)
        manLayout0.addLayout(line2)
        manLayout0.addLayout(line3)
        manLayout0.addStretch()
#        manLayout0.addLayout(topLine)
#        manLayout0.addWidget(self.plotter)
#        manLayout0.addLayout(botLine)
        self.setLayout(manLayout0)

    @pyqtSlot()
    def on_click_start(self):
        print('Start scan')
        self.plotter.clear()
        scan = iscan.IScan()
        scan.sendPlotsTo(self.plotter)

        self.strtBtn.setEnabled(False)
        self.pauseBtn.setEnabled(True)
        self.stopBtn.setEnabled(True)

        s_rate = int(self.rate.text())
#        self.plotter.p3.setXRange(0.0, 1.0)
#        self.plotter.p3.setYRange(-10.0, 10.0)
        self.stopScan = False
        scan.startScan(s_rate)
        itn = 0
        while True:
            scan.stepScan()
            QApplication.processEvents()
            if self.stopScan:
#            if itn > 10:
                break
            print(itn)
            itn += 1
        self.strtBtn.setEnabled(True)
        self.pauseBtn.setEnabled(False)
        self.stopBtn.setEnabled(False)

    @pyqtSlot()
    def on_click_pause(self):
        print('Pause scan')

    @pyqtSlot()
    def on_click_stop(self):
        print('Stop scan')
        self.stopScan = True

    @pyqtSlot()
    def on_click_save(self):
        print('Save scan')  
