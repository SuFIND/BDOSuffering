# -*- coding: utf-8 -*-
"""
用于检测是否有GM出现的足迹
"""
import math
import time
import traceback
import os

import cv2
from win32gui import FindWindow

from utils.capture_utils import WinDCApiCap
from utils.cv_utils import static_color_pix_count
from utils.muti_utils import FormatMsg, ExecSig

fmmsg = FormatMsg(source="GM检测")


def GM_check_loop(sig_dic, sig_mutex, msg_queue,
                  window_title: str, window_class: str, gm_chat_color: tuple, gm_check_cool_time: int,
                  find_pix_max_count: int, gui_params: dict):
    """
    Loop for GM check
    :param sig_dic:
    :param sig_mutex:
    :param msg_queue:
    :param window_title:
    :param window_class:
    :param gm_chat_color: GM聊天时字体的颜色
    :param gm_check_cool_time: GM检测报警的冷却时间默认30分钟 -> 1800s
    :param find_pix_max_count:  报警阀值，超出这个数量的像素会进行警报
    :param gui_params:
    :return:
    """
    from utils.log_utils import Logger

    # 初始化该进程的日志模块
    Logger.set_log_name("GM_check.log")

    # 信号量模块
    exec_sig = ExecSig(sig_dic, sig_mutex)

    # 最后一次发现GM行径的事件
    last_find_at = time.perf_counter() - gm_check_cool_time

    # 检测窗口句柄
    hwnd = FindWindow(window_class, window_title)
    if hwnd == 0:
        # 如果句柄地址为0代表未能找到句柄则异常退出
        msg_queue.put(fmmsg.to_str(
            "无法检测到黑色沙漠窗口句柄！请先打开游戏或检查 config/basic.toml 中的 BDO.window_title 是否与游戏窗口名一致",
            level="error"))
        return

    win_dc = WinDCApiCap(hwnd)
    try:
        while True:
            if exec_sig.is_pause():
                time.sleep(3)
                continue
            if exec_sig.is_stop():
                break

            if not win_dc.is_available():
                # is mean process is exits
                msg_queue.put(fmmsg.to_str("无法检测到黑色沙漠窗口句柄！", level="error"))
                break

            # 获取截图
            sc_np = win_dc.get_hwnd_screenshot_to_numpy_array()

            # 获取截图的长宽高
            or_h, or_w = sc_np.shape[:2]

            # 切割获取右下角的玩家聊天框小图减少干扰
            start_row = round(or_h / 4 * 3)
            end_row = or_h
            start_col = 0
            end_col = round(or_w / 4)
            cropped = sc_np[start_row:end_row, start_col:end_col, :3]
            count = static_color_pix_count(cropped, gm_chat_color, threshold=0.6)

            # 如果计算出的相近颜色像素值大于阀值，且距离上一次警报已经超出冷却时间
            now_at = time.perf_counter()
            if count > find_pix_max_count and now_at - last_find_at > gm_check_cool_time:
                exec_sig.set_pause()
                last_find_at = now_at
                msg_queue.put(fmmsg.to_str("发现GM进行检测，模拟仿真程序紧急停止！", level="warning"))
                msg_queue.put("action::show_gm_modal")

                # save img
                if gui_params["collectImgGMCheck"]:
                    dir = os.path.join("log", "img", "GMCheck")
                    if os.path.exists(dir):
                        os.makedirs(dir)
                    img_name = str(time.time()).replace(".", "")
                    abs_path = os.path.join(dir, f"{img_name}.jpg")

                    cv2.imwrite(abs_path, sc_np)

                Logger.info("发现GM督查")

            # 检测间隔
            time.sleep(3)
    except Exception as e:
        err = traceback.format_exc()
        Logger.error(err)
    finally:
        Logger.shutdown()


