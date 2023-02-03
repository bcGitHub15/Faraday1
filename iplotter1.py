#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iplotter.py
Faraday
This is tab for running an interactive graph of the voltages
from the machine

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

class IPlotter(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        manLayout0 = QVBoxLayout()
        '''
        #
        #   Top lines have settings and control buttons
        #
        topLine = QHBoxLayout()
        rateLab = QLabel('Sample Rate')
        self.rate = QLineEdit('10000')
        u1Lab = QLabel('Unused')
        self.u1 = QLineEdit('5.0')
        u2Lab = QLabel('Unused')
        self.u2 = QLineEdit('0.2')
        topLine.addWidget(rateLab)
        topLine.addWidget(self.rate)
        topLine.addWidget(u1Lab)
        topLine.addWidget(self.u1)
        topLine.addWidget(u2Lab)
        topLine.addWidget(self.u2)
        '''
        secLine = QHBoxLayout()
        self.rate = QLineEdit('10000')
        rateLab = QLabel('Sample rate')
        self.strtBtn = QPushButton("START")
        self.strtBtn.clicked.connect(self.on_click_start)
        self.pauseBtn = QPushButton("PAUSE")
        self.pauseBtn.setEnabled(False)
        self.pauseBtn.clicked.connect(self.on_click_pause)
        self.stopBtn = QPushButton("STOP")
        self.stopBtn.setEnabled(False)
        self.stopBtn.clicked.connect(self.on_click_stop)
        secLine.addWidget(rateLab)
        secLine.addWidget(self.rate)
        secLine.addWidget(self.strtBtn)
        secLine.addWidget(self.pauseBtn)
        secLine.addWidget(self.stopBtn)
        #
        #   Next comes the live plot
        #
        setConfigOption('background', 'w')
        setConfigOption('foreground', 'k')
        vb = ViewBox(border=mkPen('b'))
        self.plotter = PlotWidget(viewBox=vb)
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
#        manLayout0.addLayout(topLine)
        manLayout0.addLayout(secLine)
        manLayout0.addWidget(self.plotter)
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
        self.plotter.setXRange(0.0, 1.0)
        self.plotter.setYRange(-10.0, 10.0)
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
