import os
import time
import threading
import multiprocessing

from PyQt6 import QtWidgets
from app.app import App
from utils.log_utils import Logger
from app.init_resource import init_config, init_resource, global_var, exitFlag
from app.del_resource import del_resource


def app_exit(app, cfg):
    app.exec()
    del_resource(cfg)


def monitor_msg_queue_thread(app):
    """
    监听进程共享的消息队列刷新进入日志, 更新界面标志
    :return:
    """
    msg_queue = global_var["process_msg_queue"]
    sig_dic = global_var["process_sig"]
    sig_mutex = global_var["process_sig_lock"]

    while exitFlag == 0:
        with sig_mutex:
            try:
                if sig_dic["start"] and app.OpCtrl.viewer.StartPauseButton.text() != "暂停 F10":
                    app.OpCtrl.button_sig.emit("refresh_display:pause")
                if (sig_dic["pause"] or sig_dic["stop"]) and app.OpCtrl.viewer.StartPauseButton.text() != "开始 F10":
                    app.OpCtrl.button_sig.emit("refresh_display:start")
            except RuntimeError:
                pass

        if not msg_queue.empty():
            msg_str = msg_queue.get(block=False)
            if msg_str == "action::show_gm_modal":
                app.sig_gm_check.emit("show_gm_modal")
            else:
                level, src, msg = msg_str.split("$")
                app.LogCtrl.add_log(msg=f"{src}->{msg}", level=level)
        else:
            time.sleep(1)


def main():
    import sys

    # 初始化日志模块
    Logger.info("app start ...")

    # 初始化配置模块
    config_path = os.environ.get("CFG_PATH", os.path.join(os.getcwd(), "config", "my_config.toml"))
    config = init_config(config_path)

    # 初始化必要资源
    init_resource(config)

    app = QtWidgets.QApplication(sys.argv)
    main_app = App()

    t = threading.Thread(target=monitor_msg_queue_thread, args=(main_app,), daemon=True)
    t.start()
    global_var["threads"].append(t)

    main_app.show()
    sys.exit(app_exit(app, config))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
