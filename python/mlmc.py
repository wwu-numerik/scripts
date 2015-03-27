#!/usr/bin/env python3

import os
import sys
import pandas_common as pc

# pd.options.display.mpl_style = 'default'
first = sys.argv[1]
mg = os.path.basename(first)
merged = 'merged_{}.csv'.format(''.join(mg[:-4]))


specials = ['run', 'threads', 'ranks']
baseline_name = 'mlmc.all'
sort_cols = ['ranks', 'threads']
round_digits = 2

headerlist, current = pc.read_files(sys.argv[1:])
current = pc.sorted(current, True)
current = pc.speedup(headerlist, current, specials, baseline_name)
# pprint(t_sections)
current.transpose().to_csv(merged)