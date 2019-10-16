# -*- coding: utf-8 -*-

"""
General description
-------------------
This script shows how to do a linear optimal powerflow (lopf) calculation
based on custom oemof components. The example is based on the PyPSA
simple lopf example.

Note: As oemof currently does not support models with one timesteps, therefore
there are two.

Installation requirements
-------------------------
This example requires the version v0.3.x of oemof and matplotlib. Install by:

    pip install 'oemof>=0.3,<0.4'
    pip install matplotlib

12.12.2017 - simon.hilpert@uni-flensburg.de
"""

__copyright__ = "oemof developer group"
__license__ = "GPLv3"

import pandas as pd
import networkx as nx
from matplotlib import pyplot as plt

# solph imports
from oemof.solph import (EnergySystem, Model, Flow, Source, Sink, custom,
                         Investment)
from oemof.outputlib import processing, views
from oemof.graph import create_nx_graph


def draw_graph(grph, edge_labels=True, node_color='#AFAFAF',
               edge_color='#CFCFCF', plot=True, node_size=2000,
               with_labels=True, arrows=True, layout='neato'):
    """
    Draw a graph. This function will be removed in future versions.

    Parameters
    ----------
    grph : networkxGraph
        A graph to draw.
    edge_labels : boolean
        Use nominal values of flow as edge label
    node_color : dict or string
        Hex color code oder matplotlib color for each node. If string, all
        colors are the same.

    edge_color : string
        Hex color code oder matplotlib color for edge color.

    plot : boolean
        Show matplotlib plot.

    node_size : integer
        Size of nodes.

    with_labels : boolean
        Draw node labels.

    arrows : boolean
        Draw arrows on directed edges. Works only if an optimization_model has
        been passed.
    layout : string
        networkx graph layout, one of: neato, dot, twopi, circo, fdp, sfdp.
    """
    if type(node_color) is dict:
        node_color = [node_color.get(g, '#AFAFAF') for g in grph.nodes()]

    # set drawing options
    options = {
     'prog': 'dot',
     'with_labels': with_labels,
     'node_color': node_color,
     'edge_color': edge_color,
     'node_size': node_size,
     'arrows': arrows
    }

    # draw graph
    pos = nx.drawing.nx_agraph.graphviz_layout(grph, prog=layout)

    nx.draw(grph, pos=pos, **options)

    # add edge labels for all edges
    if edge_labels is True and plt:
        labels = nx.get_edge_attributes(grph, 'weight')
        nx.draw_networkx_edge_labels(grph, pos=pos, edge_labels=labels)

    # show output
    if plot is True:
        plt.show()


datetimeindex = pd.date_range('1/1/2017', periods=2, freq='H')

es = EnergySystem(timeindex=datetimeindex)

b_el0 = custom.ElectricalBus(label="b_0", v_min=-1, v_max=1)

b_el1 = custom.ElectricalBus(label="b_1", v_min=-1, v_max=1)

b_el2 = custom.ElectricalBus(label="b_2", v_min=-1, v_max=1)

es.add(b_el0, b_el1, b_el2)

es.add(custom.ElectricalLine(input=b_el0,
                             output=b_el1,
                             reactance=0.0001,
                             investment=Investment(ep_costs=10),
                             min=-1,
                             max=1
                        )
                    )

es.add(custom.ElectricalLine(input=b_el1,
                             output=b_el2,
                             reactance=0.0001,
                             nominal_value=60,
                             min=-1,
                             max=1
                        )
                    )

es.add(custom.ElectricalLine(input=b_el2,
                             output=b_el0,
                             reactance=0.0001,
                             nominal_value=60,
                             min=-1,
                             max=1
                        )
                    )

es.add(Source(label="gen_0", outputs={b_el0: Flow(nominal_value=100,
                                                  variable_costs=50)}))

es.add(Source(label="gen_1", outputs={b_el1: Flow(nominal_value=100,
                                                  variable_costs=25)}))

es.add(Sink(label="load", inputs={b_el2: Flow(nominal_value=100,
                                              actual_value=[1, 1],
                                              fixed=True)}))

m = Model(energysystem=es)

# m.write('lopf.lp', io_options={'symbolic_solver_labels': True})

m.solve(solver='cplex',
        solve_kwargs={'tee': True, 'keepfiles': False})


m.results()

#graph = create_nx_graph(es)
#
#draw_graph(graph, plot=True, layout='neato', node_size=3000,
#           node_color={
#                  'b_0': '#cd3333',
#                  'b_1': '#7EC0EE',
#                  'b_2': '#eeac7e'})


results = processing.results(m)

print(views.node(results, 'gen_0'))
print(views.node(results, 'gen_1'))
print(views.node(results, 'line_1'))
