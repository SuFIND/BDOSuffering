import time
import traceback
import pythoncom
from winsound import PlaySound, SND_FILENAME
import smtplib
from email.mime.text import MIMEText

from utils.muti_utils import CanStopThread
from utils.win_utils import set_unmuted
from utils.log_utils import Logger
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


