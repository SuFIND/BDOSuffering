import datetime

from PyQt6 import QtWidgets, QtCore
from ui.ui_op_ctrl import Ui_OpCtrl


class OpCtrl(QtWidgets.QWidget):
    button_sig = QtCore.pyqtSignal(str)

    def __init__(self, parent, logCtrl, *args):
        super(OpCtrl, self).__init__(parent, *args)

        self.LogCtrl = logCtrl

        self.viewer = Ui_OpCtrl()
        self.viewer.setupUi(self)

        self.viewer.StartPauseButton.clicked.connect(self.clicked_for_start_pause_button)
        self.viewer.EndButton.clicked.connect(self.clicked_for_end_button)

        self.button_sig.connect(self.handel_button_logic)

    def clicked_for_start_pause_button(self):
        button_flag = self.viewer.StartPauseButton.text()
        if button_flag == "开始 F10":
            self.button_sig.emit("start")
        elif button_flag == "暂停 F10":
            self.button_sig.emit("pause")

    def clicked_for_end_button(self):
        pass

    def handel_button_logic(self, sig):
        if sig == "start":
            self.LogCtrl.add_log(msg="启动")
            # TODO 启动打三角进程
            # TODO 启动GM守护进程
            # 并重置按钮文字为暂停
            self.viewer.StartPauseButton.setText("暂停 F10")
        elif sig == "pause":
            self.LogCtrl.add_log(msg="暂停")
            # TODO 释放暂停信号
            # 并重置按钮文字为开始
            self.viewer.StartPauseButton.setText("开始 F10")
        elif sig == "end":
            # TODO 释放结束信号
            pass