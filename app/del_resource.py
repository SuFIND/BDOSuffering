import traceback
from concurrent.futures import ProcessPoolExecutor

from app.init_resource import global_var
from utils.log_utils import Logger


def release_process_pool(cfg: dict):
    try:
        process_pool: ProcessPoolExecutor = global_var['process_pool']
        process_pool.shutdown(wait=True)
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)


def release_thread(cfg: dict):
    try:
        threads = global_var["threads"]
        for _, custom_t_obj in threads:
            custom_t_obj.terminate()
        for t, _ in threads:
            t.join()
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)


def release_share_space(cfg):
    try:
        manager = global_var["manager"]
        manager.shutdown()
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)


def release_log_handle(cfg):
    Logger.shutdown()


def release_resource(cfg: dict):
    funcs = [
        release_process_pool,
        release_thread,
        release_share_space,
        release_log_handle,
    ]
    for func in funcs:
        func(cfg)
