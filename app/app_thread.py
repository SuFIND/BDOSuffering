import threading
import time
import traceback
import pythoncom
from winsound import PlaySound, SND_FILENAME
import smtplib
from email.mime.text import MIMEText

import cv2

from utils.muti_utils import CanStopThread, ExecSig
from utils.win_utils import set_unmuted
from utils.log_utils import Logger
from utils.capture_utils import WinDCApiCap
from app.init_resource import global_var
from operation.classics_op import SkillAction


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

        exec_sig = ExecSig(sig_dic, sig_mutex)

        while self._running:
            if exec_sig.is_start() and app.OpCtrl.viewer.StartPauseButton.text() != "暂停 F10":
                app.OpCtrl.button_sig.emit("refresh_display:pause")
            if (exec_sig.is_stop() or exec_sig.is_pause()) and app.OpCtrl.viewer.StartPauseButton.text() != "开始 F10":
                app.OpCtrl.button_sig.emit("refresh_display:start")

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
                Logger.error(err)
                break

        pythoncom.CoUninitialize()


class EmailThread(CanStopThread):
    def run(self, subject, message, from_addr, to_addr, password, smtp_server, smtp_port):
        """
        邮件发送线程
        :param subject: 邮件主题
        :param message: 邮件内容
        :param from_addr: 发件人邮箱地址
        :param to_addr: 收信人邮箱地址
        :param password: 发件人邮箱密码
        :param smtp_server: smtp邮件服务器地址
        :param smtp_port: smtp邮件服务器端口
        :return:
        """
        try:
            # 创建一个MIMEText对象，该对象包含您要发送的消息
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = from_addr
            msg['To'] = to_addr

            # 创建SMTP对象并连接到您的邮件服务器
            smtp = smtplib.SMTP(smtp_server, smtp_port)
            smtp.starttls()
            smtp.login(from_addr, password)

            # 发送电子邮件
            smtp.sendmail(from_addr, [to_addr], msg.as_string())

            # 断开与邮件服务器的连接
            smtp.quit()
        except Exception as e:
            err = traceback.format_exc()
            Logger.error(err)


class ShowImgThread(CanStopThread):
    def run(self, hwnd):
        try:
            # 获取截图
            win_dc = WinDCApiCap(hwnd)
            src = win_dc.get_hwnd_screenshot_to_numpy_array()

            # 获取截图的长宽高
            or_h, or_w = src.shape[:2]

            # 切割获取右下角的玩家聊天框小图减少干扰
            start_row = round(or_h / 4 * 3)
            end_row = or_h
            start_col = 0
            end_col = round(or_w / 4)
            cropped = src[start_row:end_row, start_col:end_col, :]
            cv2.imshow("demo viewer", cropped)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except Exception as e:
            err = traceback.format_exc()
            Logger.error(err)
            cv2.destroyAllWindows()

    def terminate(self):
        cv2.destroyAllWindows()


def start_thread_play_skill_group(group_one_config):
    """
    启动一个线程播放配置的技能动作
    :param group_one_config:
    :return:
    """
    def _run():
        exc_unit = SkillAction([group_one_config])
        exc_unit.run()

    t = threading.Thread(target=_run)
    t.start()
