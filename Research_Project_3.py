#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 26 17:36:49 2021

@author: colin
"""

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
        self._setup_biophysics()
        h.define_shape()
        
        self._spike_detector = h.NetCon(self.axon(0.1)._ref_v, None, sec=self.axon)
        self.spike_times = h.Vector()
        self._spike_detector.record(self.spike_times)
        
        self._ncs = []
        
        self.axon_v = h.Vector().record(self.axon(0.8)._ref_v)

    def __repr__(self):
        return '{}[{}]'.format(self.name, self._gid)



class BallAndStick(Cell):
    name = 'BallAndStick'
    
    def _setup_morphology(self):

        self.axon = h.Section(name='axon', cell=self)
        self.axon.L = 10000
        self.axon.diam = 100

    def _setup_biophysics(self):
        self.axon.Ra = 100    # Axial resistance in Ohm * cm
        self.axon.cm = 1      # Membrane capacitance in micro Farads / cm^2
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

# Add stimulus current to neuronA soma.
"""Change magnitude of stimulus current in section below!"""

iclamp = h.IClamp(neuronA.axon(0))
iclamp.delay = 10
iclamp.dur = 90 * ms
iclamp.amp = 250

# Add excitatory synapses from neuronA to neuronB. 

syn_excite_AB = h.Exp2Syn(neuronB.axon(0))
syn_excite_AB.e = 40 * mV
syn_excite_AB.tau1 = 1
syn_excite_AB.tau2 = 1

# Add inhibitory synapses from neuronB to neuronA. 
""" Change the location on axon on next line!"""

syn_inhibit_BA = h.Exp2Syn(neuronA.axon(0.8))
syn_inhibit_BA.e = -65 * mV
syn_inhibit_BA.tau1 = 2
syn_inhibit_BA.tau2 = 2

# Add excitatory synapses from neuronA to neuronC. 

syn_excite_AC = h.Exp2Syn(neuronC.axon(0))
syn_excite_AC.e = 40 * mV
syn_excite_AC.tau1 = 1
syn_excite_AC.tau2 = 1

# Netcon neuronA to neuronB.

netcon_AB = h.NetCon(neuronA.axon(1)._ref_v, syn_excite_AB, sec=neuronA.axon)
netcon_AB.delay = 2 * ms
netcon_AB.weight[0] = 20

# Netcon neuronB to neuronA.

netcon_BA = h.NetCon(neuronB.axon(1)._ref_v, syn_inhibit_BA, sec=neuronB.axon)
netcon_BA.delay = 2 * ms
netcon_BA.weight[0] = 100
netcon_BA.threshold = 0

# Netcon neuronA to neuronC.

netcon_AC = h.NetCon(neuronA.axon(1)._ref_v, syn_excite_AC, sec=neuronA.axon)
netcon_AC.delay = 2 * ms
netcon_AC.weight[0] = 100

# Record inhibitory synaptic current.
syn_inhibit_BA_i = h.Vector().record(syn_inhibit_BA._ref_i)

t = h.Vector().record(h._ref_t)
h.finitialize(-65 * mV)
h.continuerun(100)



import matplotlib.pyplot as plt
plt.plot(t, neuronA.axon_v)
plt.xlabel('t (ms)')
plt.ylabel('v (mV)')
plt.title('Cell[0] Voltage Plot')
plt.show()

plt.plot(t, neuronB.axon_v)
plt.xlabel('t (ms)')
plt.ylabel('v (mV)')
plt.title('Cell[1] Voltage Plot')
plt.show()

plt.plot(t, neuronC.axon_v)
plt.xlabel('t (ms)')
plt.ylabel('v (mV)')
plt.title('Cell[2] Voltage Plot')
plt.show()

plt.plot(t, syn_inhibit_BA_i)
plt.xlabel('t (ms)')
plt.ylabel('Current (nA)')
plt.title('Inhibitory Current')
plt.show()

plt.figure()
plt.vlines(neuronA.spike_times, 0.5, 1.5)
plt.vlines(neuronB.spike_times, 1.5, 2.5)
plt.vlines(neuronC.spike_times, 2.5, 3.5)
plt.show()

