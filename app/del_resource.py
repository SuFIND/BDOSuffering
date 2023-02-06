import sys
from app.init_resource import global_var, exitFlag


def del_process_pool(cfg: dict):
    process_pool = global_var['process_pool']
    process_pool.shutdown()


def del_thread(cfg: dict):
    exitFlag = 1
    ts = global_var["threads"]
    for t in ts:
        t.join()


def del_queue(cfg):
    q = global_var["process_msg_queue"]
    q.close()


def del_resource(cfg: dict):
    funcs = [
        del_process_pool,
        del_thread,
        del_queue,
    ]
    for func in funcs:
        ok = func(cfg)
        if ok:
            continue
        sys.exit(-1)
