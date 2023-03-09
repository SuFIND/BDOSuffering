import sys
import os
import traceback
from traceback import format_exc
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from pathlib import Path

import rtoml

from utils.log_utils import Logger
from utils.crypt_utils import decrypt_config_file, build_key

global global_var
global_var = {}

cipher = os.environ.get("CIPHER", "")

def init_config(public_cfg_path: str, private_cfg_path: str):
    public_p = Path(public_cfg_path)
    public_config = rtoml.load(public_p)
    _, r_key = build_key(cipher)
    config = decrypt_config_file(private_cfg_path, r_key)
    config["BDO"]["window_title"] = public_config["window_title"]
    config["BDO"]["window_title_bar_height"] = public_config["window_title_bar_height"]
    return config


def init_app_config(cfg: dict):
    ok = True
    try:
        global_var["debug"] = cfg["app"]["debug"]
    except Exception as e:
        err = format_exc()
        Logger.error(err)
        ok = False
    return ok


def init_bod_config(cfg: dict):
    """
    初始化黑色沙漠窗口相关的信息
    :param cfg:
    :return:
    """
    ok = True
    try:
        global_var['BDO_window_title'] = cfg["BDO"]["window_title"]
        global_var['BDO_window_class'] = cfg["BDO"]["window_class"]
        global_var['BDO_window_title_bar_height'] = cfg["BDO"]["window_title_bar_height"]
    except Exception:
        err = format_exc()
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
    global_var["manager"] = m
    global_var["process_sig"] = sig_dic
    global_var["process_sig_lock"] = sig_mutex
    global_var["process_msg_queue"] = msg_queue
    global_var["threads"] = []
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
        err = format_exc()
        Logger.error(err)
    return ok


def init_model_config(cfg: dict):
    """
    加载模型相关的配置
    :param cfg:
    :return:
    """
    ok = True
    try:
        global_var["onnx_file_path"] = cfg["model"]["onnx_file_path"]
        global_var["classes_id_file_path"] = cfg["model"]["classes_id_file_path"]
    except Exception as e:
        ok = False
        err = format_exc()
        Logger.error(err)
    return ok


def init_email_config(cfg: dict):
    ok = True
    try:
        global_var["enable_email"] = cfg["email"]["enable"]
        global_var["smtp_server"] = cfg["email"]["smtp_server"]
        global_var["smtp_port"] = cfg["email"]["smtp_port"]
        global_var["from_email"] = cfg["email"]["from_email"]
        global_var["from_email_password"] = cfg["email"]["password"]
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)
        ok = False
    return ok


def init_resource(cfg: dict):
    funcs = [
        init_app_config,
        init_process_pool,
        init_bod_config,
        init_gm_check_config,
        init_model_config,
        init_email_config,
    ]
    for func in funcs:
        ok = func(cfg)
        if ok:
            continue
        sys.exit(-1)
