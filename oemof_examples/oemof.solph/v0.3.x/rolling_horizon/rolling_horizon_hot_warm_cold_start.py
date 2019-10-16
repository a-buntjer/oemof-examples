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
from time import time
# read sequence data
full_filename = os.path.join(os.path.dirname(__file__),
                             'data.csv')
data = pd.read_csv(full_filename, sep=";")

# select periods
periods = 24
total_time_steps = 8760

# create an energy system
idx = pd.date_range('1/1/2017', periods=total_time_steps, freq='H')
start = time()
es = EnergySystem(timeindex=idx[:periods])
Node.registry = es

# power bus and components
bel = Bus(label='bel')

demand_el = Sink(
    label='demand_el',
    inputs={bel: Flow(
        fixed=True, actual_value=data['demand_el'], nominal_value=10)})

pp1 = Source(
    label='power_plant1',
    outputs={bel: Flow(nominal_value=25, variable_costs=10.25)})

pp2 = Source(
    label='power_plant2',
    outputs={
        bel: Flow(
            nominal_value=10, min=0.2, max=1.0, variable_costs=5,
            rollinghorizon=RollingHorizon(t_start_cold=5,
                                          t_start_warm=3,
                                          t_start_hot=1,
                                          cold_start_costs=5,
                                          warm_start_costs=4,
                                          hot_start_costs=1,
                                          flow_min_last=0.3,
                                          minimum_downtime=1,
                                          T_int=periods-1))})

print(f'Time for es creation: {time()-start}')
# create an optimization problem and solve it
start = time()
total_optimization_period = [x for x in range(24, 8760, periods)]
for T in total_optimization_period:
    om = Model(es)
    om.solve(solver='cplex', solve_kwargs={'tee': True})
    for (i, o) in om.FLOWS:
        for t in om.TIMESTEPS:
            if om.flows[i, o].actual_value[t] is not None:
                # pre- optimized value of flow variable
                om.flows[i, o].actual_value[t] = data.loc[T+t, 'demand_el']
                om.flow[i, o, t].value = (
                    om.flows[i, o].actual_value[t] *
                    om.flows[i, o].nominal_value)
                # fix variable if flow is fixed
                if om.flows[i, o].fixed:
                    om.flow[i, o, t].fix()
        if om.flows[i, o].rollinghorizon:
            om.flows[i, o].rollinghorizon.T = T
            om.flows[i, o].rollinghorizon.optimized_status[T-periods:T] = list(om.RollingHorizonFlow.status[i, o, :]())
    es.timeindex = idx[T-periods:T]
print(f'Time for om creation: {time()-start:.6f}')


# debugging
# om.write('problem.lp', io_options={'symbolic_solver_labels': True})

# solve model
#om.solve(solver='cplex', solve_kwargs={'tee': True})

# create result object
#results = processing.results(om)
#
## plot result_data
#if plt is not None:
#    # plot electrical bus
#    result_data = views.node(results, 'bel')['sequences']
#    result_data[(('bel', 'demand_el'), 'flow')] *= -1
#    columns = [c for c in result_data.columns
#               if not any(s in c for s in ['status'])]
#    result_data = result_data[columns]
#    ax = result_data.plot(kind='line', drawstyle='steps-post', grid=True, rot=0)
#    ax.set_xlabel('Hour')
#    ax.set_ylabel('P (MW)')
#    plt.show()
