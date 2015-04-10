#!/usr/bin/env python3

import os
import sys
import itertools
import matplotlib as mpl

import pandas_common as pc

def plot_mlmc(current, filename_base):
    categories = ['all']
    ycols = ['mlmc.{}_avg_wall_speedup'.format(v) for v in categories] + ['ideal_speedup']
    labels = ['Actual', 'Ideal']
    cm = mpl.colors.ListedColormap([(1,0,0), (0,0,0)], 'indexed')
    pc.plot_common(current, filename_base, ycols, labels, color_map=cm)

common_string = pc.common_substring(sys.argv[1:])
merged = 'merged_{}.csv'.format(common_string)
baseline_name = 'mlmc.all'

header, current = pc.read_files(sys.argv[1:])
headerlist = header['profiler']
current = pc.sorted_f(current, True)
# full = pc.speedup(headerlist, current.copy(), baseline_name)
# full.transpose().to_csv(merged)

cols = [c for c in current.columns.values if c.startswith(baseline_name) and 'mix' not in c]
cols = cols + ['{}_{}'.format(c,p) for c,p in itertools.product(cols, ['abspart', 'speedup'])]
current = pc.speedup(headerlist, current, baseline_name)
current = current.loc[:, pc.SPECIALS + cols + ['ideal_speedup']]
# pprint(t_sections)
plot_mlmc(current, merged)

current.transpose().to_csv('filtered_' + merged)
