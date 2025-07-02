#!/usr/bin/python3

import collections
import datetime
import os
import math
from subprocess import Popen, PIPE
from graphviz import Digraph

# Build DOT graphs using the ``graphviz`` library to ensure that
# node names and attributes are properly escaped.

def critical_path(influences, dependencies, inputs, timing):
    targets = dict()
    update_queue = list(inputs)
    results = list()

    # forward: early start
    while update_queue:
        t = update_queue.pop(0)
        if t not in targets:
            targets[t] = {"early_start": 0.0}
        if t in timing:
            duration = timing[t].get('timing_sec', 1)
        else:
            duration = 1
        targets[t]["duration"] = duration
        targets[t]["early_end"] = targets[t]["early_start"] + duration
        # add timing tag as hour number from very start
        targets[t]["timing_tag"] = math.ceil(targets[t]["early_end"]/60/10)
        targets[t]["pin_timing_tag"] = True
        for z in influences[t]:
            update_queue.append(z)
            if z not in targets:
                targets[z] = {"early_start": targets[t]["early_end"]}
            else:
                targets[z]["early_start"] = max(targets[z]["early_start"], targets[t]["early_end"])
        if not influences[t]:
            results.append(t)
            # don't pin the final targets to the timeline
            targets[t]["pin_timing_tag"] = False

    # backward: late start
    update_queue = results
    while update_queue:
        t = update_queue.pop(0)
        if "late_end" not in targets[t]:
            targets[t]["late_end"] = targets[t]["early_end"]
        targets[t]["late_start"] = targets[t]["late_end"] - targets[t]["duration"]
        for d in dependencies.get(t, []):
            for z in d:
                # don't pin timing tags for dependencies if they're at the same tag
                if targets[z]["timing_tag"] == targets[t]["timing_tag"]:
                    targets[z]["pin_timing_tag"] = False
                if z not in update_queue:
                    update_queue.append(z)
                if "late_end" not in targets[z]:
                    targets[z]["late_end"] = targets[t]["late_start"]
                else:
                    targets[z]["late_end"] = min(targets[t]["late_start"], targets[z]["late_end"])

    cp = set()
    timing_tags = {}
    for t, z in targets.items():
        if z["early_start"] == z["late_start"]:
            cp.add(t)
        if z["pin_timing_tag"]:
            if z["timing_tag"] not in timing_tags:
                timing_tags[z["timing_tag"]] = [t]
            else:
                timing_tags[z["timing_tag"]].append(t)

    return cp, timing_tags


def current_run_critical_path(influences, dependencies, timing):
    """Return the critical path limited to targets executed in the current run."""
    current = {t for t, perf in timing.items() if perf.get('current')}
    if not current:
        return set()

    inf = {k: {d for d in v if d in current} for k, v in influences.items() if k in current}
    deps = {}
    for k, (deps_list, order_list) in dependencies.items():
        if k not in current:
            continue
        deps[k] = [
            [d for d in deps_list if d in current],
            [d for d in order_list if d in current],
        ]

    inputs = set(inf.keys())
    for v in inf.values():
        for t in v:
            inputs.discard(t)

    cp, _ = critical_path(inf, deps, inputs, timing)
    return cp


def classify_target(name, influences, dependencies, inputs, order_only):
    group = ''
    if name not in dependencies:
        group = 'cluster_not_implemented'
    elif name in inputs:
        if influences:
            group = 'cluster_inputs'
        else:
            if name in order_only:
                group = 'cluster_order_only'
            else:
                group = 'cluster_tools'
    elif not influences:
        group = 'cluster_result'
    return group


def dot_node(graph, name, performance, docstring, cp, *, invisible=False):
    """Add a node to *graph* with attributes derived from performance data."""
    node = {
        'label': name,
        'fontsize': 10,
        'color': 'black',
        'fillcolor': '#d3d3d3'
    }
    if name in performance:
        target_performance = performance[name]
        # Mark targets built in the current run with a dedicated color.
        if target_performance.get('failed'):
            node['fillcolor'] = '.05 .3 1.0'
        elif target_performance.get('current'):
            node['fillcolor'] = '#0969DA'
            node['fontcolor'] = '#fff'
        elif target_performance.get('done'):
            node['fillcolor'] = '.7 .3 1.0'
            if target_performance['isdir']:
                node['fillcolor'] = '.2 .3 1.0'
        timing_sec = target_performance.get('timing_sec', 0)
        timing = str(datetime.timedelta(seconds=int(timing_sec)))
        if 'log' in target_performance:
            node['URL'] = target_performance['log']
        if timing != '0:00:00':
            node['label'] += '\\n%s\\r' % timing
            node['fontsize'] = min(max(timing_sec ** .5, node['fontsize']), 150)
    if name in cp:
        node['color'] = '#cc0000'
    node['group'] = '/'.join(name.split('/')[:2])
    node['shape'] = 'box'
    node['style'] = 'filled'
    if invisible:
        node['style'] = 'invis'
    # generate title as target name when docstring is empty
    node['tooltip'] = docstring if docstring else name
    if name[-4:] == '.png' and os.path.exists(name):
        node['image'] = name
        node['imagescale'] = 'true'
        node['width'] = '1'
    graph.node(name, **{k: str(v) for k, v in node.items()})


