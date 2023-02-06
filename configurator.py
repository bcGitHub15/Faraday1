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


class Configurator(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #
        # Mapper parameters
        #
        mapperPanel = QGroupBox('Faraday parameters')
        mapperLayout = QFormLayout()
        self.portText = QLineEdit(bmap.config.mapper('port'))
        mapperLayout.addRow('Stepper controller port', self.portText)
        self.zmin = QLineEdit(str(bmap.config.mapper('zmin')))
        mapperLayout.addRow('Minimum real world Z', self.zmin)
        self.zmax = QLineEdit(str(bmap.config.mapper('zmax')))
        mapperLayout.addRow('Maximum real world Z', self.zmax)
        self.ymin = QLineEdit(str(bmap.config.mapper('ymin')))
        mapperLayout.addRow('Minimum real world Y', self.ymin)
        self.ymax = QLineEdit(str(bmap.config.mapper('ymax')))
        mapperLayout.addRow('Maximum real world Y', self.ymax)
        self.zorig = QLineEdit(str(bmap.config.mapper('zoriginsteps')))
        mapperLayout.addRow('Z origin (steps)', self.zorig)
        self.yorig = QLineEdit(str(bmap.config.mapper('yoriginsteps')))
        mapperLayout.addRow('Y origin (steps)', self.yorig)
        mapperPanel.setLayout(mapperLayout)
        #
        # Probe parameters
        #
        probePanel = QGroupBox('Field Probe parameters')
        probeLayout = QFormLayout()
        self.probe = QComboBox()
        self.probe.insertItem(0, "FluxGate on LabJackU6")
        self.probe.insertItem(1, "FluxGate on Keithley")
        self.probe.insertItem(2, "Sypris Hall Probe on GPIB")
        self.probe.setCurrentIndex(bmap.config.probe('index'))
        probeLayout.addRow('Field probe type', self.probe)
        self.srate = QLineEdit(str(bmap.config.probe('samplerate')))
        mapperLayout.addRow('Raw sample rate', self.srate)
        self.nsamp = QLineEdit(str(bmap.config.probe('nsample')))
        mapperLayout.addRow('Raw sample rate', self.nsamp)
        probePanel.setLayout(probeLayout)
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
        leftLayout.addWidget(mapperPanel)
        leftLayout.addWidget(probePanel)
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
