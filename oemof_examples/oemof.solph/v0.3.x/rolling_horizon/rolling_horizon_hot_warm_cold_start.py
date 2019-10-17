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
from oemof.solph import (EnergySystem, MultiPeriodModel, Flow, Source, Sink, Bus,
                         RollingHorizon)
from oemof.outputlib import processing, views
from time import time
# read sequence data
full_filename = os.path.join(os.path.dirname(__file__),
                             'data.csv')
data = pd.read_csv(full_filename, sep=";")

# select periods
total_time_steps = 24*7

# create an energy system
idx = pd.date_range('1/1/2017', periods=total_time_steps, freq='H')
start = time()
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
    outputs={bel: Flow(nominal_value=35, variable_costs=10.25)})

pp2 = Source(
    label='power_plant2',
    outputs={
        bel: Flow(
            nominal_value=10, min=0.6, max=1.0, variable_costs=5,
            rollinghorizon=RollingHorizon(t_start_cold=5,
                                          t_start_warm=3,
                                          t_start_hot=1,
                                          cold_start_costs=5,
                                          warm_start_costs=4,
                                          hot_start_costs=1,
                                          minimum_downtime=1))})

print(f'Time for es creation: {time()-start}')
start = time()
om = MultiPeriodModel(es, interval_length=24)
print(f'Time for model creation: {time()-start:.6f}')
# create an optimization problem and solve it
start = time()
om.solve(solver='cplex', solve_kwargs={'tee': True})
print(f'Time for solving: {time()-start:.6f}')
if plt is not None:
    def plot_results(results):
        # plot electrical bus

        result_data = views.node(results, 'bel')['sequences']
        result_data[(('bel', 'demand_el'), 'flow')] *= -1
        columns = [c for c in result_data.columns
                   if not any(s in c for s in ['status'])]
        result_data = result_data[columns]
        ax = result_data.plot(kind='line', drawstyle='steps-post',
                              grid=True, rot=0)
        ax.set_xlabel('Hour')
        ax.set_ylabel('P (MW)')
        plt.show()
        return result_data

plotted_results = plot_results(om.multiperiod_results)
