import time

import cv2
import numpy as np
import win32gui

from utils.capture_utils import WinDCApiCap
from utils.simulate_utils import KeyboardSimulate as kb, MouseSimulate as ms
from utils.win_utils import get_bdo_rect


def skill_action():
    # 强：蝶旋风
    kb.press("left shift")
    ms.click()
    kb.release("left shift")
    time.sleep(1.4)

    # 强：飓风/
    kb.press("space")
    time.sleep(1)
    kb.release("space")
    time.sleep(0.5)

def skill_action2():
    # 强：骤雨
    kb.press("left shift")
    kb.press_and_release("Q")
    kb.release("left shift")


def call_black_wizard_to_finish_task():
    kb.press_and_release("/")
    time.sleep(1.5)
    kb.press_and_release("r")
    time.sleep(0.5)
    kb.press_and_release("esc")


def back_call_place():
    kb.press_and_release("T")
    time.sleep(1.5)


def open_bag():
    kb.press_and_release('i')
    time.sleep(0.75)


def use_scroll(pos):
    ms.move(pos[0], pos[1], duration=0.1)
    time.sleep(0.2)
    ms.click(ms.RIGHT)
    time.sleep(1)
    kb.press_and_release("return")


def close_bag():
    kb.press_and_release("i")
    time.sleep(0.5)


def reposition_after_call():
    kb.press("shift")
    kb.press_and_release("s")
    kb.release("shift")
    time.sleep(0.5)


def reposition_before_call():
    """
    任务结束后下一次战斗开始之前
    :return:
    """
    kb.press_and_release("t")
    time.sleep(2)


def get_bag_ui_pos(hwnd):
    assert win32gui.IsWindowEnabled(hwnd), True
    cur_windows_left, cur_windows_top, _, _ = get_bdo_rect(hwnd)
    cap = WinDCApiCap(hwnd)
    sc_hots = cap.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/bag.bmp")
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        return cur_windows_left + pt_left + 200, cur_windows_top + pt_top + 200
    return None


def get_market_npc_gps_pos(hwnd):
    cap = WinDCApiCap(hwnd)
    if not cap.is_available():
        return
    cur_windows_left, cur_windows_top, _, _ = get_bdo_rect(hwnd)
    sc_hots = cap.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/marketPos.bmp")
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        return cur_windows_left + pt_left + 5, cur_windows_top + pt_top + 5
    return None


def reset_viewer():
    """
    调整视角
    :return:
    """
    ms.wheel(-1000)


def get_repair_weapons_icon_pos(hwnd):
    """
    获取修理icon的位置
    :param hwnd:
    :return:
    """
    cap = WinDCApiCap(hwnd)
    if not cap.is_available():
        return
    cur_windows_left, cur_windows_top, _, _ = get_bdo_rect(hwnd)
    sc_hots = cap.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/repairIcon.bmp")
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        return cur_windows_left + pt_left + 5, cur_windows_top + pt_top + 5
    return None


def repair_weapons_by_tent(hwnd):
    # 利用快捷键打开帐篷
    kb.press("alt")
    kb.press_and_release("3")
    kb.release("alt")

    time.sleep(2)

    # 利用快捷键打开修理
    kb.press("alt")
    kb.press_and_release("4")
    kb.release("alt")

    time.sleep(1)

    # 定位修理图标修理
    icon_pos = get_repair_weapons_icon_pos(hwnd)
    if icon_pos:
        ms.move(icon_pos[0], icon_pos[1], duration=0.1)
        ms.click()

    kb.press_and_release('return')

    time.sleep(1)
    kb.press_and_release('esc')

    time.sleep(0.5)

    # 利用快捷键回收帐篷
    kb.press("alt")
    kb.press_and_release("5")
    kb.release("alt")
    kb.press_and_release('return')


def get_market_management_gps_pos(hwnd):
    cap = WinDCApiCap(hwnd)
    if not cap.is_available():
        return
    cur_windows_left, cur_windows_top, _, _ = get_bdo_rect(hwnd)
    sc_hots = cap.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/marketManagementButton.bmp")
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        return cur_windows_left + pt_left + 5, cur_windows_top + pt_top + 5
    return None


def chat_with_LucyBenKun_to_show_market_ui(hwnd):
    """
    和鲁西比恩坤交流并打开交易所内部ui
    :param hwnd
    :return:
    """
    kb.press_and_release("R")
    time.sleep(0.5)

    kb.press_and_release("2")
    time.sleep(0.5)

    pos = get_market_management_gps_pos(hwnd)
    if pos is None:
        # TODO raise RetrySig(redo=["kb::esc", "kb::esc", "kb::esc"])
        return False
    ms.move(pos[0], pos[1], duration=0.1)
    ms.click()
    return True


def into_action_state():
    """
    进入动作模式
    :return:
    """
    ms.click()
