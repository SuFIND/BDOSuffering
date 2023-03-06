import time

import cv2
import numpy as np
from win32gui import IsWindowEnabled

from utils.capture_utils import WinDCApiCap
from utils.simulate_utils import KeyboardSimulate as kb, MouseSimulate as ms
from utils.win_utils import get_bdo_rect


def skill_action(has_been_play_time: int):
    has_been_play_time += 1
    if has_been_play_time % 2 != 0:
        skill_group_1()
    else:
        skill_group_2()


def skill_group_1():
    # 角色施展这套动作的游戏内硬直耗时
    expect_cost = 3.5

    start_at = time.process_time()
    # 强：蝶旋风
    kb.press("left shift")
    ms.click()
    kb.release("left shift")
    time.sleep(1.4)

    # 强：飓风
    kb.press("space")
    time.sleep(1)
    kb.release("space")
    time.sleep(0.5)

    # 程序仿真这套动作的耗时
    end_at = time.process_time()
    exec_cost = end_at - start_at

    # 需要额外补充等待的睡眠时长
    wait = expect_cost - exec_cost
    time.sleep(wait)


def skill_group_2():
    # 角色施展这套动作的游戏内硬直耗时
    expect_cost = 8

    start_at = time.process_time()
    # 左移动
    kb.press("left shift")
    kb.press_and_release("D")
    kb.release("left shift")

    time.sleep(1)

    # 右移动
    kb.press("left shift")
    kb.press_and_release("A")
    kb.release("left shift")

    time.sleep(1)

    # 强：骤雨
    kb.press("left shift")
    kb.press_and_release("Q")
    kb.release("left shift")

    # 程序仿真这套动作的耗时
    end_at = time.process_time()
    exec_cost = end_at - start_at

    # 需要额外补充等待的睡眠时长
    wait = expect_cost - exec_cost
    time.sleep(wait)


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
    assert IsWindowEnabled(hwnd), True
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


def repair_weapons_by_tent(hwnd, setTentShortcut: str, tentRepairWeaponsShortcut: str,
                           recycleTentShortcut: str) -> None:
    # 利用快捷键打开帐篷
    kb.press("alt")
    kb.press_and_release(setTentShortcut)
    kb.release("alt")

    time.sleep(2)

    # 利用快捷键打开修理
    kb.press("alt")
    kb.press_and_release(tentRepairWeaponsShortcut)
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
    kb.press_and_release(recycleTentShortcut)
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


def calculate_the_elapsed_time_so_far(start: float):
    """
    计算从输入的开始时间为止到目前所消耗的时间
    :param start:
    :return:
    """
    now = time.perf_counter()
    return now - start


def set_timer_key_value(dic: dict, key: str, value: int = None) -> None:
    if value is None:
        value = time.perf_counter()
    dic[key] = value


class ActionExec:
    action_mapping = {
        "wait": time.sleep,

        "KBPress": kb.press,
        "KBRelease": kb.release,
        "KBPressAndRelease": kb.press_and_release,

        "MSClick": ms.click,
    }

    def __init__(self, action_queue):
        self.queue = action_queue

    def run(self):
        for action in self.queue:
            func = self.action_mapping[action["type"]]
            args = []
            if action["type"] in {"KBPress", "KBRelease", "KBPressAndRelease", "MSClick"}:
                args = [action["key"]]
            if action["type"] in {"wait"}:
                args = [action["sec"]]

            func(*args)


class SkillAction:
    def __init__(self, groups):
        self.groups = []
        self.cur_exec_times = 0

        for group in groups:
            cost = group["groupExpectCost"]
            actions = [ActionExec(one['pipelines']) for one in group["blocks"]]
            self.groups.append({
                "expectCost": cost,
                "actions": actions,
            })

    def reset_exec_times(self):
        self.cur_exec_times = 0

    def run(self):
        cur_group_idx = self.cur_exec_times % len(self.groups)
        start = time.perf_counter()
        for action in self.groups[cur_group_idx]["actions"]:
            action.run()

        self.cur_exec_times += 1

        end = time.perf_counter()
        exec_cost = end - start
        wait = self.groups[cur_group_idx]["expectCost"] - exec_cost
        wait = max(0, wait)
        time.sleep(wait)
