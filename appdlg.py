#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
g.py

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
        QVBoxLayout, QWidget, QFormLayout)
from PyQt5.QtGui import QStaticText
#
#   Mapper support imports
#
#import iplotter
import rplotter
from threeplotwidget import ThreePlotWidget


class AppDLG(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        print('Setup main Window')
        self.setWindowTitle("Faraday Plotter")
        self.originalPalette = QApplication.palette()
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        QApplication.setPalette(self.originalPalette)

        print('Build dialog')
        self.win = QTabWidget()
        self.win.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)


#        tab1 = iplotter.IPlotter()
        self.tab1 = rplotter.RPlotter()
        tab2 = QWidget()
        tab3 = QWidget()
#        tab7 = configurator.Configurator(bmap)
        print('Built all tabs')

        mainLayout = QVBoxLayout()
        print('Built main layout')
        mainLayout.addWidget(self.win)
        print('Added self to layout')
        self.setLayout(mainLayout)

        print('Built layout')
        self.win.addTab(self.tab1, "Live Plot")
        self.win.addTab(tab2, "Tab2")
        self.win.addTab(tab3, "Tab3")
#        self.win.addTab(tab7, "Configure")
        print('added all tabs')

    def closeEvent(self, evnt):
        print('Closing main dialog')
        super().closeEvent(evnt)
        self.tab1.close()
        QApplication.quit()