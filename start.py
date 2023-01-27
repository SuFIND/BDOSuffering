import logging.handlers
import os

from PyQt6 import QtWidgets
from app.app import App
from utils.log_utils import Logger
from app.init_resource import init_config, init_resource
from app.del_resource import del_resource


def app_exit(app, cfg):
    app.exec()
    del_resource(cfg)


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
    main_app.show()
    sys.exit(app_exit(app, config))


if __name__ == "__main__":
    main()
