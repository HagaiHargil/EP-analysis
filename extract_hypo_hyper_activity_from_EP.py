"""
__author__ = Hagai Hargil
"""
import scipy
import h5py
import csv
import glob
import pathlib
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy import stats
from typing import Dict, List
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import warnings
from collections import deque


def multipage(filename, figs=None, dpi=200):
    pp = PdfPages(filename)
    if figs is None:
        figs = [plt.figure(n) for n in plt.get_fignums()]
    for fig in figs:
        fig.savefig(pp, format='pdf')
    pp.close()


def add_column_headers(sheet, heads: List):
    """ Take a sheet and add the header row """

    sheet.insert_row(heads, 1)


def add_row_headers(sheet, heads: List):
    """ Take a sheet and add the first column """

    cell_list = sheet.range(f'A2:A{2 + len(heads) - 1}')
    for idx, cell in enumerate(cell_list):
        cell.value = heads[idx]

    sheet.update_cells(cell_list)


def write_dict_to_gsheet(data: Dict, sheet, row: str):
    """
    Write the data dict into a Google sheet
    :return: None
    """
    headers: List = sheet.row_values(1)
    if [] == headers:
        raise UserWarning("Missing header row")

    try:
        row_idx = sheet.find(row)
    except CellNotFound:
        raise UserWarning(f"Missing row key {row}.")

    for key, item in data.items():
        print(key, item)
        try:
            col_idx = sheet.find(key)
        except CellNotFound:
            warnings.warn(f"Key {key} was missing.")
        sheet.update_cell(row_idx.row, col_idx.col, item)


def write_all_data_to_gsheet(data: Dict, sheetname="Sheet1",
                             scope='https://spreadsheets.google.com/feeds',
                             json_filename='client_secret.json',
                             spreadsheet_name="Hypo_Hyper_from_EP"):
    """
    Write the data dict into a Google sheet
    :return: None
    """
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_filename, scope)
    client = gspread.authorize(creds)
    try:  # if the worksheet already exists
        sheet = client.open(spreadsheet_name).add_worksheet(sheetname, rows=100, cols=30)
    except:
        sheet = client.open(spreadsheet_name).worksheet(sheetname)

    col_heads = deque(list(data.values())[0].keys())
    col_heads.appendleft(0)
    row_heads = list(data.keys())
    add_column_headers(sheet=sheet, heads=col_heads)
    add_row_headers(sheet=sheet, heads=row_heads)

    for key, dict_data in data.items():
        write_dict_to_gsheet(data=dict_data, sheet=sheet, row=key)


dict_of_data: Dict = {}
list_of_wanted = ['S_or_run_stim', 'S_or_run_spont', 'S_or_run_juxta',
                  'S_or_stand_stim', 'S_or_stand_spont', 'S_or_stand_juxta',
                  'C_df_run_stim', 'C_df_run_spont', 'C_df_run_juxta',
                  'C_df_stand_stim', 'C_df_stand_spont', 'C_df_stand_juxta']

directory = r'X:\David\7mm_win_thy1\results'

# Find *_with_compiled.mat and load it into memory
for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith("compiled.mat"):
            data = h5py.File(os.path.join(root, file), 'r')
            print(os.path.join(root, file))
            for name, vars_ in data.items():
                if name == 'compiled':
                    for name in vars_:
                        if name in list_of_wanted:
                            if "HYPO" in root:
                                key_of_dict = file + name + "HYPO"
                            if "HYPER" in root:
                                key_of_dict = file + name + "HYPER"
                            dict_of_data[key_of_dict] = vars_.get(name).value
                            # with open((root + file + name + '.csv'), 'wb') as f:
                            #     np.savetxt(f, vars_.get(name).value, delimiter=',')

# Process data
dict_of_std_hypo = {key: np.array([]) for key in list_of_wanted}
dict_of_averages_hypo = {key: np.array([]) for key in list_of_wanted}
dict_of_std_hyper = {key: np.array([]) for key in list_of_wanted}
dict_of_averages_hyper = {key: np.array([]) for key in list_of_wanted}

for key in sorted(dict_of_data):
    for key2 in sorted(dict_of_averages_hypo):
        if key2 in key:
            average = np.mean(dict_of_data[key])
            if "HYPO" in key:
                dict_of_averages_hypo[key2] = np.append(dict_of_averages_hypo[key2], average)
            else:
                dict_of_averages_hyper[key2] = np.append(dict_of_averages_hyper[key2], average)

hypo_mean: Dict = {}
hypo_std: Dict = {}
hyper_mean: Dict = {}
hyper_std: Dict = {}

for key in sorted(dict_of_averages_hyper):
    plt.figure()
    last_ind = len(dict_of_averages_hyper[key]) if len(dict_of_averages_hyper[key]) < len(dict_of_averages_hypo[key]) \
        else len(dict_of_averages_hypo[key])
    _, pval = stats.ttest_ind(dict_of_averages_hypo[key], dict_of_averages_hyper[key],
                              equal_var=False)
    plt.title(f"{key}, p-value (Welch): {pval:.3f}")
    ###
    np.save(arr=dict_of_averages_hyper, file='avg_hyper.npy')
    np.save(arr=dict_of_averages_hypo, file='avg_hypo.npy')
    ###

    hypo_std[key] = np.std(dict_of_averages_hypo[key])
    hypo_mean[key] = np.mean(dict_of_averages_hypo[key])
    hyper_std[key] = np.std(dict_of_averages_hyper[key])
    hyper_mean[key] = np.mean(dict_of_averages_hyper[key])
    plt.errorbar(np.arange(2), [hypo_mean[key], hyper_mean[key]],
                 yerr=[hypo_std[key], hyper_std[key]], fmt='o')
    labels = ['Hypo', 'Hyper']
    plt.xticks(np.arange(2), labels)

# Write to a Google sheet
dict_of_data = {'hypo_mean': hypo_mean,
                'hypo_std': hypo_std,
                'hyper_mean': hyper_mean,
                'hyper_std': hyper_std}
write_all_data_to_gsheet(data=dict_of_data, sheetname="Rotated Mice2")

# Save figures to a single PDF
# multipage('hypo_hyper_mean_std_with_Welch_t_test.pdf')
