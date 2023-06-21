# -*- coding: utf-8 -*-
"""
Created on Tue May  2 14:48:28 2023
Tests of the new ttimer module.

@author: pguest
"""
import ttimer

freq = float(ttimer.init())

print(ttimer.now())
print(ttimer.now())
print(ttimer.now())
print(ttimer.now())
print(ttimer.now())

t1 = ttimer.now()
t2 = ttimer.now()
t3 = ttimer.now()
t4 = ttimer.now()
t5 = ttimer.now()

print(t1, t2, t3, t4, t5)
