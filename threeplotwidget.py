# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 15:39:43 2023

@author: pguest
"""
import numpy as np
#
#
#   PyQt5 imports for the GUI
#
from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QFormLayout, QMainWindow)
from PyQt5.QtGui import QStaticText
#
#   PyQtGraph imports
#
from pyqtgraph import PlotWidget, plot, setConfigOption, ViewBox, mkPen
from pyqtgraph import GraphicsLayoutWidget, GraphicsLayout

class ThreePlotWidget(QWidget):
    winCount = 0
    def __init__(self, parent_view=None, *args, **kwargs):
#        super().__init__(parent=parent_view, *args, **kwargs)
        super().__init__()
        self.resize(900, 800)
        layout0 = QVBoxLayout()
#        self.label = QLabel(f"Another Window {ThreePlotWidget.winCount}")
#        ThreePlotWidget.winCount += 1
#        layout0.addWidget(self.label)
        self.setLayout(layout0)
#        '''
        setConfigOption('background', 'w')
        setConfigOption('foreground', 'k')

        self.g1 = PlotWidget(parent=self)
        self.g2 = PlotWidget(parent=self)
        self.g3 = PlotWidget(parent=self)
        self.g1.showGrid(x=True, y=True)
        self.g2.showGrid(x=True, y=True)
        self.g3.showGrid(x=True, y=True)
#        self.g1.setLabel('bottom', 'Time (s)')
        self.g1.setLabel('left', 'Photo 1 (V)')
#        self.g2.setLabel('bottom', 'Time (s)')
        self.g2.setLabel('left', 'Photo 2 (V)')
        self.g3.setLabel('bottom', 'Time (s)')
        self.g3.setLabel('left', 'B Field (V)')
        layout0.addWidget(self.g1)
        layout0.addWidget(self.g2)
        layout0.addWidget(self.g3)
        self.setLayout(layout0)
        y = np.sin(np.linspace(0, 4*np.pi, 1000))
        self.p1 = self.g1.plot(y=y)
        self.p2 = self.g2.plot(y=y)
        self.p3 = self.g3.plot(y=y)
#        '''
#        print(f'Created {self}')

    def clear(self):
        print('Clear sub plts')
        '''
        self.p1.clear()
        self.p2.clear()
        self.p3.clear()
        '''
        