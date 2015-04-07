__author__ = 'r_milk01'

import os
import pandas as pd
from configparser import SafeConfigParser
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import cm
import itertools
import logging

TIMINGS = ['usr', 'mix', 'sys', 'wall']
MEASURES = ['max', 'avg']
SPECIALS = ['run', 'threads', 'ranks']

pd.options.display.mpl_style = 'default'

def make_val(val, round_digits=3):
    try:
        return round(float(val), round_digits)
    except ValueError:
        return str(val)


def m_strip(s, timings=None, measures=None):
    timings = timings or TIMINGS
    measures = measures or MEASURES
    for t,m in itertools.product(timings, measures):
        s = s.replace('_{}_{}'.format(m, t), '')
    return s


def read_files(dirnames):
    current = None
    for fn in dirnames:
        assert os.path.isdir(fn)
        prof = os.path.join(fn, 'profiler.csv')
        try:
            new = pd.read_csv(prof)
        except pd.parser.CParserError as e:
            logging.error('Failed parsing {}'.format(prof))
            raise e
        headerlist = list(new.columns.values)
        params = SafeConfigParser()
        param_fn = 'dsc_parameter.log'
        params.read([os.path.join(fn, param_fn), os.path.join(fn, 'logs', param_fn)])
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


def sorted_f(frame, ascending=True, sort_cols=None):
    sort_cols = sort_cols or ['ranks', 'threads']
    return frame.sort(columns=sort_cols, na_position='last', ascending=ascending)


def speedup(headerlist, current, baseline_name, specials=None, round_digits=3, timings=None, measures=None):
    timings = timings or TIMINGS
    measures = measures or MEASURES
    specials = specials or SPECIALS
    t_sections = set([m_strip(h) for h in headerlist]) - set(specials)

    for sec in t_sections:
        for t, m in itertools.product(timings, measures):
            source_col = '{}_{}_{}'.format(sec, m, t)
            source = current[source_col]

            speedup_col = source_col + '_speedup'
            ref_value = source[0]
            values = [round(ref_value / source[i], round_digits) for i in range(len(source))]
            current[speedup_col] = pd.Series(values)

            # relative part of overall absolut timing category
            abspart_col = source_col + '_abspart'
            ref_value = lambda j: float(current['{}_{}_{}'.format(baseline_name, m, t)][j])
            values = [round(source[i] / ref_value(i), round_digits) for i in range(len(source))]
            current[abspart_col] = pd.Series(values)

            # relative part of overall total walltime
            wallpart_col = source_col + '_wallpart'
            ref_value = lambda j: float(current['{}_{}_{}'.format(baseline_name, m, 'wall')][j])
            values = [round(source[i] / ref_value(i), round_digits) for i in range(len(source))]
            current[wallpart_col] = pd.Series(values)

        for m in measures:
            # thread efficiency
            source_col = '{}_{}_{}'.format(sec, m, 'usr')
            threadeff_col = source_col + '_threadeff'
            wall = current['{}_{}_{}'.format(sec, m, 'wall')]
            source = current[source_col]
            value = lambda j: float(source[j] / (current['threads'][j] * wall[j]))
            values = [round(value(i), round_digits) for i in range(len(source))]
            current[threadeff_col] = pd.Series(values)

    ref_value = 1
    # ideal speedup account for non-uniform thread/rank ratio across columns
    cmp_value = lambda j: current['ranks'][j] * current['threads'][j]
    values = [cmp_value(i) / cmp_value(0) for i in range(0, len(source))]
    current.insert(len(specials), 'ideal_speedup', pd.Series(values))
    current = sorted_f(current, True)
    return current

def plot_msfem(current, filename_base):
    categories = ['all', 'coarse.solve', 'local.solve_for_all_cells', 'coarse.assemble']
    ycols = ['msfem.{}_avg_wall_speedup'.format(v) for v in categories] + ['ideal_speedup']
    bar_cols = ['msfem.{}_avg_wall_abspart'.format(v) for v in categories[1:]]
    labels = ['Overall', 'Coarse solve', 'Local assembly + solve', 'Coarse assembly'] + ['Ideal']
    plot_common(current, filename_base, ycols, labels, (bar_cols,['Coarse solve', 'Local assembly + solve', 'Coarse assembly']))

def plot_fem(current, filename_base):
    categories = ['apply', 'solve', 'constraints', 'assemble']
    ycols = ['fem.{}_avg_wall_speedup'.format(v) for v in categories] + ['ideal_speedup']
    labels = ['Overall', 'Solve', 'Constraints', 'Assembly', 'Ideal']
    plot_common(current, filename_base, ycols, labels, categories)


def plot_common(current, filename_base, ycols, labels, bar=None, logx_base=None, logy_base=None):
    xcol = 'ranks'
    fig = plt.figure()
    colors = cm.brg
    foo = current.plot(x=xcol, y=ycols, colormap=colors)
    plt.ylabel('Speedup')
    plt.xlabel('# MPI Ranks')
    ax = fig.axes[0]
    if logx_base is not None:
        ax.set_xscale('log', basex=logx_base)
    if logy_base is not None:
        ax.set_yscale('log', basey=logy_base)
    lgd = plt.legend(ax.lines, labels, bbox_to_anchor=(1.05, 1),  borderaxespad=0., loc=2)

    plt.savefig(filename_base + '_speedup.png', bbox_extra_artists=(lgd,), bbox_inches='tight')

    if bar is None:
        return
    cols, labels = bar
    fig = plt.figure()
    ax = current[cols].plot(kind='bar', stacked=True, colormap=colors)
    patches, _ = ax.get_legend_handles_labels()

    lgd = ax.legend(patches, labels, bbox_to_anchor=(1.05, 1),  borderaxespad=0., loc=2)

    plt.savefig(filename_base + '_pie.png', bbox_extra_artists=(lgd,), bbox_inches='tight')
