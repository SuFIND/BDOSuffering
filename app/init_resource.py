import sys
import toml
from concurrent.futures import ProcessPoolExecutor
global global_var
global_var = {}


def init_config(paths: list):
    config = toml.load(paths)
    return config


def init_process_pool(cfg: dict):
    """
    初始化进程池
    :param cfg:
    :return:
    """
    ok = True
    process_pool = ProcessPoolExecutor(max_workers=cfg['app']['max_process_cnt'])
    global_var["process_pool"] = process_pool
    return ok


def init_resource(cfg: dict):
    funcs = [
        init_process_pool
    ]
    for func in funcs:
        ok = func(cfg)
        if ok:
            continue
        sys.exit(-1)
