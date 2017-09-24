import argparse

import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--logs-dir', '-l', type=str, default='./logs', help='path to the directory with logs')

    args = parser.parse_args()

    all_logs = []
    for log_path in os.listdir(args.logs_dir):
        with open(os.path.join(args.logs_dir, log_path), 'r') as file:
            pid_logs = []
            for line in file.readlines():
                pid, time, log_clock, event = line.split()
                if event == 'ACQUIRE':
                    assert pid_logs[-1][3] == 'REQUEST',\
                        'PID {} ACQUIRED MUTEX WITHOUT REQUEST AT {}'.format(pid, time)
                if event == 'RELEASE':
                    assert pid_logs[-1][3] == 'ACQUIRE',\
                        'PID {} RELEASED UNACQUIRED MUTEX AT {}'.format(pid, time)
                pid_logs.append((int(pid), time, int(log_clock), event))
        all_logs.extend(pid_logs)

    all_logs.sort(key=lambda a: a[2])
    acquired = False

    for *_, log_clock, event in all_logs:
        if event == 'ACQUIRE' and acquired:
            assert False, 'ACQUIRE-RELEASE PERIOD OVERLAPS AT {}'.format(log_clock)
        elif event == 'ACQUIRE' and not acquired:
            acquired = True
        elif event == 'RELEASE' and acquired:
            acquired = False
        elif event == 'RELEASE' and not acquired:
            assert False, 'ACQUIRE-RELEASE PERIOD OVERLAPS AT {}'.format(log_clock)
