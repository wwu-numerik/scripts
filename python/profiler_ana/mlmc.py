#!/usr/bin/env python3

import os
import sys
import itertools

import pandas_common as pc

# pd.options.display.mpl_style = 'default'
first = sys.argv[1]
mg = os.path.basename(first)
merged = 'merged_{}.csv'.format(''.join(mg[:-4]))

baseline_name = 'mlmc.all'

headerlist, current = pc.read_files(sys.argv[1:])
current = pc.sorted_f(current, True)
cols = [c for c in current.columns.values if c.startswith(baseline_name) and 'mix' not in c]
cols = cols + ['{}_{}'.format(c,p) for c,p in itertools.product(cols, ['abspart', 'speedup'])]
print(cols)
current = pc.speedup(headerlist, current, baseline_name)
print(current.columns.values)
current = current.loc[:, pc.SPECIALS + cols + ['ideal_speedup']]
# pprint(t_sections)
current.transpose().to_csv(merged)

def plot_mlmc(current, filename_base):
    categories = ['all']
    ycols = ['mlmc.{}_avg_wall_speedup'.format(v) for v in categories] + ['ideal_speedup']
    labels = ['Overall'] + ['Ideal']
    pc.plot_common(current, merged, ycols, labels)

plot_mlmc(current, merged)