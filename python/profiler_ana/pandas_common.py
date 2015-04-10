__author__ = 'r_milk01'

import os
import pandas as pd
from configparser import SafeConfigParser
import matplotlib.pyplot as plt
import matplotlib
import itertools
import logging
import difflib
import colors as color_util

TIMINGS = ['usr', 'mix', 'sys', 'wall']
MEASURES = ['max', 'avg']
SPECIALS = ['run', 'threads', 'ranks', 'cores']
'''markers = {0: u'tickleft', 1: u'tickright', 2: u'tickup', 3: u'tickdown', 4: u'caretleft', u'D': u'diamond',
           6: u'caretup', 7: u'caretdown', u's': u'square', u'|': u'vline', u'': u'nothing', u'None': u'nothing',
           None: u'nothing', u'x': u'x', 5: u'caretright', u'_': u'hline', u'^': u'triangle_up', u' ': u'nothing',
           u'd': u'thin_diamond', u'h': u'hexagon1', u'+': u'plus', u'*': u'star', u',': u'pixel', u'o': u'circle',
           u'.': u'point', u'1': u'tri_down', u'p': u'pentagon', u'3': u'tri_left', u'2': u'tri_up', u'4': u'tri_right',
           u'H': u'hexagon2', u'v': u'triangle_down', u'8': u'octagon', u'<': u'triangle_left', u'>': u'triangle_right'}
'''
MARKERS = ['s', 'x', 'o', 'D', '+', '|', '*', 1, 2, 3, 4, 6, 7]
FIGURE_OUTPUTS = ['png', 'eps', 'svg']

pd.options.display.mpl_style = 'default'
matplotlib.rc('font', family='sans-serif')
# http://nerdjusttyped.blogspot.de/2010/07/type-1-fonts-and-matplotlib-figures.html
matplotlib.rcParams['ps.useafm'] = True
matplotlib.rcParams['pdf.use14corefonts'] = True
matplotlib.rcParams['text.usetex'] = True

def common_substring(strings, glue='_'):
    first, last = strings[0], strings[-1]
    seq = difflib.SequenceMatcher(None, first, last, autojunk=False)
    mb = seq.get_matching_blocks()
    return glue.join([first[m.a:m.a + m.size] for m in mb]).replace(os.path.sep, '')

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


def read_files(dirnames, specials=None):
    current = None
    specials = specials or SPECIALS
    header = {'memory': [], 'profiler': [], 'params': [], 'errors': []}
    for fn in dirnames:
        assert os.path.isdir(fn)
        prof = os.path.join(fn, 'profiler.csv')
        try:
            new = pd.read_csv(prof)
        except pd.parser.CParserError as e:
            logging.error('Failed parsing {}'.format(prof))
            raise e
        header['profiler'] = list(new.columns.values)
        params = SafeConfigParser()
        param_fn = 'dsc_parameter.log'
        params.read([os.path.join(fn, param_fn), os.path.join(fn, 'logs', param_fn),
                     os.path.join(fn, 'logdata', param_fn)])
        p = {}
        for section in params.sections():
            p.update({'{}.{}'.format(section, n): make_val(v) for n, v in params.items(section)})
        param = pd.DataFrame(p, index=[0])
        # mem
        mem = os.path.join(fn, 'memory.csv')
        mem = pd.read_csv(mem)
        new = pd.concat((new, param, mem), axis=1)
        header['memory'] = mem.columns.values
        header['params'] = param.columns.values
        err = os.path.join(fn, 'errors.csv')
        if os.path.isfile(err):
            err = pd.read_csv(err)
            header['errors'] = err.columns.values
            new = pd.concat((new, err), axis=1)

        current = current.append(new, ignore_index=True) if current is not None else new
    # ideal speedup account for non-uniform thread/rank ratio across columns
    count = len(current['ranks'])
    cmp_value = lambda j: current['ranks'][j] * current['threads'][j]
    values = [cmp_value(i) / cmp_value(0) for i in range(0, count)]
    current.insert(len(specials), 'ideal_speedup', pd.Series(values))
    cores = [cmp_value(i) for i in range(0, count)]
    current.insert(len(specials), 'cores', pd.Series(cores))
    return header, current


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


def plot_common(current, filename_base, ycols, labels, bar=None, logx_base=None, logy_base=None, color_map=None):
    xcol = 'cores'
    fig = plt.figure()
    color_map = color_map or color_util.discrete_cmap(len(labels))
    foo = current.plot(x=xcol, y=ycols, colormap=color_map)
    for i, line in enumerate(foo.lines):
        line.set_marker(MARKERS[i])
    plt.ylabel('Speedup')
    plt.xlabel('\# Cores')
    ax = fig.axes[0]
    if logx_base is not None:
        ax.set_xscale('log', basex=logx_base)
    if logy_base is not None:
        ax.set_yscale('log', basey=logy_base)
    lgd = plt.legend(ax.lines, labels, loc=2)#, bbox_to_anchor=(1.05, 1),  borderaxespad=0., loc=2)

    for fmt in FIGURE_OUTPUTS:
        plt.savefig(filename_base + '_speedup.{}'.format(fmt), bbox_extra_artists=(lgd,), bbox_inches='tight')

    if bar is None:
        return
    cols, labels = bar
    fig = plt.figure()
    ax = current[cols].plot(kind='bar', stacked=True, colormap=color_map)
    patches, _ = ax.get_legend_handles_labels()

    lgd = ax.legend(patches, labels, bbox_to_anchor=(1.05, 1),  borderaxespad=0., loc=2)

    plt.savefig(filename_base + '_pie.png', bbox_extra_artists=(lgd,), bbox_inches='tight')


def plot_error(data_frame, filename_base, error_cols, xcol, labels, baseline_name,
               logx_base=None, logy_base=None, color_map=None):
    fig = plt.figure()

    #normed walltime
    normed = 'normed_walltime'
    w_time = data_frame['{}_avg_wall'.format(baseline_name)]
    count = len(w_time)
    values = [w_time[i] / w_time.max() for i in range(0, count)]
    data_frame.insert(0, normed, pd.Series(values))

    color_map = color_map or color_util.discrete_cmap(len(labels))
    foo = data_frame.plot(x=xcol, y=error_cols+[normed], colormap=color_map)
    for i, line in enumerate(foo.lines):
        line.set_marker(MARKERS[i])
    plt.ylabel('Error')
    plt.xlabel('Cells')
    ax = fig.axes[0]
    if logx_base is not None:
        ax.set_xscale('log', basex=logx_base)
    if logy_base is not None:
        ax.set_yscale('log', basey=logy_base)
    lgd = plt.legend(ax.lines, labels, loc=2)#, bbox_to_anchor=(1.05, 1),  borderaxespad=0., loc=2)

    common = common_substring(error_cols)
    for fmt in FIGURE_OUTPUTS:
        plt.savefig( '{}_{}.{}'.format(filename_base, common, fmt), bbox_extra_artists=(lgd,), bbox_inches='tight')
