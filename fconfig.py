#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fconfig.py
Faraday
This implements a TOML configuration file for the FieldMapper.
FConfig holds dictionaries of configuration values that can be accessed
by the application. It is intended that all potentially alterable
configuration be stored in here.
Created on Tue Aug 16 11:40:48 2022
@author: bcollett
"""
import toml

class FConfig:
    def __init__(self):
        # inputs section
        self._inDict = {'InDev': 'Dev2'}
        self._inDict['test'] = 'testing'
        self._inDict['V1Chan'] = 'ai0'
        self._inDict['V2Chan'] = 'ai1'
        self._inDict['VMChan'] = 'ai2'
        self._inDict['SampleRate'] = 10_000
        self._inDict['LiveDuration'] = 10.0
        self._inDict['UpdateRate'] = 10.0
        self._inDict['NAverage'] = 10.0
        self._inDict['LXLimit'] = 0
        self._inDict['RXLimit'] = 0

        # outputs section
        self._outDict = {'OutDev': 'Dev1'}
        # graphics section
        self._graphDict = {}
        self._graphDict['GraphWidth'] = 900
        self._graphDict['GraphHeight'] = 800
        self._graphDict['UpdateRate'] = 10.0
        # main section
        self._config = {'inputs': self._inDict}
        self._config['outputs'] = self._outDict
        self._config['graphing'] = self._graphDict
        self._config['MainXPos'] = 50
        self._config['MainYPos'] = 100
        self._config['MainWidth'] = 250
        self._config['MainHeight'] = 800

    def get(self, key):
        return self._config[key]

    def inputs_get(self, key):
        #print(self._config['inputs'])
        #print(self._config['inputs'][key])
        return self._config['inputs'][key]

    def outputs_get(self, key):
        return self._config['outputs'][key]

    def graphs_get(self, key):
        return self._config['graphing'][key]

    def set(self, key, value):
        self._config[key] = value

    def inputs_set(self, key, value):
        #  print(key, self._inDict[key])
        self._config['inputs'][key] = value
#        print(key, self._inDict[key])
#        print('inputs_set _indict=', self._inDict)

    def outputs_set(self, key, value):
        self._config['outputs'][key] = value

    def graphs_set(self, key, value):
        self._config['graphing'][key] = value

    def __str__(self):
        return "Faraday Config"

    #
    #   Write configuration out as a json file.
    #
    def saveOn(self, filename: str='Faraday.toml') -> bool:
        if not isinstance(filename, str):
            raise RuntimeError('Config filename must be a string.')
        if not filename.endswith('.toml'):
            raise RuntimeError('Config filename must end in ".toml".')
        with open(filename, 'w') as f:
            toml.dump(self._config, f)
        return True
    #
    #   Read configuration from a json file.
    #

    def loadFrom(self, filename: str='Faraday.toml') -> bool:
        if not isinstance(filename, str):
            raise RuntimeError('Config filename must be a string.')
        if not filename.endswith('.toml'):
            raise RuntimeError('Config filename must end in ".toml".')
        with open(filename, 'r') as f:
            self._config = toml.load(f)
#            self._mapDict = self._config['mapper']
#            self._probeDict = self._config['probe']
        print('In fconfig loadFrom')
        print(self._config)
        print(self.inputs_get('InDev'))
        return True


if __name__ == '__main__':
    d = FConfig()
    print('d =', d)
    print(d._config)
    d.loadFrom('Faraday.toml')
#    print('d =', d)
    d.saveOn('Ftest.toml')
