import time
import traceback
import pythoncom
from winsound import PlaySound, SND_FILENAME

from utils.muti_utils import CanStopThread
from utils.win_utils import set_unmuted
from app.init_resource import global_var


class MsgHandleThread(CanStopThread):
    def run(self, app):
        """
        监听进程共享的消息队列刷新进入日志, 更新界面标志
        :return:
        """
        # 从全局变量中获取消息队列
        msg_queue = global_var["process_msg_queue"]
        # 互斥锁及多进程共享的信号字典
        sig_dic = global_var["process_sig"]
        sig_mutex = global_var["process_sig_lock"]

        while self._running:
            with sig_mutex:
                try:
                    if sig_dic["start"] and app.OpCtrl.viewer.StartPauseButton.text() != "暂停 F10":
                        app.OpCtrl.button_sig.emit("refresh_display:pause")
                    if (sig_dic["pause"] or sig_dic["stop"]) and app.OpCtrl.viewer.StartPauseButton.text() != "开始 F10":
                        app.OpCtrl.button_sig.emit("refresh_display:start")
                except RuntimeError:
                    pass

            if not msg_queue.empty():
                msg_str: str = msg_queue.get(block=False)
                if msg_str == "action::show_gm_modal":
                    app.sig_gm_check.emit("show_gm_modal")
                elif msg_str.startswith("msg::"):
                    level, src, msg = msg_str[5:].split("$")
                    app.LogCtrl.add_log(msg=f"{src}->{msg}", level=level)
            else:
                time.sleep(1)


class GMAlarmThread(CanStopThread):
    def run(self):
        # 互斥锁及多进程共享的信号字典
        sig_dic = global_var["process_sig"]
        sig_mutex = global_var["process_sig_lock"]

        pythoncom.CoInitialize()

        while self._running:
            try:
                with sig_mutex:
                    if sig_dic["stop"]:
                        break
                set_unmuted()
                PlaySound("data/sound/alarm.wav", SND_FILENAME)
            except Exception as e:
                err = traceback.format_exc()
                break

        pythoncom.CoUninitialize()
