# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 16:22:58 2019

@author: cab1410
"""
import os
import pandas as pd
from matplotlib import pyplot as plt
# oemof imports
from oemof.network import Node
# solph imports
from oemof.solph import (EnergySystem, Model, Flow, Source, Sink, Bus,
                         RollingHorizon)
from oemof.outputlib import processing, views

# read sequence data
full_filename = os.path.join(os.path.dirname(__file__),
                             'data.csv')
data = pd.read_csv(full_filename, sep=",")

# select periods
periods = len(data)-1

# create an energy system
idx = pd.date_range('1/1/2017', periods=periods, freq='H')
es = EnergySystem(timeindex=idx)
Node.registry = es

# power bus and components
bel = Bus(label='bel')

demand_el = Sink(
    label='demand_el',
    inputs={bel: Flow(
        fixed=True, actual_value=data['demand_el'], nominal_value=10)})

pp1 = Source(
    label='power_plant1',
    outputs={bel: Flow(nominal_value=10, variable_costs=10.25)})

pp2 = Source(
    label='power_plant2',
    outputs={
        bel: Flow(
            nominal_value=10, min=0.5, max=1.0, variable_costs=5,
            rolllinghorizon=RollingHorizon(t_start_cold=5,
                                           t_start_warm=3,
                                           t_start_hot=1,
                                           cold_start_costs=5,
                                           warm_start_cost=4,
                                           hot_start_costs=1,
                                           shutdown_costs=2,
                                           optimized_status=data['operation_status']))})

# create an optimization problem and solve it
om = Model(es)

# debugging
# om.write('problem.lp', io_options={'symbolic_solver_labels': True})

# solve model
om.solve(solver='cplex', solve_kwargs={'tee': True})

# create result object
results = processing.results(om)

# plot data
if plt is not None:
    # plot electrical bus
    data = views.node(results, 'bel')['sequences']
    data[(('bel', 'demand_el'), 'flow')] *= -1
    columns = [c for c in data.columns
               if not any(s in c for s in ['status'])]
    data = data[columns]
    ax = data.plot(kind='line', drawstyle='steps-post', grid=True, rot=0)
    ax.set_xlabel('Hour')
    ax.set_ylabel('P (MW)')
    plt.show()
