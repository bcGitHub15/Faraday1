#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faraday.py

A Python application using PyQt5 providing an interface to
the Faraday rotation system in Gordon Jones' lab.

Created on 2/5/2023

@author: bcollett
"""
#
#   System imports
#
# import os
import sys
import traceback
#
#   PyQt5 imports
#
from PyQt5.QtWidgets import QApplication, QMainWindow
# from PyQt5.QtWidgets import QCoreApplication
# from PyQt5.QtWidgets import QMenu, QSizePolicy
# from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout
# from PyQt5.QtWidgets import QMessageBox
# from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit
# from PyQt5.QtWidgets import QLabel, QFileDialog
# from PyQt5.QtGui import QIcon
# from PyQt5.QtGui import QRegExpValidator
#
#   Faraday imports
#
from appdlg import AppDLG
from fconfig import FConfig


# ******************************************************************
#
#   Actual main applicaton. Delegates most of the work to CCDWidget.
#
# ******************************************************************
class FWin(QMainWindow):
    def __init__(self, c: FConfig):
        super().__init__()
        self.title = 'Faraday Probe'
        self.left = c.get('MainXPos')
        self.top = c.get('MainYPos')
        self.width = c.get('MainWidth')
        self.height = c.get('MainHeight')

        self.contents = AppDLG(c)

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.setCentralWidget(self.contents)

#        QCoreApplication.instance().aboutToQuit.connect(self.tidy_up)

        self.show()

    def tidy_up(self):
        print('Tidy up')
        self.contents.close()


#
# Run as application.
#
if __name__ == '__main__':
    gConfig = FConfig()
    gConfig.loadFrom('Faraday.toml')
    theApp = QApplication(sys.argv)
    mainWin = FWin(gConfig)
    try:
        sys.exit(theApp.exec_())
    except RuntimeError:
        print("".join(i for i in traceback.format_exc()))
        print('Quit with errors.')
    finally:
        mainWin.tidy_up()
