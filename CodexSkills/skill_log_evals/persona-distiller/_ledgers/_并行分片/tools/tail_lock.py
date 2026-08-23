#!/usr/bin/env python3
"""
T3 尾段互斥锁：register_persona + git add/commit 的共享写串行化。

用法：
    python3 tail_lock.py -- bash -c 'python3 register_persona.py ... && git add ... && git commit ...'
    python3 tail_lock.py --timeout 3600 -- bash -c '...'

锁文件：<本脚本目录>/tail.lock（fcntl.flock，跨进程互斥）。
任一子代理在「发布→登记→提交」尾段持有锁，其余子代理阻塞等待（默认最长 3600s）。
"""
import sys, os, time, subprocess

LOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tail.lock")
DEFAULT_TIMEOUT = 3600


def main():
    args = sys.argv[1:]
    timeout = DEFAULT_TIMEOUT
    if args and args[0] == "--timeout":
        timeout = int(args[1])
        args = args[2:]
    if not args or args[0] != "--":
        raise SystemExit("用法: tail_lock.py [--timeout N] -- <command...>")
    cmd = args[1:]

    import fcntl
    fd = os.open(LOCK, os.O_CREAT | os.O_RDWR, 0o644)
    deadline = time.time() + timeout
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except OSError:
            if time.time() > deadline:
                os.close(fd)
                raise SystemExit("tail_lock: 等待锁超时 (%ss)，放弃" % timeout)
            time.sleep(2)
    try:
        rc = subprocess.call(cmd)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    raise SystemExit(rc)


if __name__ == "__main__":
    main()
