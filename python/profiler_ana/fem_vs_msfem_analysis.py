#!/usr/bin/env python3


import sys
import os
import pandas as pd
import numpy as np
from configparser import SafeConfigParser
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import cm
import itertools

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


def make_val(val):
    try:
        return round(float(val), round_digits)
    except ValueError:
        return str(val)


def m_strip(s):
    for t,m in itertools.product(timings, measures):
        s = s.replace('_{}_{}'.format(m, t), '')
    return s


def read_files(dirnames):
    current = None
    for fn in dirnames:
        assert os.path.isdir(fn)
        prof = os.path.join(fn, 'profiler.csv')
        new = pd.read_csv(prof)
        headerlist = list(new.columns.values)
        params = SafeConfigParser()
        params.read(os.path.join(fn, 'dsc_parameter.log'))
        p = {}
        for section in params.sections():
            p.update({'{}.{}'.format(section, n): make_val(v) for n, v in params.items(section)})
        p = pd.DataFrame(p, index=[0])
        # mem
        mem = os.path.join(fn, 'memory.csv')
        mem = pd.read_csv(mem)
        new = pd.concat((new, p, mem), axis=1)
        err = os.path.join(fn, 'errors.csv')
        if os.path.isfile(err):
            err = pd.read_csv(err)
            new = pd.concat((new, p, err), axis=1)

        current = current.append(new, ignore_index=True) if current is not None else new
    return headerlist, current

headerlist, current = read_files(sys.argv[1:])

def sorted(frame, ascending=True):
    return frame.sort(columns=sort_cols, na_position='last', ascending=ascending)

current = sorted(current, False)

def speedup(headerlist, current):
  t_sections = set([m_strip(h) for h in headerlist]) - set(specials)

  for sec in t_sections:
      for t, m in itertools.product(timings, measures):
          source_col = '{}_{}_{}'.format(sec, m, t)
          source = current[source_col]

          speedup_col = source_col + '_speedup'
          ref_value = source[0]
          values = [round(ref_value/source[i], round_digits) for i in range(len(source))]
          current[speedup_col] = pd.Series(values)

          abspart_col = source_col + '_abspart'
          ref_value = lambda i: float(current['{}_{}_{}'.format(baseline_name, m, t)][i])
          values = [round(source[i]/ref_value(i), round_digits) for i in range(len(source))]
          current[abspart_col] = pd.Series(values)
  ref_value = 1
  cmp_value = lambda i: current['ranks'][i] / current['threads'][i]
  values = [cmp_value(i)/cmp_value(0) for i in range(0, len(source))] #+ [np.NaN]
  current.insert(len(specials), 'ideal_speedup', pd.Series(values))
  current = sorted(current, True)
  return current

#current = speedup(headerlist, current)


# pprint(t_sections)
current.transpose().to_csv(merged)
# current.transpose().to_excel(merged+'.xls')
# current.to_csv(merged)
def msfem_plots():
  categories = ['all', 'coarse.solve', 'local.solve_for_all_cells', 'coarse.assemble']
  ycols = ['msfem.{}_avg_wall_speedup'.format(v) for v in categories] + ['ideal_speedup']
  labels = ['Overall', 'Coarse solve', 'Local assembly + solve', 'Coarse assembly'] + ['Ideal']
  label_lookup = {v: p for v, p in zip(ycols, labels)}
  xcol = 'ranks'
  # plt.figure()
  fig, ax = plt.subplots()
  ax.set_xscale('log', basex=2)
  # ax.set_yscale('log', basey=2)
  colors = cm.brg

  foo = current.plot(x=xcol, y=ycols, colormap=colors)
  # plt.show()
  # Remove grid lines (dotted lines inside plot)

  # Pandas trick: remove weird dotted line on axis
  ax.lines[0].set_visible(False)
  lgd = plt.legend(ax.lines, labels, bbox_to_anchor=(1.05, 1),  borderaxespad=0., loc=2)

  plt.savefig(merged + '_speedup.png', bbox_extra_artists=(lgd,), bbox_inches='tight')

  pie_header = [f for f in headerlist if 'part' in f]
  foo = current.plot(kind='pie', subplots=True, colormap=colors)
