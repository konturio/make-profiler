import os
import time


def parse_timing_db(filename, after_date=None):
    if not os.path.isfile(filename):
        return {}

    lines = [i.strip().split() for i in open(filename)]
    lines.reverse()
    cur_run_bid = ''
    targets = dict()
    for parts in lines:
        if len(parts) != 4:
            continue
        target = parts[3]
        bid = parts[1]
        action = parts[2]
        timestamp = float(parts[0])

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
