#!/usr/bin/env python3

import sys
import os
import pandas_common as pc

# pd.options.display.mpl_style = 'default'
first = sys.argv[1]
mg = os.path.basename(first)
merged = 'merged_{}.csv'.format(''.join(mg[:-4]))

baseline_name = 'fem.apply'

headerlist, current = pc.read_files(sys.argv[1:])
current = pc.sorted_f(current, True)
current = pc.speedup(headerlist, current, baseline_name)
# pprint(t_sections)
current.transpose().to_csv(merged)
pc.plot_fem(current)
