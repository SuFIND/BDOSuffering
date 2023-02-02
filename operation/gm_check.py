# -*- coding: utf-8 -*-
"""
用于检测是否有GM出现的足迹
"""
import datetime
import time

import cv2
from win32gui import FindWindow, IsWindowEnabled
from utils.capture_utils import WinDCApiCap
from utils.cv_utils import static_color_pix_count


def GMCheckLoop(sig_dic, sig_mutex, msg_queue,
                window_title: str, window_class: str, gm_chat_color: tuple = None, gm_check_interval: int = 1800,
                find_pix_max_count=500):
    """
    Loop for GM check
    :param sig_dic:
    :param sig_mutex:
    :param msg_queue:
    :param window_title:
    :param window_class:
    :param gm_chat_color: GM聊天时字体的颜色
    :param gm_check_interval: GM查找的时间间隔默认30分钟 -> 1800s
    :param find_pix_max_count:  报警阀值
    :return:
    """
    last_find_at = datetime.datetime.now() - datetime.timedelta(seconds=gm_check_interval)
    gm_chat_color = () if gm_chat_color is None else (57, 181, 47)

    hwnd = FindWindow(window_class, window_title)
    obj = WinDCApiCap(hwnd)
    while True:
        if not obj.is_available():
            # is mean process is exits
            break

        # 获取截图
        sc_np = obj.get_hwnd_screenshot_to_numpy_array()

        # 获取截图的长宽高
        or_h, or_w = sc_np.shape[:2]

        # 切割获取右下角的玩家聊天框小图减少干扰
        start_row = round(or_h / 4 * 3)
        end_row = or_h
        start_col = 0
        end_col = round(or_w / 4)
        cropped = sc_np[start_row:end_row, start_col:end_col, :3]
        count = static_color_pix_count(cropped, gm_chat_color, threshold=0.6)

        if count > find_pix_max_count:
            with sig_mutex:
                sig_dic.update({"start": False, "stop": True, "pause": False})
            break

        time.sleep(5)
