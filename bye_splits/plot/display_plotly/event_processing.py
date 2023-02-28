_all_ = [ ]

import os
import pathlib
from pathlib import Path
import sys
parent_dir = os.path.abspath(__file__ + 3 * '/..')
sys.path.insert(0, parent_dir)

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

import data_handle
from data_handle.data_handle import EventDataParticle
from data_handle.geometry import GeometryData
from plot_event import produce_2dplot, produce_3dplot, plot_modules
from plotly.express.colors import sample_colorscale

import logging
log = logging.getLogger(__name__)

data_part_opt = dict(tag='v2', reprocess=False, debug=True, logger=log)
data_particle = {
    'photons': EventDataParticle(particles='photons', **data_part_opt),
    'electrons': EventDataParticle(particles='electrons', **data_part_opt),
    'pions': EventDataParticle(particles='pions', **data_part_opt)}
geom_data = GeometryData(inname='test_triggergeom.root',
                         reprocess=False, logger=log)

axis = dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="white", showbackground=True, zerolinecolor="white",)

def get_data(event, particles):
    ds_geom = geom_data.provide(library='plotly')

    if event is None:
    	event = data_particle[particles].provide_event_numbers()
    
    ds_ev = data_particle[particles].provide_event(event)
   
    ds_ev.rename(columns={'good_tc_waferu':'waferu', 'good_tc_waferv':'waferv',
                          'good_tc_cellu':'triggercellu', 'good_tc_cellv':'triggercellv',
                          'good_tc_layer':'layer', 'good_tc_mipPt':'mipPt',
                          'good_tc_energy':'energy', 'good_tc_cluster_id':'tc_cluster_id'},
                inplace=True)
    ds_ev = pd.merge(left=ds_ev, right=ds_geom, how='inner',
                     on=['layer', 'waferu', 'waferv', 'triggercellu', 'triggercellv'])

    color = sample_colorscale('viridis', (ds_ev.mipPt-ds_ev.mipPt.min())/(ds_ev.mipPt.max()-ds_ev.mipPt.min()))
    ds_ev = ds_ev.assign(colors=color)
    return ds_ev, event

def set_3dfigure(df):
    fig = go.Figure(produce_3dplot(df))
    
    fig.update_layout(autosize=False, width=1300, height=700,
                      scene_aspectmode='manual',
                      scene_aspectratio=dict(x=1, y=1, z=1),
                      scene=dict(xaxis=axis, yaxis=axis, zaxis=axis,
                                 xaxis_title="z [cm]",yaxis_title="y [cm]",zaxis_title="x [cm]",
                                 xaxis_showspikes=False,yaxis_showspikes=False,zaxis_showspikes=False),
                      showlegend=False,
                      margin=dict(l=0, r=0, t=10, b=10),
                      ) 

    return fig

def update_3dfigure(fig, df):
    list_scatter = produce_3dplot(df, opacity=.2)
    for index in range(len(list_scatter)):
        fig.add_trace(list_scatter[index])
    return fig

def add_ROI(fig, df, k=4):
    ''' Choose k-layers window based on energy deposited in each layer '''
    layer_sums = df.groupby(['layer']).mipPt.sum() 
    initial_layer = (layer_sums.rolling(window=k).sum().shift(-k+1)).idxmax()
    
    mask = (df.layer>=initial_layer) & (df.layer<(initial_layer+2*k))
    input_df = df[mask]
    
    ''' Choose the (u,v) coordinates of the module corresponding to max dep-energy.
    Extend the selection to the modules with at least 30% max energy and 10 mipT. '''
    module_sums = input_df.groupby(['waferu','waferv']).mipPt.sum()
    
    skim = (module_sums.values > 0.3 * module_sums.max()) & (module_sums.values > 10)
    skim_module_sums = module_sums[skim]
    
    roi_df = input_df[input_df.set_index(['waferu','waferv']).index.isin(skim_module_sums.index)]
    roi_df = roi_df.drop_duplicates(['waferu', 'waferv', 'layer'])

    list_scatter = plot_modules(roi_df)
    for index in range(len(list_scatter)):
        fig.add_trace(list_scatter[index])
    return fig

