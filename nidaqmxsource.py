#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nidaqmxsource.py

A class for nidaqmx instruments that measure voltages
and return single or multiple values on multiple
channels.

New version uses the fast nipy library instead of the general
purpose NIDAQmx libary.

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

#import ttimer
#import nipy

import tracemalloc

tracemalloc.start()


class NidaqmxSource:
    nInstance = 0;
    
    def __init__(self, chans: list, rate=1000):
        NidaqmxSource.nInstance += 1
        self.instance = NidaqmxSource.nInstance
        self.max_sample_rate = 1_000_000
        self.task = None
        print(f'NidaqmxSource({list},{rate}) No {self.instance}')
        # For moment chans must be a list or tuple of names
        # acceptable to nidaqmx, e.g. 'Dev/ai0'.
        for ch in chans:
            if type(ch) != str:
                raise TypeError('Voltage channel names must be strings')
        self.chan_names = chans
        self.n_chan = len(chans)
        #
        # Pull sample rate into range
        #
        self.setDataRate(rate)
        print(f'Sampling at {self.sample_rate} sps')
        
        self.task = ni.Task()
        # Install channels
        for ch in chans:
            self.task.ai_channels.add_ai_voltage_chan(ch)

        # Install rate source and create the reader
        # self.task.timing.cfg_samp_clk_timing(self.sample_rate,
        #                                      sample_mode=AcquisitionType.CONTINUOUS,
        #                                      active_edge=Edge.RISING)
        self.reader = AnalogMultiChannelReader(self.task.in_stream)
        

    def close(self):
        print(f'Close nidaqmxsource {self.instance}')
        self.instance = -1
        if self.task is not None:
            print('Close nidaqmx task')
            self.task.stop()
            self.task.close()
            self.task.__del__()
            self.task = None
        # nipy.close()
    
    def __del__(self):
        print('Destroy nidaqmxsource')
        self.close()
    
    def setDataRate(self, rate: int) -> int:
        self.sample_rate = self._setGoodSampleRate(rate)
        # nipy.init(self.sample_rate)
        return self.sample_rate

    #
    #   The plain read routines are only suitable for data collection
    #   at relatively slow rates becuase they start and stop the task
    #   for every call. This takes 10s of ms. THus you can't call these
    #   routines more than about 20 times per second.
    #
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

    def readN(self, n2read: int, tmax=2) -> np.ndarray:
        data = np.zeros((self.n_chan, n2read))
        self.task.timing.cfg_samp_clk_timing(self.sample_rate,
                                             sample_mode=AcquisitionType.FINITE,
                                             samps_per_chan=n2read)
        self.task.start()
        self.reader.read_many_sample(data,
                                     number_of_samples_per_channel=n2read,
                                     timeout=tmax)
        self.task.stop()
        return data
    
    # Original version that uses PyNIDAQmx Takes >=17ms/call
    def readAvg(self, n2avg: int) -> float:
        data = np.zeros((self.n_chan, n2avg))
        # print(f'Read avg rate {self.sample_rate}')
        # nit1 = ttimer.now()
        self.task.timing.cfg_samp_clk_timing(self.sample_rate,
                                             sample_mode=AcquisitionType.FINITE,
                                             samps_per_chan=n2avg)
        # nit2 = ttimer.now()
        self.task.start()
        nread = self.reader.read_many_sample(data,
                                             number_of_samples_per_channel=n2avg,
                                             timeout=2)
        # nit3 = ttimer.now()
        if nread < n2avg:
            print(f'Asked for {n2avg} got {nread}')
        # print(f'Asked for {n2avg} got {nread} at {self.sample_rate}')
        self.task.stop()
        # nit4 = ttimer.now()
        # print(nit2-nit1, nit3-nit1, nit4-nit1)
        return np.average(data, axis=1)
    '''
    
    # New version using the homegrown nipy functions.
    def readAvg(self, n2avg: int) -> float:
        t1 = ttimer.now()
        r = nipy.read(n2avg)
        t2 = ttimer.now()
        print('>',t2-t1)
        return r
    '''
    #
    #   This set is designed to support high frequency reads.
    #   For these you must call an init function that sets the
    #   data rate, sample configuration, and MAXIMUM TOTAL number of
    #   samples to be read through the lifetime of the complete
    #   task.
    #   Then you need to call the get function at least as
    #   as the samples will be generated to avoid over-run errors.
    #   Finally, you have to call the close function to tidy
    #   up the task and release storage.
    #   I start with a set that provide single reads of all the
    #   pre-set channels. I uses the data rate and list of channels
    #   from the class. It sets the task to doing continuous reads
    #   so no limit is required.
    #
    def single_init(self) -> None:
        print('Single init')
        self.task = ni.Task()
        # Install channels
        for ch in self.chan_names:
            self.task.ai_channels.add_ai_voltage_chan(ch)
        # Install rate source and create the reader
        self.task.timing.cfg_samp_clk_timing(self.sample_rate,
                                             sample_mode=AcquisitionType.CONTINUOUS,
                                             active_edge=Edge.RISING)
        self.reader = AnalogMultiChannelReader(self.task.in_stream)
        self.task.start()
    
    def single_close(self) -> None:
        print('single close')
        self.task.stop()
        self.task.clear()
        self.task = 0
    
    def single_read(self) -> np.ndarray:
        print('single read')
        data = np.zeros((self.n_chan, 1))
        n_read = self.reader.read_many_sample(data,
                                              number_of_samples_per_channel=1,
                                              timeout=2)
        # data[self.n_chan] = ttimer.now() * 1.0e-7
        if n_read < self.n_chan:
            print(f'Asked for {self.n_chan} got {n_read}')
        # print(f'Asked for {n2avg} got {nread} at {self.sample_rate}')
        print(data)
        return data
    #
    #   Second set does multiple reads and returns them all. Again
    #   it uses the data rate and list of channels
    #   from the class. It sets the task to doing continuous reads
    #   so no limit is required.
    #
    def multi_init(self, n_point: int) -> None:
        self.n_point = n_point
        print(f'Multi init {self.n_point}')
        self.data = np.zeros((self.n_chan, n_point))
        self.task = ni.Task()
        # Install channels
        for ch in self.chan_names:
            self.task.ai_channels.add_ai_voltage_chan(ch)
        # Install rate source and create the reader
        self.task.timing.cfg_samp_clk_timing(self.sample_rate,
                                             sample_mode=AcquisitionType.CONTINUOUS,
                                             active_edge=Edge.RISING)
        self.reader = AnalogMultiChannelReader(self.task.in_stream)
        self.task.start()
    
    def multi_close(self) -> None:
        print('multi close')
        self.task.stop()
        self.task.clear()
        self.task = 0
    
    def multi_read(self) -> np.ndarray:
        print('multi read')
        n_read = self.reader.read_many_sample(self.data,
                                              number_of_samples_per_channel=self.n_point,
                                              timeout=2)
        if n_read < self.n_n_point:
            print(f'Asked for {self.n_point} got {n_read}')
        return self.data
    #
    # Internal helpers
    # First pulls sample rate into range, sets internally, and returns.
    # Max rate is spread over all channels.
    # Min rate is, arbitrarily, 1 (as it has to be an integer)
    def _setGoodSampleRate(self, origRate: int) -> int:
        newRate = origRate
        maxRate = self.max_sample_rate / self.n_chan
        if newRate < 1:
            newRate = 1
        if newRate > maxRate:
            newRate = maxRate
        self.sampleRate = int(newRate)
        print('New sample rate = ', newRate)
        return newRate

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    rate = 10000
    duration = 5
    clist = [ '/Dev2/ai0', '/Dev2/ai1', '/Dev2/ai2' ]
    daq = NidaqmxSource(clist, rate=rate)
    d = daq.readN(duration * rate, tmax=duration+1)
#    d = np.array( [0,0,0,1.0,1.0,1.0,2.0,2.0,2.0]) 
#    d = np.reshape(d, (3,3))
    nc, npt = d.shape
    print(d[:, 0])
    print(d[:, 1])
    print(d[:, 2])
    daq.close()
    t = np.linspace(0, 1.0, npt)
    plt.plot(t, d[2,:], ',')
    print('Ending')