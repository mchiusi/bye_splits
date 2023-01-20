# coding: utf-8

_all_ = [ ]

import os
from pathlib import Path
import sys
parent_dir = os.path.abspath(__file__ + 2 * '/..')
sys.path.insert(0, parent_dir)

from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import argparse

import numpy as np
import pandas as pd
import event_processing as processing

parser = argparse.ArgumentParser()
parser.add_argument('-id','--username',type=str,default=os.getlogin())
args = parser.parse_args()

app = Dash(__name__)
app.title = '3D Visualization' 
app.config['suppress_callback_exceptions'] = True

app.layout = html.Div([
    html.Div([
        html.Div([dcc.Dropdown(['3D view', 'Layer view'], '3D view', id='page')], style={'width':'15%'}),
    ], style={'display': 'flex', 'flex-direction': 'row'}),
    html.Div(id='page-content')
    ])

@app.callback(Output('page-content', 'children'),
              [Input('page', 'value')])
def render_content(page = '3D view'):
    if page == '3D view':
        return processing.tab_3d_layout
    elif page == 'Layer view':
        return processing.tab_layer_layout

@app.callback([Output('graph3d', 'figure'), Output('event-display', 'children')],
              [Input('particle', 'value'),  Input('tc-cl', 'value'),             Input('event-val', 'n_clicks'),
               Input('mip', 'value'),       Input('event', 'value')])
def update_event(particle, cluster, n_clicks, mip, event):
    df, event  = processing.get_data(event, particle)
    df = df.loc[df.mipPt >= mip]

    if cluster == 'cluster':
        df_no_cluster = df.loc[df.tc_cluster_id == 0]
        df_cluster    = df.loc[df.tc_cluster_id != 0]
        fig = processing.set_3dfigure(df_cluster)
        fig = processing.update_3dfigure(fig, df_no_cluster)
    else:
        fig = processing.set_3dfigure(df)
    return fig, u'Event {} displayed'.format(event)


@app.callback(Output('event_display_out', 'children'), Output('out_slider', 'children'), Output('dataframe', 'data'),
    Input('particle', 'value'), Input('tc-cl', 'value'), Input('event-val', 'n_clicks'), Input('mip', 'value'),
    Input('event', 'value'), Input('page', 'value') )
def update_event(particle, cluster, n_clicks, mip, event, page):
    df, event  = processing.get_data(event, particle)
    df = df.loc[df.mipPt >= mip]

    if page == 'Layer view':
    	slider = dcc.Slider(df['layer'].min(),df['layer'].max(), value=df['layer'].min(), step=None,
	                   marks={int(layer) : {"label": str(layer)} for each, layer in enumerate(sorted(df['layer'].unique()))}, 
                           id = 'slider-range', included=False)
    	return u'Event {} selected'.format(event), slider, df.reset_index().to_json(date_format='iso')
    raise PreventUpdate

@app.callback(Output('graph', 'figure'), Output('which', 'children'), 
    [Input('page', 'value'), Input('dataframe', 'data'), Input('slider-range', 'value'),
    Input('particle', 'value'), Input('tc-cl', 'value'), Input('mip', 'value')])
def update_output(page, data, slider_value, particle, cluster, mip):
    df = pd.read_json(data, orient='records')
    df_layer = df[df.layer == slider_value]

    if page == 'Layer view':
        if cluster == 'cluster':
            df_no_cluster = df_layer.loc[df_layer.tc_cluster_id == 0]
            df_cluster    = df_layer.loc[df_layer.tc_cluster_id != 0]
            fig = processing.set_2dfigure(df_cluster)
            fig = processing.update_2dfigure(fig, df_no_cluster)
        else:
            fig = processing.set_2dfigure(df_layer)
        return fig, u'Layer {} displayed'.format(slider_value) 
    raise PreventUpdate

if __name__ == '__main__':
    app.run_server(debug=True,
                   host='llruicms01.in2p3.fr',
                   port=8004)
