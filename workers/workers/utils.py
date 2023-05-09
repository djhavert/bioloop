import hashlib
import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from subprocess import Popen, PIPE

# import multiprocessing
# https://stackoverflow.com/questions/30624290/celery-daemonic-processes-are-not-allowed-to-have-children
import billiard as multiprocessing


def checksum(fname):
    m = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            m.update(chunk)
    return m.hexdigest()


#
# def checksum_py311(fname):
#     with open(fname, 'rb') as f:
#         digest = hashlib.file_digest(f, 'md5')
#         return digest.hexdigest()


def execute_old(cmd, cwd=None):
    if not cwd:
        cwd = os.getcwd()
    print('executing', cmd, 'at', cwd)
    env = os.environ.copy()
    with Popen(cmd, cwd=cwd, stdout=PIPE, stderr=PIPE, shell=True, env=env) as p:
        stdout_lines = []
        for line in p.stdout:
            stdout_lines.append(line)
        return p.pid, stdout_lines, p.returncode


def execute(cmd, cwd=None):
    """
    returns stdout, stderr (strings)
    if the return code is not zero, subprocess.CalledProcessError is raised
    try:
        execute(cmd)
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, exc.stderr, exc.returncode)
    """
    print('executing', cmd, cwd)
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
    return p.stdout, p.stderr


def total_size(dir_path):
    """
    can throw CalledProcessError
    can throw IndexError: list index out of range - if the stdout is not in expected format
    can throw ValueError - invalid literal for int() with base 10 - if the stdout is not in expected format
    """
    completed_proc = subprocess.run(['du', '-sb', str(dir_path)], capture_output=True, check=True, text=True)
    return int(completed_proc.stdout.split()[0])


@contextmanager
def track_progress_parallel(progress_fn, progress_fn_args, loop_delay=5):
    def progress_loop():
        while True:
            time.sleep(loop_delay)
            try:
                progress_fn(*progress_fn_args)
            except Exception as e:
                print('loop: exception', e)

    p = None
    try:
        # start a subprocess to call progress_loop every loop_delay seconds
        p = multiprocessing.Process(target=progress_loop)
        p.start()
        print(f'starting a sub process to track progress with pid: {p.pid}')
        yield p  # inside the context manager
    finally:
        # terminate the sub process
        print(f'terminating progress tracker')
        if p is not None:
            p.terminate()


def progress(name, done, total=None):
    percent_done = None
    if total:
        percent_done = done * 1.0 / total
    return {
        'name': name,
        'percent_done': percent_done,
        'done': done,
        'total': total,
        'units': 'bytes',
    }


def file_progress(celery_task, path, total, progress_name):
    size = Path(path).stat().st_size
    name = progress_name
    r = progress(name=name, done=size, total=total)
    celery_task.update_progress(r)


def parse_number(x, default=None, func=int):
    if x is None:
        return x
    try:
        return func(x)
    except ValueError:
        return default


def convert_size_to_bytes(size_str: str) -> int:
    num, unit = size_str[:-1], size_str[-1]
    if unit == "K":
        return int(float(num) * 1024)
    elif unit == "M":
        return int(float(num) * 1024 ** 2)
    elif unit == "G":
        return int(float(num) * 1024 ** 3)
    elif unit == "T":
        return int(float(num) * 1024 ** 4)
    else:
        return parse_number(size_str, default=size_str)


def merge(a: dict, b: dict) -> dict:
    """
    "merges b into a"

    a = {
        1: {"a":"A"},
        2: {"b":"B"},
        3: [1,2,3],
        4: {'a': {'b': 2}}
    }

    b = {
        2: {"c":"C"},
        3: {"d":"D"},
        4: {'c': {'b': 3}, 'a': [1,2,{'b':2}]}
    }

    merge(a,b)
    {
        1: {'a': 'A'},
        2: {'b': 'B', 'c': 'C'},
        3: {'d': 'D'},
        4: {'a': [1, 2, {'b': 2}], 'c': {'b': 3}}
    }
    """

    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a
