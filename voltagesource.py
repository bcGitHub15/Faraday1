#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
voltagesource.py

A base class for instruments that measure voltages
and return single or multiple values on multiple
channels.

@author: bcollett
"""
import numpy as np

class VoltageSource:
    def __init__(self, chans, rate: int):
        # For moment chans should be a list or tuple of names
        for ch in chans:
            if type(ch) != str:
                raise TypeError('Voltage channel names must be strings')
        self.chan_names = chans
        self.n_chan = len(chans)
        self.sample_rate = int(rate)
    
    def setDataRate(self, rate: int) -> None:
        self.sample_rate = int(rate)

    def readOneFrom(self, chan: int) -> float:
        if 0 <= chan and chan < self.n_chan:
            return 0.0
        else:
            raise IndexError(f'Channel numbe {chan} is out of range 0-{self.n_chan} in readOneFrom')

    def readNFrom(self, chan: int, n2read: int) -> np.ndarray:
        if 0 <= chan and chan < self.n_chan:
            res = np.random(n2read)
            return res
        else:
            raise IndexError(f'Channel numbe {chan} is out of range 0-{self.n_chan}')

    def readAvgFrom(self, chan: int, n2avg: int) -> float:
        if 0 <= chan and chan < self.n_chan:
            return 0.1
        else:
            raise IndexError(f'Channel numbe {chan} is out of range 0-{self.n_chan} in readAvgFrom')
    
    # Sim but do all channels at once
    def readOne(self) -> float:
        return np.zeros(self.n_chan)
    
    def readN(self, n2read: int) -> np.ndarray:
        res = np.random((self.n_chan, n2read))
        return res

    def readAvg(self, chan: int, n2avg: int) -> float:
        return np.zeros(self.n_chan)
