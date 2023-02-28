import os
from threading import Thread

import toml
from PyQt6.QtWidgets import QMainWindow, QFileDialog
from PyQt6.QtCore import pyqtSignal as Signal
from ui.ui_app import Ui_MainWindow
from system_hotkey import SystemHotkey

from app.app_thread import GMAlarmThread, EmailThread
from app.init_resource import global_var
from control.GMCheckDialog import GMCheckDialog


class App(QMainWindow, Ui_MainWindow):
    sig_hotkey = Signal(str)
    sig_gm_check = Signal(str)

    def __init__(self, parent=None):
        super(App, self).__init__(parent)
        self.setupUi(self)

        self.sig_hotkey.connect(self.handleHotKeyEvent)
        self.sig_gm_check.connect(self.showGMCheckDialog)

        self.hk_start_pause = SystemHotkey()
        self.hk_stop = SystemHotkey()
        self.hk_test = SystemHotkey()

        self.hk_start_pause.register(('f10',), callback=lambda x: self.sendHotKeySig('f10'))
        self.hk_stop.register(('f11',), callback=lambda x: self.sendHotKeySig('f11'))
        self.hk_test.register(('f9',), callback=lambda x: self.sendHotKeySig('f9'))

        self.actionSaveConfig.triggered.connect(self.save_config)
        self.actionLoadConfig.triggered.connect(self.load_config)

    def sendHotKeySig(self, i_str):
        self.sig_hotkey.emit(i_str)

    def handleHotKeyEvent(self, i_str):
        if i_str == 'f10':
            # 开始 / 暂停
            self.OpCtrl.clicked_for_start_pause_button()
        if i_str == 'f11':
            # 停止
            self.OpCtrl.clicked_for_end_button()
        if i_str == 'f9':
            # 仅合球
            self.OpCtrl.clicked_for_al_button()

    def showGMCheckDialog(self, i_str):
        # 启动警报音的播放线程
        alarm_thread = GMAlarmThread()
        t1 = Thread(target=alarm_thread.run, args=())
        t1.start()
        global_var["threads"].append((t1, alarm_thread))

        # 启动邮件线程，发送报警邮件
        enable_email_alarm = self.OpCtrl.viewer.EmailAlarmCheckBox.isChecked()
        if enable_email_alarm and global_var["enable_email"]:
            to_addr = self.OpCtrl.viewer.EmailEdit.text()
            email_thread = EmailThread()
            t2 = Thread(target=email_thread.run,
                        args=("GM督查警报", "警报！检测到GM督查，请立即人工介入！", global_var["from_email"], to_addr,
                              global_var["from_email_password"], global_var["smtp_server"], global_var["smtp_port"]))
            t2.start()
            global_var["threads"].append((t2, email_thread))

        # 展示弹窗信息
        dialog = GMCheckDialog(self)
        dialog.show()

    def save_config(self):
        """保存配置逻辑"""
        available, rst, reason = self.OpCtrl.collect()
        if available:
            toml_content = toml.dumps(rst)

            fileName_choose, filetype = QFileDialog.getSaveFileName(self,
                                                                    caption="保存配置文件",
                                                                    directory=os.path.join(os.getcwd(), "config"),  # 起始路径
                                                                    filter="Toml Files (*.toml);;All Files (*)",
                                                                    initialFilter="Toml Files (*.toml)")
            if fileName_choose == "":
                # 取消选择
                return

            with open(fileName_choose, 'w', encoding="utf-8") as fp:
                fp.write(toml_content)

    def load_config(self):
        """加载保存的配置逻辑"""
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,
                                                                caption="加载配置文件",
                                                                directory=os.path.join(os.getcwd(), "config"),  # 起始路径
                                                                filter="Toml Files (*.toml)",
                                                                initialFilter="Toml Files (*.toml)")
        if fileName_choose == "":
            # 取消选择
            return

        with open(fileName_choose, encoding="utf-8") as fp:
            custom_config = toml.load(fp)

        self.OpCtrl.load_config(custom_config)
