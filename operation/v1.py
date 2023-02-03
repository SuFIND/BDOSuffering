import time
import traceback

from win32gui import FindWindow

from app.init_resource import global_var
from utils.log_utils import Logger
from operation.classics_op import open_bag, close_bag, reposition_after_call, reposition_before_call, cell_volume, \
    skil_action, call_black_wizard_to_finish_task
from utils.muti_utils import StopSig, OverSig, FormatMsg

fmmsg = FormatMsg(source="模拟动作")


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
    Logger.set_log_name("action_simulate.log")
    start_at = time.perf_counter()
    exec_cnt = 0

    try:
        # 为当前进程的global_var的必要资源进行初始化
        global_var["process_sig"] = sig_dic
        global_var["process_sig_lock"] = sig_mutex
        global_var["process_msg_queue"] = msg_queue

        hwnd = FindWindow(window_class, window_title)
        if hwnd == 0:
            msg_queue.put(fmmsg.to_str(
                "无法检测到黑色沙漠窗口句柄！请先打开游戏或检查 config/my_config.toml 中的 BDO.window_class 是否与游戏窗口名一致",
                level="error"))
            return 

        msg_queue.put(fmmsg.to_str("开始准备召唤!", level="info"))
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
            msg_queue.put(
                fmmsg.to_str(f"完成第{exec_cnt}次, 约为 {round(exec_cnt / ((now_at - start_at) / 3600), 2)}个/小时",
                             level="info"))
    except OverSig:
        now_at = time.perf_counter()
        msg_queue.put(fmmsg.to_str("完成了所有召唤书的召唤，停止模拟！", level="info"))
    except StopSig as e:
        msg_queue.put(fmmsg.to_str("接受到停止请求，停止模拟!", level="info"))
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)
        now_at = time.perf_counter()
        msg_queue.put(fmmsg.to_str("意外退出!请查看日志文件定位错误。", level="error"))
    finally:
        msg_queue.put(fmmsg.to_str(f"运行时长{round((now_at - start_at) / 60)}分钟", level="info"))
    with sig_mutex:
        sig_dic.update({"stop": True, "start": False, "pause": False})
