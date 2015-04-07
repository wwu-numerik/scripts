#!/usr/bin/env python3
import sys

import pandas_common as pc

common_string = pc.common_substring(sys.argv[1:])
merged = 'merged_{}.csv'.format(common_string)
baseline_name = 'msfem.all'

headerlist, current = pc.read_files(sys.argv[1:])
current = pc.sorted_f(current, False)
current = pc.speedup(headerlist, current, baseline_name)
# pprint(t_sections)

pc.plot_msfem(current, merged)

current.transpose().to_csv(merged)
# current.transpose().to_excel(merged+'.xls')
# current.to_csv(merged)
