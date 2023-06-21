# -*- coding: utf-8 -*-
"""
windowcontroller.py
Faraday

This is a mix-in class for dialogs that control other windows.
It exists to avoid a circular import between RPlotter and
ThreePlotWidget.

Created on Wed Feb  8 10:34:59 2023

@author: bcollett
"""
from PyQt5.QtWidgets import QWidget

class WindowController:
    def __init__(self, ch: QWidget):
        self.child = ch
        if ch is None:
            self.childOpen = False
        else:
            self.childOpen = True
        
    def installChild(self, newChild: QWidget):
        self.child = newChild
    
    def childClosing(self):
        self.childOpen = False
