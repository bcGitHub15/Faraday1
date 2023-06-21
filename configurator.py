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
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import (QComboBox, QHBoxLayout, QLineEdit, QPushButton,
                             QVBoxLayout, QWidget, QFormLayout, QSpacerItem,
                             QGroupBox, QSizePolicy)
#
#   nidaq import for device probing is only loaded if expected
#
#
#   Import our configuration
#
from fconfig import FConfig


class Configurator(QWidget):
    def __init__(self, cfg: FConfig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cfg = cfg
        print('In configurator')
        print(self.cfg)
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
        # First build description of DAQ system if we have
        # a valid device name in the incoming cfg
        #
        self.devList = []
        self.chanList = ['ai0', 'ai1', 'ai2', 'ai3',
                         'ai4', 'ai5', 'ai6', 'ai7']
        if cfg.inputs_get('InDev').startswith('Dev'):
            import nidaqmx.system
            daqsys = nidaqmx.system.System.local()
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
        self.inV1.addItems(self.chanList)
        indx = self.chanList.index(cfg.inputs_get('V1Chan'))
        self.inV1.setCurrentIndex(indx)
        inputLayout.addRow('PD1 voltage channel', self.inV1)
        self.srate = QLineEdit(str(cfg.inputs_get('SampleRate')))
        # Voltage 2 input
        self.inV2 = QComboBox()
        self.inV2.addItems(self.chanList)
        indx = self.chanList.index(cfg.inputs_get('V2Chan'))
        self.inV2.setCurrentIndex(indx)
        inputLayout.addRow('PD2 voltage channel', self.inV2)
        self.srate = QLineEdit(str(cfg.inputs_get('SampleRate')))
        # Modulation voltage input
        self.inVm = QComboBox()
        self.inVm.addItems(self.chanList)
        indx = self.chanList.index(cfg.inputs_get('VMChan'))
        self.inVm.setCurrentIndex(indx)
        inputLayout.addRow('Modulation voltage channel', self.inVm)
        # Params
        self.srate = QLineEdit(str(cfg.inputs_get('SampleRate')))
        inputLayout.addRow('Raw sample rate (sps)', self.srate)
        self.dur = QLineEdit(str(cfg.inputs_get('LiveDuration')))
        inputLayout.addRow('Live duration (s)', self.dur)
        self.drate = QLineEdit(str(cfg.inputs_get('UpdateRate')))
        inputLayout.addRow('Data update rate (sps)', self.drate)
        
        self.xMin = QLineEdit(str(cfg.inputs_get('UpdateRate')))
        inputLayout.addRow('Data update rate (sps)', self.drate)
        
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
        self.gwText = QLineEdit(str(cfg.graphs_get('GraphWidth')))
        graphLayout.addRow('Graph window width', self.gwText)
        self.ghText = QLineEdit(str(cfg.graphs_get('GraphHeight')))
        graphLayout.addRow('Graph window height', self.ghText)
        self.urate = QLineEdit(str(cfg.graphs_get('UpdateRate')))
        graphLayout.addRow('Graph update rate (fps)', self.urate)
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
        configLayout = QVBoxLayout()
        configLayout.addWidget(sysPanel)
        configLayout.addWidget(inputPanel)
        configLayout.addWidget(outputPanel)
        configLayout.addWidget(graphPanel)
        configLayout.addLayout(btnLayout)
        vSpace = QSpacerItem(20, 40, QSizePolicy.Minimum,
                             QSizePolicy.Expanding)
        configLayout.addItem(vSpace)
        self.setLayout(configLayout)

    def update(self):
        # Work through all the fields and copy values into config
        self.cfg.set('MainXPos', int(self.mxText.text()))
        self.cfg.set('MainYPos', int(self.myText.text()))
        self.cfg.set('MainWidth', int(self.mwText.text()))
        self.cfg.set('MainHeight', int(self.mhText.text()))
        # Inputs
        self.cfg.inputs_set('InDev', 'testText')
#        print(self.cfg._config['inputs'])
        fullDev = self.inDev.currentText()
        devs = fullDev.split(' ')
#        print('InDev ', devs[0])
        self.cfg.inputs_set('InDev', devs[0])
#        print(self.cfg._config['inputs'])
#        print(self.cfg._config, self.cfg._config['inputs'])
        self.cfg.inputs_set('V1Chan', self.inV1.currentText())
        self.cfg.inputs_set('V2Chan', self.inV2.currentText())
        self.cfg.inputs_set('VMChan', self.inVm.currentText())
        self.cfg.inputs_set('SampleRate', int(self.srate.text()))
        self.cfg.inputs_set('LiveDuration', float(self.dur.text()))
        self.cfg.inputs_set('UpdateRate', float(self.drate.text()))
        # Outputs
        self.cfg.outputs_set('OutDev', self.outDev.currentText())
        # Graphing
        self.cfg.graphs_set('MainWidth', int(self.gwText.text()))
        self.cfg.graphs_set('MainHeight', int(self.ghText.text()))
        self.cfg.graphs_set('UpdateRate', int(self.urate.text()))

    @pyqtSlot()
    def on_click(self, proceed: bool):
        print(f"Close config, accept = {proceed}.")
        if proceed:
            self.update()
            print("Saving resulted in {}",self.cfg.saveOn('Faraday.toml'))
