#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bcwidgets.py

Helper widgets that combine a single line edit with a label.
The base version accepts any string. The subclasses do extra checkinng to make
sure that the user can only type a valid value.

Created on 2/4/2023

@author: bcollett
"""
#
#
#   PyQt5 imports for the GUI
#
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QWidget)
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator


# ******************************************************************
#
#   Widget that combines a label and LineEdit.
#   Returns string values.
#
# ******************************************************************
class NamedEdit(QWidget):
    def __init__(self, name: str, istr: str):
        print(f'Init NamedEdit({name}, {istr})')
        self.label = QLabel(name)
        self.box = QLineEdit(istr)
        print(self.box)
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.box)

    def value(self) -> str:
        return self.box.text()
    
# ******************************************************************
#
#   Widget that combines a label and a read only LineEdit.
#   Returns string values.
#
# ******************************************************************
class NamedReadOnlyEdit(QWidget):
    def __init__(self, name: str):
        print(f'Init NamedEdit({name})')
        self.label = QLabel(name)
        self.box = QLineEdit("0.00")
        self.box.setReadOnly((True))
        print(self.box)
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.box)

    def value(self) -> str:
        return self.box.text()
    
    def show(self, val: float):
        dstr = f'{val:.5f}'
        self.box.setText(dstr)
        
    def showText(self, val: str):
        self.box.setText(val)


# ******************************************************************
#
#   Variant of NamedEdit that only accepts integers and knows
#   how to extract their values.
#
# ******************************************************************
class NamedIntEdit(NamedEdit):

    intValidExpr = QRegExp("[0-9]+")

    def __init__(self, name: str, ival: int):
        print(f'Init NamedIntEdit({name}, {ival})')
        super().__init__(name, str(int(ival)))
        print(self.box)
        self.box.setValidator(QRegExpValidator(self.intValidExpr, self.box))

    def value(self) -> int:
        return int(self.box.text())


# ******************************************************************
#
#   Variant of NamedEdit that only accepts floats and knows
#   how to extract their values.
#
# ******************************************************************
class NamedFloatEdit(NamedEdit):

    floatValidExpr = QRegExp("[0-9]+.?[0-9]{,2}")

    def __init__(self, name: str, ival: float):
        super().__init__(name, str(float(ival)))
        self.box.setValidator(QRegExpValidator(self.floatValidExpr, self.box))

    def value(self):
        return float(self.box.text())

# ******************************************************************
#
#   Widget that combines a comboBox and LineEdit.
#   Returns string values.
#
# ******************************************************************
class NamedCombo(QWidget):
    def __init__(self, name: str, namelist: list):
        print(f'Init NamedCombo({name}, {namelist})')
        self.label = QLabel(name)
        self.box = QComboBox()
        self.box.addItems(namelist)
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.box)

    def value(self) -> int:
        return self.box.currentIndex()

    def text(self) -> int:
        return self.box.currentText()

# ******************************************************************
#
#   Widget that combines a comboBox, a LineEdit, and a display
#   Returns string values.
#
# ******************************************************************
class NamedComboDisp(QWidget):
    def __init__(self, name: str, namelist: list):
        print(f'Init NamedCombo({name}, {namelist})')
        self.label = QLabel(name)
        self.box = QComboBox()
        self.box.addItems(namelist)
        self.disp = QLineEdit('0+/-0')
        self.disp.setReadOnly((True))
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.box)
        self.layout.addWidget(self.disp)

    def value(self) -> int:
        return self.box.currentIndex()

    def text(self) -> int:
        return self.box.currentText()

    def show(self, val: float, err: float):
        dstr = f'{val:.5f}+/-{err:.5f}'
        self.disp.setText(dstr)