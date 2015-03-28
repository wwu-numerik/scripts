#!/usr/bin/env python3


import sys
import os

import pandas_common as pc

# pd.options.display.mpl_style = 'default'
first = sys.argv[1]
mg = os.path.basename(first)
merged = 'merged_{}.csv'.format(''.join(mg[:-4]))

timings = ['usr', 'mix', 'sys', 'wall']
measures = ['max', 'avg']
specials = ['run', 'threads', 'ranks']
baseline_name = 'msfem.all'
sort_cols = ['ranks', 'threads']
round_digits = 2

headerlist, current = pc.read_files(sys.argv[1:])
current = pc.sorted(current, False)
current = pc.speedup(headerlist, current)
# pprint(t_sections)
current.transpose().to_csv(merged)
# current.transpose().to_excel(merged+'.xls')
# current.to_csv(merged)
