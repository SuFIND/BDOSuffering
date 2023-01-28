import datetime

from PyQt6 import QtWidgets, QtCore
from ui.ui_op_ctrl import Ui_OpCtrl
from app.init_resource import global_var
from operation.v1 import start_action


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
        self.button_sig.emit("stop")

    def handel_button_logic(self, sig):
        sig_dic = global_var["process_sig"]
        sig_mutex = global_var["process_sig_lock"]
        if sig == "start":
            with sig_mutex:
                if sig_dic["pause"]:
                    sig_dic.update({"start": True, "pause": False})
                else:
                    # 启动打三角进程
                    process_pool = global_var["process_pool"]
                    sig_dic = global_var["process_sig"]
                    sig_mutex = global_var["process_sig_lock"]
                    msg_queue = global_var["process_msg_queue"]
                    window_title = global_var['BDO_window_title']
                    window_class = global_var['BDO_window_class']

                    process_pool.submit(start_action, sig_dic, sig_mutex, msg_queue, window_title, window_class)

            # TODO 启动GM守护进程
            # 并重置按钮文字为暂停
            self.viewer.StartPauseButton.setText("暂停 F10")
        elif sig == "pause":
            self.LogCtrl.add_log(msg="暂停")
            # 释放暂停信号
            with sig_mutex:
                sig_dic.update({"stop": False, "start": False, "pause": True})

            # 并重置按钮文字为开始
            self.viewer.StartPauseButton.setText("开始 F10")
        elif sig == "stop":
            # 释放结束信号
            sig_dic = global_var["process_sig"]
            sig_mutex = global_var["process_sig_lock"]
            with sig_mutex:
                sig_dic.update({"stop": True, "start": False, "pause": False})

            self.LogCtrl.add_log("手动停止")
        elif sig == "refresh_display:pause":
            self.viewer.StartPauseButton.setText("暂停 F10")
        elif sig == "refresh_display:start":
            self.viewer.StartPauseButton.setText("开始 F10")
