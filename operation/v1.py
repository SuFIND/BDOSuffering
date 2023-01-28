import time
import traceback

from win32gui import FindWindow

from app.init_resource import global_var
from utils.log_utils import Logger
from operation.classics_op import open_bag, close_bag, reposition_after_call, reposition_before_call, cell_volume, \
    skil_action, call_black_wizard_to_finish_task
from utils.muti_utils import StopSig, OverSig


class FormatMsg:
    def __init__(self, msg, level="info", source=""):
        self.msg = msg
        self.level = level
        self.source = source

    def to_str(self):
        return self.__str__()

    def __str__(self):
        return f"{self.level}${self.source}${self.msg}"


def start_action(sig_dic, sig_mutex, msg_queue,
                 window_title: str, window_class: str):
    """

    :param sig_dic: 信号字典
    :param sig_mutex:
    :param msg_queue:
    :param window_title:
    :param window_class:
    :return:
    """
    start_at = time.perf_counter()
    exec_cnt = 0

    try:
        # 为当前进程的global_var的必要资源进行初始化
        global_var["process_sig"] = sig_dic
        global_var["process_sig_lock"] = sig_mutex
        global_var["process_msg_queue"] = msg_queue

        hwnd = FindWindow(window_class, window_title)
        if hwnd == 0:
            msg_queue.put(FormatMsg("无法找到黑色沙漠窗口句柄！", "error", "模拟动作").to_str())
            raise OSError("无法找到黑色沙漠窗口句柄！")

        msg_queue.put(FormatMsg("开始准备召唤!", "info", "模拟动作").to_str())
        with sig_mutex:
            sig_dic.update({"start": True, "stop": False, "pause": False})
        while True:
            with sig_mutex:
                if sig_dic["pause"]:
                    time.sleep(1)
                    continue
                if sig_dic["stop"]:
                    raise StopSig
            funcs = [
                (reposition_before_call, ()),  # 按t回到可以召唤球的地点
                (open_bag, ()),  # 打开背包
                (cell_volume, (hwnd,)),  # 找到召唤书并召唤
                (close_bag, ()),  # 关闭背包
                (time.sleep, (35,)),  # 等待直到第一个boss可被攻击
                (reposition_after_call, ()),  # 进行一个后撤步
                (skil_action, ()),  # 释放攻击动作
                (time.sleep, (11.25,)),  # 等待第二个boss出现
                (skil_action, ()),  # 释放攻击动作
                (time.sleep, (2.5,)),  # 等待任务结束展示
                (call_black_wizard_to_finish_task, ()),
            ]
            for func, args in funcs:

                can_run = False
                while not can_run:
                    with sig_mutex:
                        # 如果此时的信号是中断则
                        if sig_dic["stop"]:
                            raise StopSig
                        # 如果此时的信号是暂停则睡眠一秒
                        elif sig_dic["pause"]:
                            time.sleep(1)
                            continue

                    can_run = True

                func(*args)
            exec_cnt += 1
            now_at = time.perf_counter()
            msg_queue.put(FormatMsg(f"完成第{exec_cnt}次, 约为 {round(exec_cnt / ((now_at - start_at) / 3600), 2)}个/小时",
                                    "info",
                                    "模拟动作").to_str())
    except OverSig:
        now_at = time.perf_counter()
        msg_queue.put(FormatMsg("完成了所有召唤书的召唤，停止模拟！", "info", "模拟动作").to_str())
        msg_queue.put(FormatMsg(f"运行时长{round((now_at - start_at) / 60)}分钟", "info", "模拟动作").to_str())
    except StopSig as e:
        msg_queue.put(FormatMsg("接受到停止请求，停止模拟!", "info", "模拟动作").to_str())
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)
        now_at = time.perf_counter()
        with sig_mutex:
            sig_dic.update({"stop": True, "start": False, "pause": False})
        msg_queue.put(FormatMsg("意外退出!请查看日志文件定位错误。", "error", "模拟动作").to_str())
        msg_queue.put(FormatMsg(f"运行时长{round((now_at - start_at) / 60)}分钟", "info", "模拟动作").to_str())
