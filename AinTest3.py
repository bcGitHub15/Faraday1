# -*- coding: utf-8 -*-
"""
AinTest3
Continuous analog input from nidaq test3.
Test1 verified input using the internal clock up to 1 msps. I am sticking
to 10ksps for now.
Test 2 extended to 3 channels, AIN0, AIN1, and AIN2
Test3 tries for reasonably continuous data taking and plotting. It is
aiming for pseudo-real time plotting and is not concerned with perfect
alignment of one read with the next

Created on Tue Jan 31 13:24:18 2023

@author: BCollett
"""
from PyQt5.QtWidgets import QApplication
import sys
from appdlg import AppDLG
import traceback

if __name__ == "__main__":

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        print(f'Using {app}')

    try:
        mainWin = AppDLG()
        print('Main window complete')
        mainWin.resize(300, 800)
        mainWin.move(100, 100)
        print('Main window resized')
        mainWin.show()
        print('Main window shown')
        sys.exit(app.exec_())
        app.exec_()
    except RuntimeError:
        print("".join(i for i in traceback.format_exc()))
        print('Quit with errors.')
