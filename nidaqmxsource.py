#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nidaqmxsource.py

A class for nidaqmx instruments that measure voltages
and return single or multiple values on multiple
channels.

@author: bcollett
"""
import numpy as np
#
#   NI imports
#
import nidaqmx as ni
from nidaqmx.constants import Edge, AcquisitionType
#from nidaqmx.stream_readers import AnalogSingleChannelReader
from nidaqmx.stream_readers import AnalogMultiChannelReader

class NidaqmxSource:
    def __init__(self, chans: list, rate=1000):
        self.max_sample_rate = 1_000_000
        self.task = None
        # For moment chans must be a list or tuple of names
        # acceptable to nidaqmx, e.g. 'Dev/ai0'.
        for ch in chans:
            if type(ch) != str:
                raise TypeError('Voltage channel names must be strings')
        self.chan_names = chans
        self.n_chan = len(chans)
        self.task = ni.Task()
        #
        # Pull sample rate into range
        #
        self.setDataRate(rate)
        print(f'Sampling at {self.sample_rate} sps')
        # Install channels
        for ch in chans:
            self.task.ai_channels.add_ai_voltage_chan(ch)
        # Install rate source and create the reader
        self.task.timing.cfg_samp_clk_timing(self.sample_rate,
                                             sample_mode=AcquisitionType.FINITE,
                                    active_edge=Edge.RISING)
        self.reader = AnalogMultiChannelReader(self.task.in_stream)
    
    def close(self):
        print('Close nidaqmxsource')
        if self.task is not None:
            print('Close nidaqmx task')
            self.task.stop()
            self.task.close()
            self.task = None
    
    def __del__(self):
        print('Destroy nidaqmxsource')
        self.close()
    
    def setDataRate(self, rate: int) -> None:
        self.sample_rate = self._setGoodSampleRate(rate)

    def readOneFrom(self, chan: int) -> float:
        data = np.zeros((self.n_chan,1))
        if 0 <= chan and chan < self.n_chan:
            self.task.start()
            nread = self.reader.read_many_sample(data, 
                                    number_of_samples_per_channel=1,
                                    timeout=2)
            self.task.stop()
            return data[chan]
        else:
            raise IndexError(f'Channel numbe {chan} is out of range 0-{self.n_chan} in readOneFrom')
    
    def readNFrom(self, chan: int, n2read: int) -> np.ndarray:
        data = np.zeros((self.n_chan, n2read))
        if 0 <= chan and chan < self.n_chan:
            self.task.start()
            nread = self.reader.read_many_sample(data, 
                                    number_of_samples_per_channel=n2read,
                                    timeout=2)
            self.task.stop()
            return data[chan, :]
        else:
            raise IndexError(f'Channel number {chan} is out of range'
                             ' 0-{self.n_chan}')

    def readAvgFrom(self, chan: int, n2avg: int) -> float:
        data = np.zeros((self.n_chan, n2avg))
        if 0 <= chan and chan < self.n_chan:
            self.task.start()
            self.reader.read_many_sample(data,
                                         number_of_samples_per_channel=n2avg,
                                         timeout=2)
            self.task.stop()
            return np.average(data[chan, :])
        else:
            raise IndexError(f'Channel numbe {chan} is out of range'
                             ' 0-{self.n_chan} in readAvgFrom')

    def readOne(self) -> float:
        data = np.zeros((self.n_chan, 1))
        self.task.start()
        self.reader.read_many_sample(data,
                                     number_of_samples_per_channel=1,
                                     timeout=2)
        self.task.stop()
        return data

    def readN(self, n2read: int) -> np.ndarray:
        data = np.zeros((self.n_chan, n2read))
        self.task.start()
        self.reader.read_many_sample(data,
                                     number_of_samples_per_channel=n2read,
                                     timeout=2)
        self.task.stop()
        return data

    def readAvg(self, n2avg: int) -> float:
        data = np.zeros((self.n_chan, n2avg))
        self.task.timing.cfg_samp_clk_timing(self.sample_rate,
                                             sample_mode=AcquisitionType.FINITE,
                                             samps_per_chan=n2avg)
        self.task.start()
        nread = self.reader.read_many_sample(data,
                                             number_of_samples_per_channel=n2avg,
                                             timeout=2)
        if nread < n2avg:
            print(f'Asked for {n2avg} got {nread}')
        self.task.stop()
        return np.average(data, axis=1)

    #
    # Internal helpers
    # First pulls sample rate into range, sets internally, and returns.
    # Max rate is spread over all channels.
    # Min rate is, arbitrarily, 1 (as it has to be an integer)
    def _setGoodSampleRate(self, origRate: int):
        newRate = origRate
        maxRate = self.max_sample_rate / self.n_chan
        if newRate < 1:
            newRate = 1
        if newRate > maxRate:
            newRate = maxRate
        self.sampleRate = newRate
        return newRate
