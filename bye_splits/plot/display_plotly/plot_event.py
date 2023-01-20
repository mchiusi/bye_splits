# coding: utf-8

_all_ = [ 'EventData' ]

import os
from pathlib import Path
import sys
parent_dir = os.path.abspath(__file__ + 2 * '/..')
sys.path.insert(0, parent_dir)

import numpy as np
import pandas as pd
import plotly.graph_objects as go

def produce_3dplot(df, opacity=1, surfaceaxis=2):
    array_data = df[['diamond_x', 'diamond_y', 'z', 'tc_x', 'tc_y', 'colors','mipPt']].to_numpy()
    listdata = []
    for j,i in enumerate(array_data):
        x1 = np.append(i[0][0][0],i[0][0][0][0])
        y1 = np.append(i[1][0][0],i[1][0][0][0])
        z1 = np.array(int(len(x1)+1) * [i[2]])
        datum = go.Scatter3d(x=x1, y=y1, z=z1, opacity=opacity,mode="lines",
                            surfaceaxis=surfaceaxis,surfacecolor=i[5],marker=dict(color="black"),
                            text=('Energy: '+str(i[6]))
                            )
        listdata.append(datum)
    return listdata

def produce_2dplot(df, opacity=1):
    array_data = df[['diamond_x', 'diamond_y', 'tc_x', 'tc_y', 'colors','mipPt']].to_numpy()
    listdata = []
    for j,i in enumerate(array_data):
        x1 = np.append(i[0][0][0],i[0][0][0][0]) 
        y1 = np.append(i[1][0][0],i[1][0][0][0])
        datum = go.Scatter(x=x1, y=y1, opacity=opacity,mode="lines",fill='toself', fillcolor=i[4],
                          line_color='black',marker_line_color="black",  text=('Energy: '+str(i[5])))
        listdata.append(datum)

    return listdata
