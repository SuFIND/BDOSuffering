import threading

from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import pyqtSignal
from ui.ui_app import Ui_MainWindow
from system_hotkey import SystemHotkey

from app.init_resource import global_var
from operation.gm_check import play_sound_to_alarm
from control.GMCheckDialog import GMCheckDialog


class App(QMainWindow, Ui_MainWindow):
    sig_hotkey = pyqtSignal(str)
    sig_gm_check = pyqtSignal(str)

    def __init__(self, parent=None):
        super(App, self).__init__(parent)
        self.setupUi(self)

        self.sig_hotkey.connect(self.handleHotKeyEvent)
        self.sig_gm_check.connect(self.showGMCheckDialog)

        self.hk_start_pause = SystemHotkey()
        self.hk_stop = SystemHotkey()
        self.hk_start_pause.register(('f10',), callback=lambda x: self.sendHotKeySig('f10'))
        self.hk_stop.register(('f11',), callback=lambda x: self.sendHotKeySig('f11'))

    def sendHotKeySig(self, i_str):
        self.sig_hotkey.emit(i_str)

    def handleHotKeyEvent(self, i_str):
        if i_str == 'f10':
            # 开始 / 暂停
            self.OpCtrl.clicked_for_start_pause_button()
        if i_str == 'f11':
            # 停止
            self.OpCtrl.clicked_for_end_button()

    def showGMCheckDialog(self, i_str):
        # 启动警报音的播放线程
        sig_dic = global_var["process_sig"]
        sig_mutex = global_var["process_sig_lock"]
        t = threading.Thread(target=play_sound_to_alarm, args=(sig_dic, sig_mutex))
        t.start()

        # 展示弹窗信息
        dialog = GMCheckDialog(self)
        dialog.show()
