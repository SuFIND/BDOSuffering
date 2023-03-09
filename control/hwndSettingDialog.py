# -*- coding: utf-8 -*-
from PyQt6 import QtWidgets
from win32gui import FindWindow

from app.init_resource import global_var
from ui.ui_hwnd_setting_diaglog import Ui_Dialog


class HwndSettingDialog(QtWidgets.QDialog):
    def __init__(self, parent, *args):
        super(HwndSettingDialog, self).__init__(parent, *args)
        self.viewer = Ui_Dialog()
        self.viewer.setupUi(self)
        self.setModal(True)
        self.init_val()

        self.viewer.TestButton.clicked.connect(self.handle_test)

    def init_val(self):
        self.viewer.lineEdit.setText(global_var["BDO_window_title"])
        self.viewer.lineEdit_2.setText(str(global_var["BDO_window_title_bar_height"]))

    def handle_test(self):
        window_title = self.viewer.lineEdit.text()
        window_class = global_var['BDO_window_class']
        hwnd = FindWindow(window_class, window_title)
        if hwnd == 0:
            QtWidgets.QMessageBox.critical(self,
                                           "错误",
                                           "无法检测到黑色沙漠窗口句柄！请确认游戏是否开启，或检查 “配置”-“黑沙句柄设置” 中窗口名称是"
                                           "否与游戏窗口匹配")
        else:
            QtWidgets.QMessageBox.information(self,
                                              "提示",
                                              "找了黑色沙漠游戏窗口")
