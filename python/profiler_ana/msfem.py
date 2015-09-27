#!/usr/bin/env python3
import logging
import sys
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import itertools

import pandas_common as pc

common_string = pc.common_substring(sys.argv[1:])
merged = 'merged_{}.csv'.format(common_string)
baseline_name = 'msfem.all'

header, current = pc.read_files(sys.argv[1:])
headerlist = header['profiler']
current = pc.sorted_f(current, False)
current = pc.speedup(headerlist, current, baseline_name)
# pprint(t_sections)
pc.plot_msfem(current, merged)
# try:
#     pc.plot_error(current, merged, ['msfem_exactH1s', 'msfem_exact_L2'],
#               'grids.macro_cells_per_dim',['$H^1_s$', '$L^2$', 'walltime'], baseline_name,
#               logy_base=10)
# except KeyError:
#     logging.error('No error data')
current.transpose().to_csv(merged)

def time_fit(x, a):
    return 1/(2**x)*a

def extrapolate(df, steps, fit, timings=None, measures=None):
    timings = timings or pc.TIMINGS
    measures = measures or pc.MEASURES
    col_ok = lambda x: [x.endswith(f) for f in itertools.product(timings, measures)].count(True)
    colnames = [colname for colname in df.columns if col_ok(colname)]
    # colnames = [colname for colname in df.columns]
    size = len(df['cores'])
    known_x = df['cores'].values
    new_x = np.array([known_x[-1] * (2**k) for k in range(1,steps+1)])
    concat_x = np.concatenate((known_x, new_x),axis=0)

    out = np.empty(shape=(concat_x.shape[0], len(colnames)), dtype=float) # Empty faster than zero

    # Return tuple of index and value
    for col_index in enumerate(colnames):
        known_y = df.iloc[:, col_index[0]]
        try:
            known_y = known_y.fillna(value=known_y.mean())
        except:
            # string data
            continue

        fitting_parameters, covariance = curve_fit(fit, known_x, known_y)
        a = fitting_parameters
        new_y = fit(new_x, a)
        #new_y = new_y[::-1] # Reverse projections

        concat_y = np.concatenate((known_y,new_y),axis=0)
        out[:, col_index[0]] = concat_y

    extended_df = pd.DataFrame(out)
    extended_df.columns = colnames

    return extended_df
hu = extrapolate(current, 2, time_fit)
# current.transpose().to_excel(merged+'.xls')
hu.transpose().to_csv('_proj_' + merged)
# pc.plot_msfem(hu,  merged)
