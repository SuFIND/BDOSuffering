import time
import traceback

from win32gui import FindWindow

from app.init_resource import global_var
from app.init_func import init_labels_dic
from utils.log_utils import Logger
import operation.classics_op as classics_op
import operation.ai_op as ai_op
# from operation.classics_op import open_bag, close_bag, reposition_after_call, reposition_before_call, \
#     skil_action, call_black_wizard_to_finish_task, repair_weapons_by_tent, chat_with_LucyBenKun_to_show_market_ui, \
#     reset_viewer, into_action_state
# from operation.ai_op import back_to_market, cell_volume
from utils.muti_utils import StopSig, OverSig, FormatMsg
from utils.cv_utils import Detector

fmmsg = FormatMsg(source="模拟动作")


def start_action(sig_dic, sig_mutex, msg_queue, window_title: str, window_class: str, onnx_path: str,
                 label_dic_path: str):
    """

    :param sig_dic: 信号字典
    :param sig_mutex: 信号字典的锁
    :param msg_queue: 向GUI更新日志心细的消息队列
    :param window_title:
    :param window_class:
    :param label_dic_path: 模型标签字典地址
    :param onnx_path: onnx模型文件地址
    :return:
    """
    Logger.set_log_name("action_simulate.log")
    start_at = time.perf_counter()
    exec_cnt = 0

    hwnd = FindWindow(window_class, window_title)
    if hwnd == 0:
        msg_queue.put(fmmsg.to_str(
            "无法检测到黑色沙漠窗口句柄！请先打开游戏或检查 config/my_config.toml 中的 BDO.window_class 是否与游戏窗口名一致",
            level="error"))
        return

    label_dic = init_labels_dic(label_dic_path)
    detector = Detector(onnx_path, label_dic)

    try:
        # 为当前进程的global_var的必要资源进行初始化
        global_var["process_sig"] = sig_dic
        global_var["process_sig_lock"] = sig_mutex
        global_var["process_msg_queue"] = msg_queue

        msg_queue.put(fmmsg.to_str("开始准备召唤!", level="info"))
        with sig_mutex:
            sig_dic.update({"start": True, "stop": False, "pause": False})

        # pre hook
        classics_op.reset_viewer()
        time.sleep(1)
        classics_op.into_action_state()
        time.sleep(2)
        classics_op.reposition_after_call()
        time.sleep(2)

        # loop hook
        while True:
            with sig_mutex:
                if sig_dic["pause"]:
                    time.sleep(1)
                    continue
                if sig_dic["stop"]:
                    raise StopSig
            funcs = [
                (classics_op.reposition_before_call, ()),  # 按t回到可以召唤球的地点
                (classics_op.open_bag, ()),  # 打开背包
                (ai_op.use_Pila_Fe_scroll, (detector, hwnd,)),  # 找到召唤书并召唤
                (classics_op.close_bag, ()),  # 关闭背包
                (time.sleep, (15,)),
                (classics_op.reposition_after_call, ()),  # 进行一个后撤步
                (time.sleep, (19.5,)),  # 等待直到第一个boss可被攻击
                (classics_op.skil_action, ()),  # 释放攻击动作
                (time.sleep, (11.25,)),  # 等待第二个boss出现
                (classics_op.skil_action, ()),  # 释放攻击动作
                (time.sleep, (2.5,)),  # 等待任务结束展示
                (classics_op.call_black_wizard_to_finish_task, ()),
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
        msg_queue.put(fmmsg.to_str("完成了所有召唤书的召唤！", level="info"))

        # back hook
        # 关闭背包
        classics_op.close_bag()
        time.sleep(1)

        # 修理当前装备
        classics_op.repair_weapons_by_tent(hwnd)
        time.sleep(2)
        # 回到交易所NPC处
        ai_op.back_to_market(detector, hwnd)
        # 路上的预计耗时为127秒,加上冗余时间保守设置为180秒
        time.sleep(180)

        # TODO step 3 合成召唤券
        classics_op.chat_with_LucyBenKun_to_show_market_ui(hwnd)

        # TODO step 4 回到召唤地点

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
