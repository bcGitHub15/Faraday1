# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 15:39:43 2023

@author: pguest
"""
import numpy as np
from pyqtgraph import PlotWidget, plot, setConfigOption, ViewBox, mkPen
from pyqtgraph import GraphicsLayoutWidget, GraphicsLayout

class ThreePlotWidget(GraphicsLayoutWidget):
    def __init__(self, parent_view=None, *args, **kwargs):
        super().__init__(parent=parent_view, *args, **kwargs)
        print(super())
        self.p1 = GraphicsLayout.addPlot(self, row=0, col=0, title='V1')
        y = np.sin(np.linspace(0, 4*np.pi, 1000))
        self.p1.plot(y=y)
        print(f'Created {self.p1}')
        self.p2 = GraphicsLayout.addPlot(self, row=1, col=0, title='V2')
        self.p3 = GraphicsLayout.addPlot(self, row=2, col=0, title='VIN')
        self.p1.showGrid(x=True, y=True)
        self.p2.showGrid(x=True, y=True)
        self.p3.showGrid(x=True, y=True)
#        self.plotter.setLabel('bottom', 'Time (s)')
#        self.plotter.setLabel('left', 'Voltage (V)')
#        self.plotter.setTitle('Live Scan')

    def clear(self):
        print('Clear sub plts')
        self.p1.clear()
        self.p2.clear()
        self.p3.clear()
