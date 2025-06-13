import os
import time


def parse_timing_db(filename, after_date=None):
    if not os.path.isfile(filename):
        return {}

    lines = [i.strip().split() for i in open(filename)]
    lines.reverse()
    cur_run_bid = ''
    targets = dict()
    for l in lines:
        if len(l) != 4:
            continue
        target = l[3]
        bid = l[1]
        action = l[2]
        timestamp = float(l[0])

        if not cur_run_bid:
            cur_run_bid = bid

        if target not in targets:
            targets[target] = {
                'current': False,
                'running': False,
                'done': os.path.exists(target),
                'isdir': os.path.isdir(target)
            }

        logpath = 'logs/%s/%s/log.txt' % (bid, target)
        if 'log' not in targets[target] and os.path.exists(logpath):
            targets[target]['log'] = logpath

        failpath = 'logs/%s/%s/failed.touch' % (bid, target)
        if 'failed' not in targets[target]:
            targets[target]['failed'] = os.path.exists(failpath)

        if bid == cur_run_bid:
            targets[target]['current'] = True
            targets[target][action + '_current'] = timestamp
            if 'finish_current' not in targets[target]:
                if targets[target]['failed']:
                    targets[target]['finish_current'] = os.path.getmtime(failpath)
                else:
                    targets[target]['finish_current'] = float(time.time())
                    targets[target]['running'] = True

        if not (bid == cur_run_bid):
            if 'prev' not in targets[target] and action == 'finish':
                targets[target]['prev'] = bid
                targets[target][action + '_prev'] = timestamp
            elif action == 'start' and targets[target].get('prev') == bid:
                targets[target][action + '_prev'] = timestamp

        if 'finish_current' in targets[target] and 'start_current' in targets[target]:
            targets[target]['timing_sec'] = targets[target]['finish_current'] - targets[target]['start_current']
        elif 'start_prev' in targets[target]:
            if after_date and targets[target]['start_prev'] < after_date.timestamp():
                targets[target]['timing_sec'] = 1
            else:
                targets[target]['timing_sec'] = targets[target]['finish_prev'] - targets[target]['start_prev']
    return targets


def analyze_target(filename, target_name):
    """Return statistics about target execution history."""
    if not os.path.isfile(filename):
        return None

    starts = {}
    durations = []
    start_count = 0
    finish_count = 0

    with open(filename) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 4:
                continue
            timestamp, bid, action, target = parts
            if target != target_name:
                continue
            ts = float(timestamp)
            if action == 'start':
                starts[bid] = ts
                start_count += 1
            elif action == 'finish':
                if bid in starts:
                    finish_count += 1
                    durations.append(ts - starts.pop(bid))

    if durations:
        durations_sorted = sorted(durations)
        max_d = max(durations)
        min_d = min(durations)
        avg_d = sum(durations) / len(durations)
        mid = len(durations_sorted) // 2
        if len(durations_sorted) % 2:
            median_d = durations_sorted[mid]
        else:
            median_d = (durations_sorted[mid - 1] + durations_sorted[mid]) / 2
        last_d = durations[-1]
    else:
        max_d = min_d = avg_d = median_d = last_d = 0

    return {
        'starts': start_count,
        'finishes': finish_count,
        'max': max_d,
        'min': min_d,
        'avg': avg_d,
        'median': median_d,
        'last': last_d,
    }
