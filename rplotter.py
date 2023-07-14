#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rplotter.py
Faraday
This is tab for running an interactive graph of the voltages
from the machine
rplotter runs a rolling long-term view of the data and moves
the plotting to a separate Qt window from the tabbed control
interface.

Created on 1/31/2023
@author: bcollett

Modified 3/30/23 Add support for a Fourier data collection section.
4/6/23 Make Stop always complete a scan. Made rolling average mark
ONLY in graph, not in data.
Replace Fourier section with a Fourier button.

Modified 5/10/23 Move basic Fourier buttons up into main section 
and make new single-shot section that does NOT do live scans. Instead
it takes all the data before displaying any. The benefit is that it
can run at MUCH higher data rates.
Re-arrange the controls so that the section that selects which plots
to display comes first, then an interactive section, then a single-shot
section.
"""
import numpy as np
import time
from datetime import datetime
#
#
#   PyQt5 imports for the GUI
#
from PyQt5.QtCore import (pyqtSlot, Qt, QTimer, pyqtSignal, QThread)
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QGroupBox,
                             QPushButton, QVBoxLayout, QWidget, QCheckBox,
                             QProgressBar, QLabel)
from pyqtgraph import PlotWidget, plot, setConfigOption, ViewBox, mkPen

# from pyqtgraph import GraphicsLayoutWidget, GraphicsLayout
#
#   Support imports
#
import iscan
import threeplotwidget
from voltagesource import VoltageSource
from faradaysource import FaradaySource
import bcwidgets
from fconfig import FConfig
# from windowcontroller import WindowController
import ttimer

#
#   Diagnostic Imports for Noise fit
# 
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt



# class RPlotter(QWidget, WindowController):
# Class that controls the Faraday GUI and is where UI changes are performed
class RPlotter(QWidget):
    def __init__(self, cfg: FConfig, *args, **kwargs):
        # Build our basic structure
        super().__init__(*args, **kwargs)
        self.cfg = cfg
        self.plotter = threeplotwidget.ThreePlotWidget()
        self.plotter.resize(cfg.graphs_get('GraphWidth'),
                            cfg.graphs_get('GraphHeight'))
#        WindowController(self).__init__(self.plotter)
        self.showPlot = False
        self.scan = None
        self.src = self._find_source(cfg)
        print(f'Create scan with source {self.src}')
        self.scan = iscan.IScan(self.src)
        #
        #   Lay controls out in the window
        #
        manLayout0 = QVBoxLayout()
        #
        # First group select which traces to plot and display
        # the statistics.
        #
        box1 = QGroupBox('Select traces to plot')
        l1 = QVBoxLayout()
        box1.setLayout(l1)
        traceNames = ('V1', 'V2', 'Vm', 'V1 - V2',
                      'v1 + v2', 'V1 - V2/v1 + v2')
        self.trace1 = bcwidgets.NamedComboDisp('Plot 1 shows', traceNames)
        self.trace1.box.setCurrentIndex(0)
        l1.addLayout(self.trace1.layout)
        self.trace2 = bcwidgets.NamedComboDisp('Plot 2 shows', traceNames)
        self.trace2.box.setCurrentIndex(1)
        l1.addLayout(self.trace2.layout)
        self.trace3 = bcwidgets.NamedComboDisp('Plot 3 shows', traceNames)
        self.trace3.box.setCurrentIndex(2)
        l1.addLayout(self.trace3.layout)
        manLayout0.addWidget(box1)
        #
        #   Then start a section for the interactive grapher.
        #
        box2 = QGroupBox('Interactive plotting')
        l2 = QVBoxLayout()
        box2.setLayout(l2)
        #
        #   Top lines have settings and control buttons
        #
        oldSRate = cfg.inputs_get('SampleRate')
        self.srate = bcwidgets.NamedIntEdit('Sample Rate (sps)', oldSRate)
        l2.addLayout(self.srate.layout)
        #
        oldDur = cfg.inputs_get('LiveDuration')
        self.dur = bcwidgets.NamedFloatEdit('Duration (s)', oldDur)
        l2.addLayout(self.dur.layout)
        #
        oldURate = cfg.graphs_get('UpdateRate')
        self.urate = bcwidgets.NamedIntEdit('Data update Rate (sps)',
                                            oldURate)
        l2.addLayout(self.urate.layout)
        #
        oldNAvg = 30
        self.navg = bcwidgets.NamedIntEdit('Number of samples'
                                           ' to average per point',
                                           oldNAvg)
        l2.addLayout(self.navg.layout)
        #
        # Next line is for four buttons
        #
        line3 = QHBoxLayout()
        # START
        self.strtBtn = QPushButton("START")
        self.strtBtn.clicked.connect(self.on_click_start)
        line3.addWidget(self.strtBtn)
        # STOP
        self.stopBtn = QPushButton("STOP")
        self.stopBtn.setEnabled(False)
        self.stopBtn.clicked.connect(self.on_click_stop)
        line3.addWidget(self.stopBtn)
        # FOURIER
        self.showBtn = QPushButton("Show Fourier")
        self.showBtn.setEnabled(False)
        self.showBtn.clicked.connect(self.on_click_show)
        line3.addWidget(self.showBtn)
        # SAVE
        self.saveBtn = QPushButton("Save Data")
        self.saveBtn.setEnabled(False)
        self.saveBtn.clicked.connect(self.on_click_save)
        line3.addWidget(self.saveBtn)
        l2.addLayout(line3)
        manLayout0.addWidget(box2)
        
        #
        #   Start a Single-Shot section
        #
        box3 = QGroupBox('Single-shot plotting')
        l3 = QVBoxLayout()
        box3.setLayout(l3)
        #
        #   Only duration and sample rate settings
        #
        oldFSRate = cfg.inputs_get('SampleRate')
        self.fsrate = bcwidgets.NamedIntEdit('Sample Rate (sps)', oldFSRate)
        l3.addLayout(self.fsrate.layout)
        #
        oldFDur = cfg.inputs_get('LiveDuration')
        self.fdur = bcwidgets.NamedFloatEdit('Duration (s)', oldFDur)
        l3.addLayout(self.fdur.layout)
        #
        fitTypes = ("linear", "decaying exponential")
        #
        self.fVdiv = bcwidgets.NamedReadOnlyEdit('Fourier Vdiv')
        self.noise = bcwidgets.NamedReadOnlyEdit('Noise')
        self.signalNoiseRatio = bcwidgets.NamedReadOnlyEdit('Signal to noise ratio')
        l3.addLayout(self.fVdiv.layout)
        l3.addLayout(self.noise.layout)
        l3.addLayout(self.signalNoiseRatio.layout)
        
        # Initializes a progress bar and puts it on the GUI 
        self.progressBar = ProgressBarWidget()
        l3.addWidget(self.progressBar.progress_bar)
        
        #
        # Next line is for three buttons
        #
        self.line3 = QHBoxLayout()
        # RUN
        self.fstrtBtn = QPushButton("RUN")
        self.fstrtBtn.clicked.connect(self.on_click_fstart)
        self.line3.addWidget(self.fstrtBtn)
        # FOURIER
        self.fshowBtn = QPushButton("Show Fourier")
        self.fshowBtn.setEnabled(False)
        self.fshowBtn.clicked.connect(self.on_click_fshow)
        self.line3.addWidget(self.fshowBtn)
        # RAW DDATA
        self.dshowBtn = QPushButton("Show Raw Data")
        self.dshowBtn.clicked.connect(self.on_click_dshow)
        self.dshowBtn.setVisible(False)
        self.line3.addWidget(self.dshowBtn)
        # SAVE
        self.fsaveBtn = QPushButton("Save Data")
        self.fsaveBtn.setEnabled(False)
        self.fsaveBtn.clicked.connect(self.on_click_fsave)
        self.line3.addWidget(self.fsaveBtn)
        l3.addLayout(self.line3)
        manLayout0.addWidget(box3)
        
        #
        #   Creates a button for enabling/disabling plot settings box
        #
        self.plotSettingsCheckbox = QCheckBox('Enable Fourier Plot Settings')
        self.plotSettingsCheckbox.setChecked(False)  # Set the initial state to disabled
        # Connect the checkbox's state change signal to a slot function that dispays the plot setting widget
        self.plotSettingsCheckbox.stateChanged.connect(self.togglePlotSettingsWidget)
        manLayout0.addWidget(self.plotSettingsCheckbox)
        
        #
        #   Start a Plot Settings Section
        #
        self.box4 = QGroupBox('Fourier Plot Settings')
        l4 = QVBoxLayout()
        self.box4.setLayout(l4)
       
        # Left and Right x limit settings *currently pulls values from _inDict, NOT using inputs_get
        # To pull value using inputs_get, update settings must be made in configurator.py
        self.lxlimit = bcwidgets.NamedFloatEdit('Left X Limit', cfg._inDict["LXLimit"])
        l4.addLayout(self.lxlimit.layout)
        
        self.rxlimit = bcwidgets.NamedFloatEdit('Right X Limit', cfg._inDict["RXLimit"])
        # Set the initial visibility of box4 based on the initial state of the checkbox
        self.box4.setVisible(self.plotSettingsCheckbox.isChecked())
        l4.addLayout(self.rxlimit.layout)
        
        # Next line creates a layout for fourier plot settings buttons
        line4 = QHBoxLayout()
        # SET
        self.plotSettingsBtn = QPushButton("Set Fourier Axis")
        self.plotSettingsBtn.clicked.connect(self.on_click_plot_set)
        line4.addWidget(self.plotSettingsBtn)
        l4.addLayout(line4)
        
        self.lNoiseLimit = bcwidgets.NamedFloatEdit('Left Noise Fit Limit', 1)
        l4.addLayout(self.lNoiseLimit.layout)
        
        self.rNoiseLimit = bcwidgets.NamedFloatEdit('Right Noise Fit Limit', 6)
        l4.addLayout(self.rNoiseLimit.layout)
        
        # Next line creates a layout for fourier plot settings buttons
        line4 = QHBoxLayout()
        # SET
        self.noiseSettingsBtn = QPushButton("Set Noise Fit")
        self.noiseSettingsBtn.clicked.connect(self.on_click_noise_set)
        line4.addWidget(self.noiseSettingsBtn)
        l4.addLayout(line4)
        
        manLayout0.addWidget(self.box4)
        
        #
        #
        #   Assemble
        #
        manLayout0.addStretch()
        self.setLayout(manLayout0)
    
    # Description: Checks to see if the graph, plotname, is one of the active traces being plotted    
    # Parameter, plotname: A string representing the name of the plot you're checking for
    # Return: plot_data, a tuple where the 1st and 2nd element are the x and y data respectively
    def checkExistanceOfGraph(self, plotname):
        
        if self.trace1.text() == plotname or self.trace2.text() == plotname or self.trace3.text() == plotname:
            if self.trace1.text() == plotname:
                plot = self.plotter.g1.getPlotItem()
                
                # Get the plot data items                
                data_items = plot.listDataItems()
                
            if self.trace2.text() == plotname:
                plot = self.plotter.g2.getPlotItem()
                
                # Get the plot data items                
                data_items = plot.listDataItems()
                
            if self.trace3.text() == plotname:
                plot = self.plotter.g3.getPlotItem()
                
                # Get the plot data items                
                data_items = plot.listDataItems()
                
            # Extract the plot data from the data items
            plot_data = []
            for item in data_items:
                # The plot data is stored in the 'xData' and 'yData' attributes
                x_data = item.xData
                y_data = item.yData
                plot_data.append((x_data, y_data))
                
            return plot_data
       
        # Activated if none of the graphs shown are Vm    
        else:
            print("U done screwed up my dude")  # Error message courteousy of Rebecca.
            return None
        
        
    # Description: Finds the position of the main magnetic peak
    # Return: max_index, the index in the signal arrays where the magnetic peak is located    
    def getMagneticPeak(self):
                
        # Check which trace has Vm in it and return data_items
        plot_data = self.checkExistanceOfGraph('Vm')
        
        # Is there plot data or not? Did you plot the graph of interest?
        if plot_data:
            data = plot_data[0] # data is a list of two elements where the 1st is the x and 2nd is the y array
                
            # The index of the max value (np.argmax) is the index of the magnetic peak
            max_index = np.argmax(data[1])
            
        else:
            max_index = None
            print("There's no plot data, shmuck")
        
        return max_index
    
    # Description: Takes in a signal and returns a clipped version of the signal based on the x-axis
    # Parameter, data: A signal array where the 1st element is a list of x values and the 2nd is y values
    # Parameter, start: A numeric describing the minimum x value to place in the return array
    # Parameter, end: A numeric describing the maximum x value to place in the return array
    # Return: subset_data, a signal where  1st and 2nd elements are clipped x,y arrays based on the input data
    def adjustFitRange(self, data, start, end):
        
        # Make lists to hold x,y subset of return data
        x_array = []
        y_array = []
        
        # Iterate through X data and if element sits in desired range, save it
        for index, freq in enumerate(data[0]):
            if freq >= start and freq <= end:
                intensity = data[1][index]
                x_array.append(freq)
                y_array.append(intensity)
                
        # shove x and y arrays into tuple to be returned
        np_x_array = np.array(x_array)
        np_y_array = np.array(y_array)
        subset_data = (np_x_array, np_y_array)        

        return subset_data
    
    # Descrption: Defines a function to create a linear fit of data
    # Return: line_of_best_fit, an array of the y values for best fit line
    def linearFit(self, data):
        
        # Perform linear regression (fit a line of best fit)
        coefficients = np.polyfit(data[0], data[1], 1)
        slope = coefficients[0]
        intercept = coefficients[1]
        
        # Generate the line of best fit
        line_of_best_fit = slope * data[0] + intercept
        
        return line_of_best_fit
    
    # Description: Fits a line to data under the assumption that at every point in frequency space the
    #              y value of the line is the noise at that point. This noise is then used to display
    #              the noise and signal to noise ratio.
    # Parameter, max_index: The index in our data where our signal is at. To fit a line to the data
    #                       we want to remove the signal so the fit is based on noise and not the signal.
    def findAndFitNoise(self, max_index):

        # Check which trace has Vm in it and return data_items
        plot_data = self.checkExistanceOfGraph('V1 - V2/v1 + v2')
        
        # Plot data is a list containing two inner lists, grab first list containing
        # x and y data arrays
        data = plot_data[0]
        
        # Clip our data so that we only plot some subset
        rerange_data = self.adjustFitRange(data, 0, 25)
        
        # Make a new array without signal peak located at index, max_index
        cleaned_rerange_data = (np.delete(rerange_data[0], max_index), np.delete(rerange_data[1], max_index))
        
        # The below variables determine the start and end of the linear fit in Hz. Adjust these values as needed.
            # To the next dedicated individual, this is worth adding in as text boxes to the plot settings box so 
            # it can be adjusted from the GUI.
            # Update: I added in a setting to adjust from the GUI but it's not complete - see on_click_noise_set
        start = 1
        end = 6
        # Take subset of data for fit to get more accurate portrayal of noise
        # where signal comes in, in frequency space.
        fit_data = self.adjustFitRange(rerange_data, self.lNoiseLimit.value(), self.rNoiseLimit.value())
       
        # Fit a line to the data
        linear_fit = self.linearFit(fit_data)
        
        # Plot the original data and the fitted curve
        plt.scatter(rerange_data[0], rerange_data[1], color = "blue", label='Signal')
        plt.scatter(cleaned_rerange_data[0], cleaned_rerange_data[1], color = "red")
        plt.plot(fit_data[0], linear_fit, 'b-', label = 'Linear Fit')
        plt.xlabel('x')
        plt.ylabel('y')
        plt.legend()
        plt.show()
        
        noise = linear_fit[max_index]
        self.noise.show(noise)
        self.signalNoiseRatio.show(rerange_data[1][max_index] / noise)

    def close(self):
        print('Close rplotter')
        if self.plotter is not None:
            self.plotter.hide()
        self.plotter = None
        if self.scan is not None:
            self.scan.close()
        self.scan = None

    def closeEvent(self, event):
        print('rplotter closing')
        self.close()

    def childClosing(self):
        self.saveBtn.setEnabled(False)
        self.showPlot = False
        
    # Description: Handle displaying a plot settings box when user checks plot settings box
    # Parameter, state: a boolean representing the state of plot settings checkbox (true or false).
    def togglePlotSettingsWidget(self, state):
        
        # Initialize variable, checked, that is true if checkbox is checked
        checked = state == Qt.Checked
        
        # Make the plot settings box visible
        self.box4.setVisible(checked)
       
        # If user turns off plot settings, show original Fourier plot by calling _do_fourier
        # but don't do this unless Fourier data has been collected - hasattr checks if class attribute 'fv1', fourier data, exists.
        if self.plotSettingsCheckbox.isChecked() == False and hasattr(self, "fv1"): 
            self._do_fourier()
        
        # Adjust the size of the parent widget to accommodate the visibility change
        self.adjustSize()
        
    @pyqtSlot()
    def on_click_plot_set(self):
        print("Changing plot settings")
        self._do_fourier()
    
    # *** This setting kinda works, there are several bugs to be sorted out however:
        # 1. findAndFitNoise should verify that linear_fit[max_index] is the frequency
        #    of the magnetic peak and not just the corresponding index along the line
        # 2. if the fit range is set outside of the frequency of the signal you can't grab the noise
        #    so a check should be put in to prevent this
        # Apologies, just didn't have time to finish this setting.
    @pyqtSlot()
    def on_click_noise_set(self):
        print("Changing fit settings - NOTE THIS FEATURE IS NOT COMPLETE")
        max_index = self.getMagneticPeak()
        self.findAndFitNoise(max_index)

    @pyqtSlot()
    def on_click_start(self):
        print('Start pressed')
        self._do_scan(True)
        
    @pyqtSlot()
    def on_click_stop(self):
        print('Stop scan')
        self.stopScan = True
        self.strtBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        self.saveBtn.setEnabled(True)
        self.showBtn.setEnabled(True)

    @pyqtSlot()
    def on_click_close(self):
        print('Close plotter')
        self.plotter.hide()

    @pyqtSlot()
    def on_click_show(self):
        print('Show Fourier')
        self._do_fourier()

    @pyqtSlot()
    def on_click_save(self):
        if self.scan is not None:
            fname = self._unique_file_name()
            fname = fname + ".csv"
            print(f'Save data to {fname}')
            self.scan.saveTo(fname)
            
    # Description: A slot function that describes how to control the GUI and collect data in single shot data acqusition.
    @pyqtSlot()
    def on_click_fstart(self):
        print('Collect Fourier pressed')
        
        # The below chunk of code acquires data using a daq_thread and collects it in chunks so that a progress bar can be displayed
        # the caveat is that the progress bar can make the raw data a bit jumpier due to a delay in stopping and starting a new chunk.
        # Use the below chunk if you'd like to have a progress bar and please note the chunk size can be adjusted by setting daq_thread.chunk_size
        # to make the chunks bigger so less jumps are introduced.
        
        self.daq_thread = DAQThread(self.src, self.fdur.value(), self.fsrate.value())
        self.progressBar.start_progress(self.daq_thread)
        
        self._swapActiveButtonWidget(self.dshowBtn, self.fshowBtn)
        self._do_single_plot()
        self.fsaveBtn.setEnabled(True)
        self.fshowBtn.setEnabled(True)
        
        # The below chunk of code acquires a constant stream of raw data at the cost of the progres bar. This is because if the data is continuously collected
        # there is no point to signal the progress bar should be updated. Use the below chunk of code if there seems to be an issue in data acqusition because it is
        # more safe but as of writing this comment we have seen no issues in the chunk data acquisition when the fourier is run on the data.
        
        # self._swapActiveButtonWidget(self.dshowBtn, self.fshowBtn)
        # self._do_single()
        # self.fsaveBtn.setEnabled(True)
        # self.fshowBtn.setEnabled(True)
    
    # Description: A slot function that switches the active plots from fourier data to raw data
    @pyqtSlot()
    def on_click_dshow(self):
        print('Show raw data')
        self._swapActiveButtonWidget(self.dshowBtn, self.fshowBtn)
        self._do_single_plot()
        self.fsaveBtn.setEnabled(True)
        self.fshowBtn.setEnabled(True)
        
    # Description: A slot function that switches the active plots from raw data to fourier data, finds the index of the signal peak, and displays a noise plot w/ linear fit
    @pyqtSlot()
    def on_click_fshow(self):
        print('Show Fourier in Fourier')
        self._swapActiveButtonWidget(self.fshowBtn, self.dshowBtn)
        self._do_fourier()
        self.dshowBtn.setEnabled(True)
        max_index = self.getMagneticPeak()
        self.findAndFitNoise(max_index)
        self.fVdiv.show(self.fdiv[max_index + 1])

    @pyqtSlot()
    def on_click_fsave(self):
        print('Save Fourier pressed')
        base_name = self._unique_file_name()
        fname = base_name + "Four.csv"
        print(f'Save Fourier to {fname}')
        darray = np.stack((self.freq, self.fv1, self.fv2, self.fvm,
                           self.fv1mv2, self.fv1pv2, self.fdiv), axis=1)
        hdr = 'freq,V1,V2,Vm,V1-V2,V1+V2,Vdiv'
        np.savetxt(fname, darray, header=hdr, delimiter=', ')
        self.scan.saveTo(base_name + '.csv')

#
#   Internal helpers
#

    # Description: A VERY SIMPLE widget swapper that swaps the visibility of two widgets.
    #              In its current form it requires that the widgets be in the same layout group.
    #              This could be made more general by returning the layout of widget 1 and swapping it with that of 
    #              widget 2, making one widget active and the other inactive, etc - it's just a little gross to do with
    #              the way different widgets are nested differently in the layout.
    def _swapActiveButtonWidget(self, widget1, widget2):
        widget1.setVisible(False)
        widget2.setVisible(True)

    def _find_source(self, cfg: FConfig) -> VoltageSource:
        print('rplotter')
        print(cfg._config)
        rate = cfg.inputs_get('SampleRate')
        head = cfg.inputs_get('InDev')
        print(head)
        print(f'len(head) = { len(head)}')
        ch_names = [cfg.inputs_get('V1Chan'),
                    cfg.inputs_get('V2Chan'),
                    cfg.inputs_get('VMChan')]
        full_names = ch_names
        for i in range(3):
            full_names[i] = head + '/' + ch_names[i]
        if len(head) < 1:
            return FaradaySource(ch_names, rate)
        print(full_names)
        if head.startswith('Dev'):
            # return FaradaySource(ch_names, rate)
            # Only import if needed!
            from nidaqmxsource import NidaqmxSource
            return NidaqmxSource(full_names, rate)
        return VoltageSource(ch_names, rate)

    def _unique_file_name(self) -> str:
        dstr = datetime.today().strftime('%m%d%y-%M%H')
        root = self.cfg.get('DataPrefix')
        return f'{root}{dstr}'

    #
    # _do_fourier transforms all data and updates displayed traces.
    #
    def _do_fourier(self):
        if self.scan is None:
            print('There are no current scan data.')
            return
        #
        # Work through the 6 data arrays
        #
        self.fv1 = np.absolute(np.fft.rfft(self.scan.v1))
        # print(self.fv1[:20])
        self.fv2 = np.absolute(np.fft.rfft(self.scan.v2))
        # print(self.fv2[:20])
        self.fvm = np.absolute(np.fft.rfft(self.scan.vm))
        # print(self.fvm[:20])
        self.fv1mv2 = np.absolute(np.fft.rfft(self.scan.v1mv2))
        # print(self.fv1mv2[:20])
        self.fv1pv2 = np.absolute(np.fft.rfft(self.scan.v1pv2))
        # print(self.fv1pv2[:20])
        self.fdiv = np.absolute(np.fft.rfft(self.scan.div))
        # print(self.fdiv[:20])
        
        ftraces = ( self.fv1, self.fv2, self.fvm, 
                    self.fv1mv2, self.fv1pv2, self.fdiv )
        # fmax = 1 + self.dur.value() * self.urate.value() * 0.5
        fmax = 0.5/(self.scan.times[1] - self.scan.times[0])
        print('Fourier', len(self.scan.v1), len(self.fv1), fmax)
        self.freq = np.linspace(0, fmax, len(self.fv1))
        n_fin = 600


        # Create plot 3
        self.plotter.g3.clear()
        print(self.freq[0:2])
        self.plotter.g3.plot(x=self.freq[1:n_fin],
                             # y=np.log10(ftraces[self.plots[2]]),
                             y=ftraces[self.plots[2]][1:n_fin],
                             name= iscan.IScan.plotNames[0], pen='r',
                             symbol='o', symbolPen='r',
                             symbolBrush='r',
                             symbolSize=2, pxMode=True)
        self.plotter.g3.setLabel('bottom', 'Frequency (Hz)')
        
        # Create plot 1
        self.plotter.g1.clear()
        print(self.freq[0:2])
        self.plotter.g1.plot(x=self.freq[1:n_fin], 
                             # y=np.log10(ftraces[self.plots[0]]),
                             y=ftraces[self.plots[0]][1:n_fin],
                             name= iscan.IScan.plotNames[0], pen='b',
                             symbol='o', symbolPen='b',
                             symbolBrush='b',
                             symbolSize=2, pxMode=True)
        
        # Create plot 2
        self.plotter.g2.clear()
        print(self.freq[0:2])
        self.plotter.g2.plot(x=self.freq[1:n_fin],
                             # y=np.log10(ftraces[self.plots[1]]),
                             y=ftraces[self.plots[1]][1:n_fin],
                             name= iscan.IScan.plotNames[0], pen='g',
                             symbol='o', symbolPen='g',
                             symbolBrush='g',
                             symbolSize=2, pxMode=True)
        
        # All plots should begin by being autoranged
        self.plotter.g1.enableAutoRange(axis=ViewBox.XYAxes)
        self.plotter.g2.enableAutoRange(axis=ViewBox.XYAxes)
        self.plotter.g3.enableAutoRange(axis=ViewBox.XYAxes)
        
        # If plot settings checkbox is checked, use user plot limits
        if self.plotSettingsCheckbox.isChecked():
            self.plotter.g1.setXRange(self.lxlimit.value(), self.rxlimit.value())
            self.plotter.g2.setXRange(self.lxlimit.value(), self.rxlimit.value())
            self.plotter.g3.setXRange(self.lxlimit.value(), self.rxlimit.value())
        
        # Show plots
        self.plotter.g1.show()
        self.plotter.g2.show()
        self.plotter.g3.show()
    #
    # _do_scan actually takes the data and maintains the plots.
    # It takes one argument that determines whether the scan runs
    # continuously or stops after one iteration.
    #
    def _do_scan(self, multi=True):
        # Get params from controls and send to scan
        self.scan.setDuration(self.dur.value())
        print(f'Orig sample rate {self.scan.sample_rate}')
        self.scan.setSampleRate(self.srate.value())
        print(f'Sample rate set to {self.scan.sample_rate}')
        self.scan.setNAverage(self.navg.value())
        # Clean plotter and connect to scan
        self.plotter.clear()
        self.scan.sendPlotsTo(self.plotter)
        self.plots = [self.trace1.value(), self.trace2.value(),
                 self.trace3.value()]
        print(f'plots = {self.plots}')
        self.scan.plotInPanes(self.plots)
        self.plotter.show()

        self.strtBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)
        self.saveBtn.setEnabled(False)

        u_rate = self.urate.value()
        step_dur = 0.93 / u_rate   # Tuned at 10/sec
        print(f'Step duration {step_dur}')
#        self.plotter.p3.setXRange(0.0, 1.0)
        self.plotter.g1.setYRange(0.0, 0.2)
        self.plotter.g2.setYRange(0.0, 0.2)
        self.plotter.g3.setYRange(-5.5, 5.5)
        self.stopScan = False
        self.scan.startScan(u_rate)

        get_time = time.time
        time_1s = 1
#        start_time = get_time()
        step_dur = time_1s / u_rate
        n_point = int(self.dur.value() * self.urate.value())
        print(self.dur.value(), self.urate.value(), n_point)
        #raw_step_times = np.linspace(0, self.dur.value(), n_point)
        tick_rate = ttimer.init()
        raw_step_times = np.linspace(0, self.dur.value()*tick_rate, n_point,dtype=int)
        n_plot = self.cfg.graphs_get('UpdateRate')
        t_plot = 1.0 / n_plot
        print(f't_plot = {t_plot}')
        print(raw_step_times[:5])
        print(raw_step_times[-5:])
        step_idx = 0
        running = True
        #
        # Actual Scan starts here
        #
        while running:
            #t0 = get_time()
            t0 = ttimer.now()
            step_times = raw_step_times + t0
            pt = t0
            # Do One Scan
            for step_idx in range(n_point):
                while True:
                    # ct = get_time()
                    ct = ttimer.now()
                    if ct >= step_times[step_idx]:
                        break
                # print(ct)
                if ct > pt:
                    pt = pt + t_plot
                    self.scan.stepScan(True)
                else:
                    self.scan.stepScan(False)
                QApplication.processEvents()
                '''
                if self.stopScan:
                    running = False
                    break
                '''
            # End of scan. Update and see if do more scans.
            idx = self.trace1.value()
            self.trace1.show(self.scan.get_avg(idx), self.scan.get_err(idx))
            idx = self.trace2.value()
            self.trace2.show(self.scan.get_avg(idx), self.scan.get_err(idx))
            idx = self.trace3.value()
            self.trace3.show(self.scan.get_avg(idx), self.scan.get_err(idx))
            if not multi or self.stopScan:
                break
        #
        #   Scan ends here.
        #
        self.scan.stopScan()
        # execTime = (get_time() - start_time) / time_1s
        # print(f'Left scan loop. {itn} steps took {execTime} s')
        # print(f'scan avg = {s_sums/itn}  process avg = {p_sums/itn}')
        self.scan.dump()

    #
    #   Run a fast single scan. This is MUCH simpler.
    #
    def _do_single(self) -> None:
        
        # Clean plotter and connect to scan
        self.plotter.clear()
        self.scan.sendPlotsTo(self.plotter)
        self.plots = [self.trace1.value(), self.trace2.value(),
                  self.trace3.value()]
        print(f'plots = {self.plots}')
        self.scan.plotInPanes(self.plots)
        self.plotter.show()
        QApplication.processEvents()
        # Get params from controls
        dur = self.fdur.value()
        print(f'Single sample duration {dur}')
        rate = self.fsrate.value()
        print(f'Single sample rate set to {rate}')
        
        self.scan.singleScan(dur, rate)
        # Update statistics
        idx = self.trace1.value()
        self.trace1.show(self.scan.get_avg(idx), self.scan.get_err(idx))
        idx = self.trace2.value()
        self.trace2.show(self.scan.get_avg(idx), self.scan.get_err(idx))
        idx = self.trace3.value()
        self.trace3.show(self.scan.get_avg(idx), self.scan.get_err(idx))
        
    #
    #   Works the same as _do_single except the data is collected in chunks rather than as a stream to allow for a progress bar to run
    #
    def _do_single_plot(self) -> None:
        
        # Clean plotter and connect to scan
        self.plotter.clear()
        self.scan.sendPlotsTo(self.plotter)
        self.plots = [self.trace1.value(), self.trace2.value(),
                  self.trace3.value()]
        print(f'plots = {self.plots}')
        self.scan.plotInPanes(self.plots)
        self.plotter.show()
        QApplication.processEvents()
        # Get params from controls
        dur = self.fdur.value()
        print(f'Single sample duration {dur}')
        rate = self.fsrate.value()
        print(f'Single sample rate set to {rate}')
        
        # singleScanPlot is a modified DAQ/plotting function that collects data in chunks
        self.scan.singleScanPlot(dur, rate, self.daq_thread.data)
        
        # Update statistics
        idx = self.trace1.value()
        self.trace1.show(self.scan.get_avg(idx), self.scan.get_err(idx))
        idx = self.trace2.value()
        self.trace2.show(self.scan.get_avg(idx), self.scan.get_err(idx))
        idx = self.trace3.value()
        self.trace3.show(self.scan.get_avg(idx), self.scan.get_err(idx))
        

# ProgressBarWidget is a class that handles the creation and operation of a progress bar.
#   In its current implementation it only works as a DAQ progress bar but can be expanded to make more progress bars if needed.
class ProgressBarWidget(QWidget):
    
    # Create a signal to let the DAQ know that when the progress bar is completed data should stop being collected
    stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.progress_bar = QProgressBar()
        self.data_index = 0
        self.npoint = 0
        self.total_points = 0

    # Description: Handles the operation of the progress bar and data acquisition thread
    # Parameter, daq_thread: An object of type DAQThread that creates a thread which concurrently collects data (except Python isn't really multithreaded but shhhh)
    def start_progress(self, daq_thread):
        
        # Set progress bar to 0%
        self.progress_bar.setValue(0)
        
        # From the daq_thread object, conect its data_ready signal to the update_progress function within our progress bar
            # This makes it so that when the DAQ emits a signal saying that data is ready the progress bar updates its completion%
        daq_thread.data_ready.connect(self.update_progress)
        
        # From progress bar object, connect its stop_requested signal to the daq_thread's stop function
            # This makes it so that when the progress bar emits a stop signal the DAQ stops collecting data
        self.stop_requested.connect(daq_thread.stop)
        
        # Initialize class attribute for how many total points will be collected so completion% can be determined.
        self.set_total(daq_thread.npoint)
        
        # Start the DAQ
        daq_thread.run()

    # Description: Updates the progress bar completion percentage
    # Parameter, data_index: self.npoint is the total points to collect and data_index represents how many of that total has been collected.
    def update_progress(self, data_index):
    
        # Calculate the progress value based on the acquired data
        progress_value = int((data_index / self.npoint) * 100)
        
        # Set progresss bar value
        self.progress_bar.setValue(progress_value)
        
        # When progress bar is complete send a signal to DAQ for it to stop
        if progress_value >= 100:
            self.stop_progress()
            return
    
    # Description: Emits a signal telling the DAQ to stop collecting data
    def stop_progress(self):
        self.stop_requested.emit()
        
    # Description: Setter to set total points to be collected
    # Parameter, npoint: An integer represeting the number of points to be collected
    def set_total(self, npoint):
        self.npoint = npoint


# DAQThread, an extension of the QThread class to create a thread that handles data acqusition from the NI board
class DAQThread(QThread):
    
    # Signal emitted when data is ready, contains an integer describing the current index of the data aqusition so progress bar can update.
    data_ready = pyqtSignal(int)

    def __init__(self, src, dur, rate, chunk_size=100):
        super().__init__()
        self.daq_source = src
        self.chans = src.chan_names
        self.n_chan = len(self.chans)
        self.rate = rate
        self.duration = dur
        self.npoint = int(self.duration * self.rate)
        self.data = np.zeros((self.n_chan, self.npoint))
        self.chunk_size = chunk_size
        self.stopped = False
        self.data_index = 0

    # Description: Handles the thread data acqusition
    def run(self):
        print(f'Single sample duration {self.duration}')
        print(f'Single sample rate set to {self.rate}')
        print(f'Single collect {self.npoint} points')
        
        # While the stop signal has not been sent by the progress bar, collect data
        while not self.stopped:
            
            # Read the data in chunks of size, chunk_size. Alter this class attribute to make bigger or smaller chunks
                # Bigger chunk sizes mean there are less gaps in data acqusition at the cost of a progress bar that updates slower
                # Smaller chunks means that there will be more gaps in data acqusition but the progress bar updates faster.
                    # Gaps in data acquisition are due to the time it takes the thread to save the chunk and request the DAQ for a new one
            data = self.daq_source.readN(self.chunk_size)
            
            # Don't read empty data from the DAQ
            if data is None:
                print("Data is None")
                break
            
            # Once the chunk has been acquired quickly save it in an array and emit a signal to update progress bar
            self.update_data(data)
            self.data_ready.emit(self.data_index)
        
    # Description: Takes in a chunk of data and places it in the appropriate spot of a data array.
    # Parameter, data: A 3 dimensional array containing 3 channels of chunk data
    def update_data(self, data):
        
        # new_index is the index to end placing data in a pre-allocated array - determined by where we left off placing data and size of chunk
        new_index = self.data_index + len(data[0])
        
        # Place our 3 channels of data in 3 indices of a data array
        for index, array in enumerate(data):
            self.data[index][self.data_index:new_index] = array
        
        # Save index of where to next begin placing data based on where we ended
        self.data_index = new_index
    
    # Description: When the stop signal is received from progress bar set self.stopped to True so that data acqusition stops
    def stop(self):
        self.stopped = True
