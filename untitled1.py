#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 14 19:09:19 2021

@author: colin
"""

from neuron import h, gui
from neuron.units import ms, mV
h.load_file('stdrun.hoc')

# Create generic cell class, but each cell records: its spike times, some membrane potential timeseries, and keep track of NetCons.

class Cell:
    def __init__(self, gid):
        self._gid = gid
        self._setup_morphology()
        self.all = self.soma.wholetree()
        self._setup_biophysics()
        h.define_shape()
        
        self._spike_detector = h.NetCon(self.axon(0.1)._ref_v, None, sec=self.axon)
        self.spike_times = h.Vector()
        self._spike_detector.record(self.spike_times)
        
        self._ncs = []
        
        self.soma_v = h.Vector().record(self.soma(0.5)._ref_v)
        self.axon_v_01 = h.Vector().record(self.axon(0.1)._ref_v)
        self.axon_v_05 = h.Vector().record(self.axon(0.5)._ref_v)
        self.axon_v_09 = h.Vector().record(self.axon(0.9)._ref_v)

    def __repr__(self):
        return '{}[{}]'.format(self.name, self._gid)


class BallAndStick(Cell):
    name = 'BallAndStick'
    
    def _setup_morphology(self):
        self.dend = h.Section(name= 'dendrite', cell=self)
        self.soma = h.Section(name='soma', cell=self)
        self.axon = h.Section(name='axon', cell=self)
        self.soma.connect(self.axon)
        self.soma.L = self.soma.diam = 100
        self.axon.diam = 75
        self.axon.L = 7500
        

    def _setup_biophysics(self):
        for sec in self.all:
            sec.Ra = 100    # Axial resistance in Ohm * cm
            sec.cm = 1      # Membrane capacitance in micro Farads / cm^2
        self.soma.insert('pas')                                          

        self.axon.insert('hh')                                          
        for seg in self.axon:
            seg.hh.gnabar = 0.12  # Sodium conductance in S/cm2
            seg.hh.gkbar = 0.036  # Potassium conductance in S/cm2
            seg.hh.gl = 0.0003    # Leak conductance in S/cm2
            seg.hh.el = -54.3     # Reversal potential in mV

# Setup single neuron feedback circuit with third output neuron.

# A---< C---<
# v  ^
# \__B

neuronA = BallAndStick(0)
neuronB = BallAndStick(1)
neuronC = BallAndStick(2)
    
# Add excitatory synapses from neuronA to neuronB. 
    
syn_excite_AB = h.Exp2Syn(neuronB.soma(0.5))
syn_excite_AB.e = 40 * mV
syn_excite_AB.tau1 = 1
syn_excite_AB.tau2 = 1
    
# Add excitatory synapses from neuronA to neuronC. 
    
syn_excite_AC = h.Exp2Syn(neuronC.soma(0.5))
syn_excite_AC.e = 40 * mV
syn_excite_AC.tau1 = 1
syn_excite_AC.tau2 = 1
    
# Netcon neuronA to neuronB.
    
netcon_AB = h.NetCon(neuronA.axon(0.9)._ref_v, syn_excite_AB, sec=neuronA.axon)
netcon_AB.delay = 1 * ms
netcon_AB.weight[0] = 5
netcon_AB.threshold = 0
    
# Netcon neuronA to neuronC.
    
netcon_AC = h.NetCon(neuronA.axon(0.9)._ref_v, syn_excite_AC, sec=neuronA.axon)
netcon_AC.delay = 1 * ms
netcon_AC.weight[0] = 5
netcon_AC.threshold = 0
    
# Run through experimental paradigm with no inhibitory synaptic connection.

import matplotlib.pyplot as plt
for i in [150,200,250]:   
    
    # Add stimulus current to neuronA soma.
    
    iclamp = h.IClamp(neuronA.soma(0.5))
    iclamp.delay = 10
    iclamp.dur = 90 * ms
    iclamp.amp = i
        
    t = h.Vector().record(h._ref_t)
    h.finitialize(-65 * mV)
    h.continuerun(100)
    
    print("Current:",i,", No inhibitory synapse")
    print("")
    plt.plot(t, neuronA.axon_v_01)
    plt.xlabel('t (ms)')
    plt.ylabel('v (mV)')
    plt.title('Neuron A Voltage Plot')
    plt.show()
    
    plt.plot(t, neuronB.axon_v_09)
    plt.xlabel('t (ms)')
    plt.ylabel('v (mV)')
    plt.title('Neuron B Voltage Plot')
    plt.show()
    
    plt.plot(t, neuronC.axon_v_01)
    plt.xlabel('t (ms)')
    plt.ylim([-90, 50])
    plt.ylabel('v (mV)')
    plt.title('Neuron C Voltage Plot')
    plt.show()
    
    plt.figure()
    plt.title('Spike Raster Plot for neuron A (1.0), neuron B (2.0) and neuron C (3.0)')
    plt.vlines(neuronA.spike_times, 0.5, 1.5)
    plt.vlines(neuronB.spike_times, 1.5, 2.5)
    plt.vlines(neuronC.spike_times, 2.5, 3.5)
    plt.show()

# Run through all experimental paradigms and print plots.

for i in [150,200,250]:
    for j in [neuronA.soma(0.5),neuronA.axon(0.3),neuronA.axon(0.7)]:

        # Add inhibitory synapses from neuronB to neuronA. 
        
        syn_inhibit_BA = h.Exp2Syn(j)
        syn_inhibit_BA.e = -65 * mV
        syn_inhibit_BA.tau1 = 2
        syn_inhibit_BA.tau2 = 2
    
        # Netcon neuronB to neuronA.
        
        netcon_BA = h.NetCon(neuronB.axon(0.9)._ref_v, syn_inhibit_BA, sec=neuronB.axon)
        netcon_BA.delay = 1 * ms
        netcon_BA.weight[0] = 1000
    
        # Record inhibitory synaptic current.
        
        syn_inhibit_BA_i = h.Vector().record(syn_inhibit_BA._ref_i)
        
        t = h.Vector().record(h._ref_t)
        h.finitialize(-65 * mV)
        h.continuerun(100)
        
        # Print voltage, current and spike raster plots.
        
        print("")
        print("Current:",i,", Inhibitory synapse location:",j)
        print("")
        plt.plot(t, neuronA.axon_v_01)
        plt.xlabel('t (ms)')
        plt.ylabel('v (mV)')
        plt.title('Neuron A Voltage Plot')
        plt.show()
        
        plt.plot(t, neuronB.axon_v_09)
        plt.xlabel('t (ms)')
        plt.ylabel('v (mV)')
        plt.title('Neuron B Voltage Plot')
        plt.show()
        
        plt.plot(t, neuronC.axon_v_01)
        plt.xlabel('t (ms)')
        plt.ylim([-90, 50])
        plt.ylabel('v (mV)')
        plt.title('Neuron C Voltage Plot')
        plt.show()
        
        plt.plot(t, syn_inhibit_BA_i)
        plt.xlabel('t (ms)')
        plt.ylabel('Current (nA)')
        plt.title('Inhibitory Synapse Current')
        plt.show()
        
        plt.figure()
        plt.title('Spike Raster Plot for neuron A (1.0), neuron B (2.0) and neuron C (3.0)')
        plt.vlines(neuronA.spike_times, 0.5, 1.5)
        plt.vlines(neuronB.spike_times, 1.5, 2.5)
        plt.vlines(neuronC.spike_times, 2.5, 3.5)
        plt.show()
    