def set_2dfigure(df):
    fig = go.Figure(produce_2dplot(df))

    fig.update_layout(autosize=False, width=1300, height=700,
                      scene_aspectmode='manual',
                      scene_aspectratio=dict(x=1, y=1),
                      scene=dict(xaxis=axis, yaxis=axis, 
                                 xaxis_title="x [cm]",yaxis_title="y [cm]",
                                 xaxis_showspikes=False,yaxis_showspikes=False),
                      showlegend=False,
                      margin=dict(l=0, r=0, t=10, b=10),
                      )

    return fig

def update_2dfigure(fig, df):
    list_scatter = produce_2dplot(df, opacity=.2)
    for index in range(len(list_scatter)):
        fig.add_trace(list_scatter[index])
    return fig


tab_3d_layout = dbc.Container([html.Div([
    html.Div([
        html.Div([dcc.Dropdown(['photons', 'electrons', 'pions'], 'photons', id='particle')], style={'width':'15%'}),
        html.Div([dbc.Checklist(['Cluster trigger cells', 'ROI', 'Layer selection'], [], inline=True, id='checkbox', switch=True)], style={"margin-left": "15px"}),
        html.Div(id='slider-container', children=html.Div(id='out_slider', style={'width':'95%'}), style= {'display': 'block', 'width':'40%'}),
    ], style={'display': 'flex', 'flex-direction': 'row'}),

    html.Div([
        html.Div(["Threshold in [mip\u209C]: ", dcc.Input(id='mip', value=1, type='number', step=0.1)], style={'padding': 10}),
        html.Div(["Select manually an event: ", dcc.Input(id='event', value=None, type='number')], style={'padding': 10, 'flex': 1}),
    ], style={'display':'flex', 'flex-direction':'row'}),

    html.Div([
        dbc.Button(children='Random event', id='event-val', n_clicks=0),
        dbc.Button(children='Submit selected event', id='submit-val', n_clicks=0, style={'display':'inline-block', "margin-left": "15px"}),
        html.Div(id='event-display', style={'display':'inline-block', "margin-left": "15px"}),
    ]),
    dcc.Graph(id='graph'),
    dcc.Store(id='dataframe'),
    ]), ])

tab_layer_layout = dbc.Container([html.Div([
    html.Div([
        html.Div([dcc.Dropdown(['photons', 'electrons', 'pions'], 'photons', id='particle')], style={'width':'15%'}),
        html.Div([dcc.Dropdown(['trigger cells', 'cluster'], 'trigger cells', id='tc-cl')], style={"margin-left": "15px", 'width':'15%'}),
        html.Br(),
        html.Div(id='out_slider', style={'width':'40%'}),
        html.Div(id='layer_slider_container', style={'width':'30%'}),
    ], style={'display': 'flex', 'flex-direction': 'row'}),
    html.Div([
        html.Div(["Threshold in [MIP Pt]: ", dcc.Input(id='mip', value=1, type='number', step=0.1)], style={'padding': 10}),
        html.Div(["Select manually an event: ", dcc.Input(id='event', value=None, type='number')], style={'padding': 10, 'flex': 1}),
    ], style={'display': 'flex', 'flex-direction': 'row'}),
    html.Br(),
    html.Div([
        dbc.Button(children='Random event', id='event-val', n_clicks=0),
        dbc.Button(children='Submit selected event', id='submit-val', n_clicks=0),
        html.Div(id='event-display', style={'display':'inline-block', "margin-left": "15px"}),
        html.Div(id='which', style={'display':'inline-block', "margin-left": "15px"}),
    ]),
    dcc.Graph(id='graph2d'),
    dcc.Store(id='dataframe')]), ])
