"""
__author__ = Hagai Hargil
"""
import pandas as pd
import numpy as np
import re
from bokeh.plotting import output_file, show, figure
from bokeh.models import Div, ColumnDataSource
from bokeh.layouts import gridplot, column
from bokeh.charts import TimeSeries


def process_ep_output(dict_of_data, list_of_wanted):

    cols = ['Measure', 'Mouse Number', 'FOV', 'Hemisphere', 'Data']
    df = pd.DataFrame([], columns=cols)
    keys = np.array(list(dict_of_data.keys()), dtype=str)
    fov = re.compile(r'FOV_(\d)')
    mouse_num = re.compile(r'^(\d+)_data')

    for key in list_of_wanted:
        indices = np.core.defchararray.find(keys, key)
        rel_keys = keys[indices >= 0]
        for rel_key in rel_keys:
            # Find the key values of the specific entry
            num = mouse_num.findall(rel_key)[0]
            cur_fov = fov.findall(rel_key)[0]
            hemi = 'Hyper' if 'HYPER' in rel_key else 'Hypo'
            helper = pd.DataFrame([[key, num, cur_fov, hemi, dict_of_data[rel_key]]], columns=cols)
            df = df.append(helper, ignore_index=True)

    df.set_index(['Measure', 'Mouse Number', 'FOV', 'Hemisphere'], drop=True, inplace=True)

    return df

def plot_all_ca_traces(df):
    """ Take a dataframe of calcium traces from EP and plot it """

    list_of_figures = []
    output_file(r"C:\Users\Hagai\Documents\GitHub\EP-analysis\all_calcium_traces.html",
                title="Calcium Analysis")


    xdata = np.arange(df.shape[0])

    ts = TimeSeries(data=df, x=xdata, title="Calcium Traces")
    show(ts)
    # for data_name in df.columns:
    #     cur_fig = figure(title=data_name)
    #     cur_data = df[data_name]
    #     source = ColumnDataSource(cur_data)
    #
    #     ts = TimeSeries()
