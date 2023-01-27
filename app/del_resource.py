import sys
from app.init_resource import global_var


def del_process_pool(cfg: dict):
    process_pool = global_var['process_pool']
    process_pool.shutdown()


def del_resource(cfg: dict):
    funcs = [
        del_process_pool
    ]
    for func in funcs:
        ok = func(cfg)
        if ok:
            continue
        sys.exit(-1)
