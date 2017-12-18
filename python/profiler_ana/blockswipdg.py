#!/usr/bin/env python3
import logging
import sys

import pandas_common as pc

common_string = pc.common_substring(sys.argv[1:])
merged = 'merged_{}.csv'.format(common_string)
method = 'block_ipdg'
baseline_name = '{}.all'.format(method)


def plot_block(current, filename_base, series_name=None, xcol=None):
    xcol = xcol or 'cores'
    series_name = series_name or 'speedup'
    categories = ['all', 'discretize', 'solve']
    ycols = ['{}.{}_avg_wall_{}'.format(method, v, series_name) for v in categories] + ['ideal_{}'.format(series_name)]
    bar_cols = ['{}.{}_avg_wall_abspart'.format(method, v) for v in categories[1:]]
    labels = ['Overall', 'Discretization', 'BiCGStab'] + ['Ideal']
    pc.plot_common(current, filename_base, ycols, labels,
                bar=(bar_cols,['Overall', 'Discretization', 'BiCGStab']), xcol=xcol,
                series_name=series_name)

def plot_block_eff(current, filename_base):
    xcol = 'cores'
    series_name = 'parallel_efficiency'
    categories = ['all', 'discretize', 'solve']
    ycols = ['{}.{}_avg_wall_{}'.format(method, v, series_name) for v in categories] + ['ideal_{}'.format(series_name)]
    bar_cols = ['{}.{}_avg_wall_abspart'.format(method, v) for v in categories[1:]]
    labels = ['Overall', 'Discretization', 'BiCGStab'] + ['Ideal']
    pc.plot_common(current, filename_base, ycols, labels,
                bar=(bar_cols,['Overall', 'Discretization', 'BiCGStab']), xcol=xcol,
                series_name=series_name)

header, current = pc.read_files(sys.argv[1:])
headerlist = header['profiler']
current = pc.sorted_f(current, True)
current = pc.speedup(headerlist, current, baseline_name)
# pprint(t_sections)
plot_block(current, merged)
plot_block(current, merged, series_name='parallel_efficiency')

current.transpose().to_csv(merged)
# current.transpose().to_excel(merged+'.xls')
# current.to_csv(merged)
