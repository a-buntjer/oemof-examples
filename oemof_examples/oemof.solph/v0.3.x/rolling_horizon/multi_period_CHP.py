# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 08:42:07 2019

@author: cab1410
"""

import os
import pandas as pd
from matplotlib import pyplot as plt
# oemof imports
from oemof.network import Node
# solph imports
from oemof.solph import (EnergySystem, MultiPeriodModel, Flow, Source, Sink,
                         Bus, RollingHorizon)
from oemof.solph.components import (GenericCHP, GenericStorage)
from oemof.outputlib import processing, views
from time import time
# read sequence data
full_filename = os.path.join(os.path.dirname(__file__),
                             'data.csv')
data = pd.read_csv(full_filename, sep=";")

# select total_time_steps
total_time_steps = 24*7

# create an energy system
idx = pd.date_range('1/1/2017', periods=total_time_steps, freq='H')
start = time()
es = EnergySystem(timeindex=idx)
Node.registry = es

# resources
bgas = Bus(label='bgas')

rgas = Source(label='rgas', outputs={bgas: Flow()})

# heat
bth = Bus(label='bth')

# dummy source at high costs that serves the residual load
source_th = Source(label='source_th',
                         outputs={bth: Flow(variable_costs=1000)})

demand_th = Sink(label='demand_th', inputs={bth: Flow(fixed=True,
                 actual_value=data['demand_th'], nominal_value=200)})

# power bus and components
bel = Bus(label='bel')

demand_el = Sink(
    label='demand_el',
    inputs={bel: Flow(
        fixed=True, actual_value=data['demand_el'], nominal_value=100)})

pp1 = Source(
    label='power_plant1',
    outputs={bel: Flow(nominal_value=300, variable_costs=10.25)})

pp2 = Source(
    label='power_plant2',
    outputs={
        bel: Flow(
            nominal_value=150, min=0.6, max=1.0, variable_costs=5,
            rollinghorizon=RollingHorizon(t_start_cold=5,
                                          t_start_warm=3,
                                          t_start_hot=1,
                                          cold_start_costs=5,
                                          warm_start_costs=4,
                                          hot_start_costs=1,
                                          minimum_downtime=1,
                                          ramp_limit_up=0.3,
                                          ramp_limit_down=0.4))})

# combined cycle extraction turbine
ccet = GenericCHP(
    label='combined_cycle_extraction_turbine',
    fuel_input={bgas: Flow(
        H_L_FG_share_max=[0.19 for p in range(0, total_time_steps)])},
    electrical_output={bel: Flow(
        nominal_value=200, variable_costs=5,
        P_max_woDH=[200 for p in range(0, total_time_steps)],
        P_min_woDH=[80 for p in range(0, total_time_steps)],
        Eta_el_max_woDH=[0.53 for p in range(0, total_time_steps)],
        Eta_el_min_woDH=[0.43 for p in range(0, total_time_steps)],
        rollinghorizon=RollingHorizon(t_start_cold=5,
                                      t_start_warm=3,
                                      t_start_hot=1,
                                      cold_start_costs=5,
                                      warm_start_costs=4,
                                      hot_start_costs=1,
                                      minimum_downtime=1,
                                      ramp_limit_up=3,
                                      ramp_limit_down=4))},
    heat_output={bth: Flow(
        Q_CW_min=[30 for p in range(0, total_time_steps)])},
    Beta=[0.19 for p in range(0, total_time_steps)],
    back_pressure=False)

stor = GenericStorage(
            label='Storage0',
            nominal_storage_capacity=100,
            inputs={bel: Flow()},
            outputs={bel: Flow()},
            initial_storage_level=0,
            balanced=False)

print(f'Time for es creation: {time()-start}')
start = time()
om = MultiPeriodModel(es, interval_length=48, period=24)
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
                   if not any(s in str(c) for s in ['status', 'costs'])]
        result_data = result_data[columns]
        ax = result_data.plot(kind='line', drawstyle='steps-post',
                              grid=True, rot=0)
        ax.set_xlabel('Hour')
        ax.set_ylabel('P (MW)')
        plt.show()

        result_data = views.node(results, 'bth')['sequences']
        result_data[(('bth', 'demand_th'), 'flow')] *= -1
        columns = [c for c in result_data.columns
                   if not any(s in str(c) for s in ['status', 'costs'])]
        result_data = result_data[columns]
        ax = result_data.plot(kind='line', drawstyle='steps-post',
                              grid=True, rot=0)
        ax.set_xlabel('Hour')
        ax.set_ylabel('Q (MW)')
        plt.show()

        return result_data

plotted_results = plot_results(om.multiperiod_results)
