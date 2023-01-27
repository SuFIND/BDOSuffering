import datetime

from PyQt6 import QtWidgets, QtCore
from ui.ui_log_ctrl import Ui_LogCtrl


class LogCtrl(QtWidgets.QWidget):
    logLines = []

    # 日志等级
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"

    # 信号
    refresh_sig = QtCore.pyqtSignal(str)

    def __init__(self, parent, *args):
        """
        树项目窗口控件
        :param parent: 父控件
        :param args:
            - flags，见PyQt5.QtWidgets.QWidget形参说明
        """
        super(LogCtrl, self).__init__(parent, *args)
        self.viewer = Ui_LogCtrl()
        self.viewer.setupUi(self)

        self.viewer.ClearLogButton.clicked.connect(self.clear_log)

        # 持有的信号
        self.refresh_sig.connect(self._refresh_log_browse)

        # 当前可返回的一些数据
        self.logLines = []

    def add_log(self, msg, level=INFO):
        """
        添加日志
        :param msg:
        :param level:
        :return:
        """
        now = datetime.datetime.now()
        self.logLines.append((now, level, msg))
        self.refresh_sig.emit("refresh")

    def clear_log(self):
        self.logLines = []
        self.refresh_sig.emit("refresh")

    def _refresh_log_browse(self, sig):
        """
        刷新日志浏览器
        :return:
        """
        log_content = ""
        for time, level, msg in self.logLines:
            time_str = time.strftime("%Y-%m-%d %H:%M:%S")
            log_content += f"{time_str} - [{level}]: {msg}\n"
        self.viewer.textBrowser.setPlainText(log_content)
