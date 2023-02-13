import datetime
import os

from PyQt6 import QtWidgets, QtCore, QtGui
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

    LEVEL_LOGS = {
        INFO: {INFO, WARNING, ERROR},
        WARNING: {WARNING, ERROR},
        ERROR: {ERROR},
        DEBUG: {DEBUG, INFO, WARNING, ERROR}
    }

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
        self.viewer.SaveLogButton.clicked.connect(self.save_log)
        self.viewer.LogLevelComboBox.currentTextChanged.connect(self.filter_log)

        # 持有的信号
        self.refresh_sig.connect(self._refresh_log_browse)

        # 当前可返回的一些数据
        self.logLines = []
        self.log_level = self.viewer.LogLevelComboBox.itemText(0).lower()

    def add_log(self, msg, level=INFO):
        """
        添加日志
        :param msg:
        :param level:
        :return:
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        html = ""
        level_color_map = {
            "debug": "#595959",
            "error": "#f5222d",
            "warning": "#fa8c16",
            "info": "#ffffff",
        }
        for (time_str, level, msg) in self.logLines:
            if level not in self.LEVEL_LOGS[self.log_level]:
                continue

            line_one_str = f"{time_str} - [{level}]: {msg}\n"

            color = level_color_map.get(level, "#434343")
            html += f"<div><font color={color}>{line_one_str}</font><div>"

        self.viewer.textBrowser.setHtml(html)
        self.viewer.textBrowser.moveCursor(QtGui.QTextCursor.MoveOperation.End)

    def save_log(self):
        plain_txt = ""
        for (time, level, msg) in self.logLines:
            if level not in self.LEVEL_LOGS[self.log_level]:
                continue

            time_str = time.strftime("%Y-%m-%d %H:%M:%S")
            line_one_str = f"{time_str} - [{level}]: {msg}\n"
            plain_txt += line_one_str

        fileName_choose, filetype = QtWidgets.QFileDialog.getSaveFileName(self,
                                                                          caption="保存日志文件",
                                                                          directory=os.getcwd(),  # 起始路径
                                                                          initialFilter="*.log")
        if fileName_choose == "":
            # 取消选择
            return

        with open(fileName_choose, 'w', encoding="utf-8") as fp:
            fp.write(plain_txt)

    def filter_log(self, level: str):
        level = level.lower()
        self.log_level = level
        self.refresh_sig.emit("")