def export_dot(f, influences, dependencies, order_only, performance, indirect_influences, docs):
    dot = Digraph('G')
    dot.attr(rankdir='BT', ratio='0.5625', newrank='true')
    dot.attr('node', shape='box')

    groups = collections.defaultdict(set)

    # look for keys that aren't linked
    inputs = set(influences.keys())
    for k, v in influences.items():
        for t in v:
            inputs.discard(t)

    cp, timing_tags = critical_path(influences, dependencies, inputs, performance)
    cp_last = current_run_critical_path(influences, dependencies, performance)

    # cluster labels
    labels = {
        'cluster_inputs': 'Input',
        'cluster_result': 'Result',
        'cluster_not_implemented': 'Not implemented',
        'cluster_order_only': 'Order only',
        'cluster_tools': 'Tools'
    }

    hidden_nodes = []

    for target, infls in influences.items():
        group = classify_target(target, infls, dependencies, inputs, order_only)
        groups[group].add(target)

    for k, v in sorted(groups.items()):
        label = labels.get(k, '')
        with dot.subgraph(name=k) as sg:
            if label:
                sg.attr(label=label)
            sg.attr(style='dotted')
            if k == 'cluster_result':
                sg.attr(rank='sink')
            if k == 'cluster_tools':
                sg.attr(rank='source')
            if k == 'cluster_order_only':
                hidden_nodes = v
                for t in v:
                    dot_node(sg, t, performance, docs.get(t, t), cp, invisible=True)
            else:
                for t in v:
                    dot_node(sg, t, performance, docs.get(t, t), cp)
            sg.node(f"{k}_DUMMY", shape='point', style='invis')

    for k, v in influences.items():
        for t in sorted(v):
            if t in indirect_influences[k]:
                dot.edge(k, t, color="#00000033", weight="0", style="dashed")
            elif k in cp_last and t in cp_last:
                dot.edge(k, t, color="#800080", weight="10", penwidth="3", headclip="true")
            elif k in cp and t in cp:
                dot.edge(k, t, color="#cc0000", weight="20", penwidth="6", headclip="true")
            else:
                dot.edge(k, t)

    dot.edge('cluster_inputs_DUMMY', 'cluster_tools_DUMMY', style='invis')
    dot.edge('cluster_tools_DUMMY', 'cluster_result_DUMMY', style='invis')

    if 'cluster_not_implemented' in groups:
        dot.edge('cluster_inputs_DUMMY', 'cluster_not_implemented_DUMMY', style='invis')
        dot.edge('cluster_not_implemented_DUMMY', 'cluster_tools_DUMMY', style='invis')
        dot.edge('cluster_not_implemented_DUMMY', 'cluster_order_only_DUMMY', style='invis')

    def format_deciminutes(k):
        hrs = math.floor(k / 6)
        minutes = (k % 6) * 10
        return f"{hrs}:{minutes:02d}"

    for k, v in timing_tags.items():
        with dot.subgraph() as sg:
            sg.attr(rank='same')
            sg.node(str(k), label=format_deciminutes(k), fontsize='50')
            for t in v:
                if t not in hidden_nodes:
                    sg.node(t)
    tags = sorted(timing_tags.keys())
    for a, b in zip(tags, tags[1:]):
        dot.edge(str(a), str(b))

    f.write(dot.source)


def render_dot(dot_fd, image_filename):
    unflatten = Popen('unflatten', stdin=PIPE, stdout=PIPE)
    dot = Popen(['dot', '-Tsvg', '-Gnslimit=50'], stdin=unflatten.stdout, stdout=PIPE)
    unflatten.stdin.write(dot_fd.read().encode('utf-8'))
    unflatten.stdin.close()
    unflatten.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
    svg, _ = dot.communicate()
    svg = svg.replace(b'svg width', b'svg disabled-width').replace(b'height', b'disabled-height')
    open(image_filename, 'wb').write(svg)
