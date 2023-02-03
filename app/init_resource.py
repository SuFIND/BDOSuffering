import sys
import traceback

import toml
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from utils.log_utils import Logger
global global_var
global exitFlag
global_var = {}
exitFlag = 0


def init_config(paths: list):
    config = toml.load(paths)
    return config


def init_bod_config(cfg: dict):
    ok = True
    try:
        global_var['BDO_window_title'] = cfg["BDO"]["window_title"]
        global_var['BDO_window_class'] = cfg["BDO"]["window_class"]
    except Exception:
        err = traceback.format_exc()
        Logger.error(err)
        ok = False
    return ok


def init_process_pool(cfg: dict):
    """
    初始化进程池
    :param cfg:
    :return:
    """
    ok = True
    process_pool = ProcessPoolExecutor(max_workers=cfg['app']['max_process_cnt'])
    global_var["process_pool"] = process_pool
    m = Manager()
    sig_dic = m.dict({"start": False,
                      "pause": False,
                      "stop": True, })
    sig_mutex = m.Lock()
    msg_queue = m.Queue()
    global_var["process_sig"] = sig_dic
    global_var["process_sig_lock"] = sig_mutex
    global_var["process_msg_queue"] = msg_queue
    return ok


def init_gm_check_config(cfg: dict):
    """
    初始化GM检测相关的配置内容
    :param cfg:
    :return:
    """
    ok = True
    try:
        global_var["gm_check_cool_time"] = cfg["GM"]["check_cool_time"]
        global_var["gm_chat_color"] = cfg["GM"]["chat_color"]
        global_var["gm_find_pix_max_count"] = cfg["GM"]["find_pix_max_count"]
    except Exception as e:
        ok = False
        err = traceback.format_exc()
        Logger.error(err)
    return ok


def init_resource(cfg: dict):
    funcs = [
        init_process_pool,
        init_bod_config,
        init_gm_check_config,
    ]
    for func in funcs:
        ok = func(cfg)
        if ok:
            continue
        sys.exit(-1)
