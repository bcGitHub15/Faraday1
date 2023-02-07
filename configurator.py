#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
configurator.py
Faraday

Builds representation of the configuration file and manages changes
to the configuration.

Created on 2/4/2023

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
        QVBoxLayout, QWidget, QFormLayout, QSpacerItem)
from PyQt5.QtGui import QStaticText
#
#   nidaq import for device probing
#
import nidaqmx.system
#
#   Import our configuration
#
from fconfig import FConfig


class Configurator(QWidget):
    def __init__(self, cfg: FConfig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #
        # System parameters
        #
        sysPanel = QGroupBox('Faraday system parameters')
        sysLayout = QFormLayout()
        self.mxText = QLineEdit(str(cfg.get('MainXPos')))
        sysLayout.addRow('Main window left position', self.mxText)
        self.myText = QLineEdit(str(cfg.get('MainYPos')))
        sysLayout.addRow('Main window top position', self.myText)
        self.mwText = QLineEdit(str(cfg.get('MainWidth')))
        sysLayout.addRow('Main window width', self.mwText)
        self.mhText = QLineEdit(str(cfg.get('MainHeight')))
        sysLayout.addRow('Main window height', self.mhText)
        sysPanel.setLayout(sysLayout)
        #
        # Input parameters
        # First build description of DAQ system
        #
        daqsys = nidaqmx.system.System.local()
        self.devList = []
        self.chanList = ['ai0', 'ai1', 'ai2', 'ai3', 
                         'ai4', 'ai5', 'ai6', 'ai7']
        for dev in daqsys.devices:
            self.devList.append(dev)
        # Then the panel
        inputPanel = QGroupBox('Input parameters')
        inputLayout = QFormLayout()
        # Device
        self.inDev = QComboBox()
        i = 0
        for d in self.devList:
            self.inDev.insertItem(i, f"{d.name} {d.product_type}")
            i += 1
        self.inDev.setCurrentIndex(0)
        inputLayout.addRow('Input device', self.inDev)
        # Voltage 1 input
        self.inV1 = QComboBox()
        for d in self.chanList:
            self.inV1.insertItem(i, d)
        self.inV1.setCurrentIndex(self.chanList.index(cfg.inputs_get('V1Chan')))
        inputLayout.addRow('PD1 voltage channel', self.inV1)
        self.srate = QLineEdit(str(cfg.inputs_get('SampleRate')))
        # Voltage 2 input
        self.inV2 = QComboBox()
        for d in self.chanList:
            self.inV2.insertItem(i, d)
        self.inV2.setCurrentIndex(self.chanList.index(cfg.inputs_get('V2Chan')))
        inputLayout.addRow('PD2 voltage channel', self.inV2)
        self.srate = QLineEdit(str(cfg.inputs_get('SampleRate')))
        # Modulation voltage input
        self.inVm = QComboBox()
        for d in self.chanList:
            self.inVm.insertItem(i, d)
        self.inVm.setCurrentIndex(self.chanList.index(cfg.inputs_get('VMChan')))
        inputLayout.addRow('Modulation voltage channel', self.inVm)
        # Params
        self.srate = QLineEdit(str(cfg.inputs_get('SampleRate')))
        inputLayout.addRow('Raw sample rate (sps)', self.srate)
        self.dur = QLineEdit(str(cfg.inputs_get('LiveDuration')))
        inputLayout.addRow('Live duration (s)', self.dur)
        inputPanel.setLayout(inputLayout)
        #
        # Output parameters
        #
        outputPanel = QGroupBox('Output parameters')
        outputLayout = QFormLayout()
        # Device
        self.outDev = QComboBox()
        i = 0
        for d in self.devList:
            self.outDev.insertItem(i, f"{d.name} {d.product_type}")
            i += 1
        self.outDev.setCurrentIndex(0)
        outputLayout.addRow('Output device', self.outDev)
        outputPanel.setLayout(outputLayout)
        #
        # Graph parameters
        #
        graphPanel = QGroupBox('Graphing parameters')
        graphLayout = QFormLayout()
        self.gwText = QLineEdit(str(cfg.get('GraphWidth')))
        graphLayout.addRow('Graph window width', self.gwText)
        self.ghText = QLineEdit(str(cfg.get('GraphHeight')))
        graphLayout.addRow('Graph window height', self.ghText)
        self.urate = QLineEdit(str(cfg.graphs_get('UpdateRate')))
        graphLayout.addRow('Graph update rate (sps)', self.urate)
        graphPanel.setLayout(graphLayout)
        #
        #   Buttons
        #
        okBtn = QPushButton("OK")
        okBtn.clicked.connect(lambda: self.on_click(True))
        cancelBtn = QPushButton("CANCEL")
        cancelBtn.clicked.connect(lambda: self.on_click(False))
        btnLayout = QHBoxLayout()
        btnLayout.addWidget(cancelBtn)
        btnLayout.addWidget(okBtn)
        #
        # Build whole system
        #
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(sysPanel)
        leftLayout.addWidget(inputPanel)
        leftLayout.addWidget(outputPanel)
        leftLayout.addWidget(graphPanel)
        vSpace = QSpacerItem(20, 40, QSizePolicy.Minimum,
                                     QSizePolicy.Expanding)
        leftLayout.addItem(vSpace)
        configLayout = QHBoxLayout()
        configLayout.addLayout(leftLayout)
        configLayout.addLayout(btnLayout)
        self.setLayout(configLayout)

    @pyqtSlot()
    def on_click(self, proceed: bool):
        print(f"Close config, accept = {proceed}.")
