import time

import cv2
import numpy as np
import win32gui

from utils.capture_utils import WinDCApiCap
from utils.simulate_utils import KeyboardSimulate as kb, MouseSimulate as ms
from utils.win_utils import get_bdo_rect
from utils.muti_utils import OverSig


def skil_action():
    # 强：蝶旋风
    kb.press("shift")
    ms.click()
    kb.release("shift")
    time.sleep(1.4)

    # 强：飓风/
    kb.press("space")
    time.sleep(1)
    kb.release("space")
    time.sleep(0.5)


def call_black_wizard_to_finish_task():
    kb.press_and_release("/")
    time.sleep(1.5)
    kb.press_and_release("r")
    time.sleep(0.1)
    kb.press_and_release("esc")


def back_call_place():
    kb.press_and_release("T")
    time.sleep(1.5)


def open_bag():
    kb.press_and_release('i')
    time.sleep(0.75)


def get_call_volume_pos(hwnd):
    assert win32gui.IsWindowEnabled(hwnd), True
    cur_windows_left, cur_windows_top, _, _ = get_bdo_rect(hwnd)
    cap = WinDCApiCap(hwnd)
    sc_hots = cap.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/cellVolume.bmp")
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        return cur_windows_left + pt_left + 3, cur_windows_top + pt_top + 3
    return None


def use_call_volume(pos):
    ms.move(pos[0], pos[1], duration=0.1)
    time.sleep(0.2)
    ms.click(ms.RIGHT)
    time.sleep(1)
    kb.press_and_release("return")


def close_bag():
    kb.press_and_release("esc")
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


def old_action(hwnd):
    is_call_volume_over = True

    reposition_before_call()

    open_bag()

    cell_volume(hwnd)

    close_bag()

    if is_call_volume_over:
        raise StopIteration("call volume is all over!")

    # 从成功使用召唤券到第一个boss出现
    time.sleep(35)

    reposition_after_call()

    skil_action()

    # 从成功使用召唤券到第二个boss出现
    time.sleep(11.25)

    skil_action()

    # 等待任务结束展示
    time.sleep(2.5)

    call_black_wizard_to_finish_task()


def cell_volume(hwnd):
    """
    寻找背包里的卷轴并右击使用召唤
    :param hwnd:
    :return:
    """
    find = False
    retry_scroll_cnt = 0
    max_retry_scroll_cnt = 16
    bag_ui_pos = get_bag_ui_pos(hwnd)
    while retry_scroll_cnt <= max_retry_scroll_cnt:
        ms.move(bag_ui_pos[0] - 30, bag_ui_pos[0]- 30, duration=0.05)
        call_volume_pos = get_call_volume_pos(hwnd)
        if call_volume_pos is not None:
            use_call_volume(call_volume_pos)
            find = True
            break
        else:
            # if bag_ui_pos is None:
            #     bag_ui_pos = get_bag_ui_pos(hwnd)
            if bag_ui_pos is not None:
                ms.move(bag_ui_pos[0], bag_ui_pos[1], duration=0.1)
                ms.scroll(0, 100, scroll_type=ms.SCROLLDOWN)
                ms.scroll(0, 100, scroll_type=ms.SCROLLDOWN)
                ms.scroll(0, 100, scroll_type=ms.SCROLLDOWN)
                ms.scroll(0, 100, scroll_type=ms.SCROLLDOWN)
            retry_scroll_cnt += 4
            continue

    if find:
        return
    else:
        raise OverSig




