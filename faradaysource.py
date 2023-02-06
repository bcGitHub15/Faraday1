#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
faradaysource.py

A class for a dummy source that returns a small noise signal
on channels 0 and 1 and returns a sine wave on channel 2.
Rest return 0.

@author: bcollett
"""
import numpy as np
import time
from voltagesource import VoltageSource

class FaradaySource(VoltageSource):
    def __init__(self, chans, rate: int):
        # For moment chans should be a list or tuple of names
        for ch in chans:
            if type(ch) != str:
                raise TypeError('Voltage channel names must be strings')
        self.chan_names = chans
        self.n_chan = len(chans)
        self.sample_rate = int(rate)
        self.start = time.monotonic()
    
    def setDataRate(self, rate: int) -> None:
        self.sample_rate = int(rate)
    
    def readOneFrom(self, chan: int) -> float:
        if 0 <= chan and chan < self.n_chan:
            if chan == 0:
                return np.random.random() * 0.04
            elif chan == 1:
                return np.random.random() * 0.04 + 0.1
            elif chan == 2:
                now = time.monotonic()
                t = now - self.start
                return np.sin(4 * np.pi * t) * 4
            else:
                return 0.0
        else:
            raise IndexError(f'Channel number {chan} is out of range 0-{self.n_chan} in readOneFrom')
    
    def readNFrom(self, chan: int, n2read: int) -> np.ndarray:
        if 0 <= chan and chan < self.n_chan:
            if chan == 0:
                return np.random.random(n2read) * 0.04
            elif chan == 1:
                return np.random.random(n2read) * 0.04 + 0.1
            elif chan == 2:
                now = time.monotonic()
                t0 = now - self.start
                ticks = 1 / self.sample_rate
                t = np.linspace(t0, t0+n2read*ticks, n2read)
                return np.sin(4 * np.pi * t) * 4
            else:
                return 0.0
        else:
            raise IndexError(f'Channel number {chan} is out of range 0-{self.n_chan}')

    def readAvgFrom(self, chan: int, n2avg: int) -> float:
        if 0 <= chan and chan < self.n_chan:
            if chan == 0:
                return np.random.random() * 0.04
            elif chan == 1:
                return np.random.random() * 0.04 + 0.1
            elif chan == 2:
                now = time.monotonic()
                t = now - self.start
                return np.sin(4 * np.pi * t) * 4
            else:
                return 0.0
        else:
            raise IndexError(f'Channel number {chan} is out of range 0-{self.n_chan} in readAvgFrom')
    
    # Sim but do all channels at once
    def readOne(self) -> np.ndarray:
        res = np.zeros(self.n_chan)
        res[0] = np.random.random() * 0.04
        res[1] = np.random.random() * 0.04
        now = time.monotonic()
        t0 = now - self.start
        res[2] = np.sin(4 * np.pi * t0) * 4
        return res
    
    def readN(self, n2read: int) -> np.ndarray:
        res = np.zeros((self.n_chan, n2read))
        res[0, :] = np.random.random(n2read) * 0.04
        res[1] = np.random.random(n2read) * 0.04
        now = time.monotonic()
        t0 = now - self.start
        ticks = 1 / self.sample_rate
        t = np.linspace(t0, t0+n2read*ticks, n2read)
        res[2] = np.sin(4 * np.pi * t) * 4
        return res

    def readAvg(self, chan: int, n2avg: int) -> float:
        res = np.zeros(self.n_chan)
        res[0] = np.random.random() * 0.04
        res[1] = np.random.random() * 0.04
        now = time.monotonic()
        t0 = now - self.start
        res[2] = np.sin(4 * np.pi * t0) * 4
        return res
