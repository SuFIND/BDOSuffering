# -*- coding: utf-8 -*-
from PyQt6 import QtWidgets
from win32gui import FindWindow
from threading import Thread

from app.init_resource import global_var
from app.app_thread import ShowImgThread
from ui.ui_gamesetting_dialog import Ui_Dialog


class GameSettingDialog(QtWidgets.QDialog):
    def __init__(self, parent, *args):
        super(GameSettingDialog, self).__init__(parent, *args)
        self.viewer = Ui_Dialog()
        self.viewer.setupUi(self)
        self.viewer.TestGMCheckSCButton.clicked.connect(self.handle_view_gm_check_sc)

    def handle_view_gm_check_sc(self):
        window_title = global_var['BDO_window_title']
        window_class = global_var['BDO_window_class']
        hwnd = FindWindow(window_class, window_title)
        if hwnd != 0:
            # 启动图片展示的线程
            showImgThread = ShowImgThread()
            t = Thread(target=showImgThread.run, args=(hwnd,))
            t.start()
            global_var["threads"].append((t, showImgThread))
        else:
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setWindowTitle("错误")
            msgBox.setText("无法检测到黑色沙漠窗口句柄！请确认游戏是否开启，或检查 “配置”-“黑沙句柄设置” 中窗口名称是否与游戏窗口匹配")
            msgBox.show()
