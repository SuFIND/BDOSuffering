# -*- coding: utf-8 -*-

from PyQt6 import QtWidgets, QtGui

from app.init_resource import global_var
from ui.ui_GM_check_diaglog import Ui_GMCheckDialog


class GMCheckDialog(QtWidgets.QDialog):
    def __init__(self, parent, *args):
        super(GMCheckDialog, self).__init__(parent, *args)
        self.viewer = Ui_GMCheckDialog()
        self.viewer.setupUi(self)

        self.viewer.StopButton.clicked.connect(self.handel_stop_button)

    def handel_stop_button(self) -> None:
        """
        处理关闭按钮
        :return:
        """
        sig_dic = global_var["process_sig"]
        sig_mutex = global_var["process_sig_lock"]
        with sig_mutex:
            sig_dic.update({"start": False, "pause": False, "stop": True})

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """
        处理关闭事件
        :param a0:
        :return:
        """
        QtWidgets.QDialog.closeEvent(self, a0)

        sig_dic = global_var["process_sig"]
        sig_mutex = global_var["process_sig_lock"]
        with sig_mutex:
            sig_dic.update({"start": False, "pause": False, "stop": True})
