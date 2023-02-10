import os
import time
import cv2
import numpy as np
import operation.classics_op as classics_op
from utils.capture_utils import WinDCApiCap
from utils.simulate_utils import MouseSimulate as ms, KeyboardSimulate as kb
from utils.win_utils import get_bdo_rect


def back_to_market(detector, hwnd, debug=False):
    """
    打开寻找NPC UI找到道具交易所并按T键自动导航
    :return:
    """
    # 利用快捷键打开寻找NPC的UI
    kb.press("alt")
    kb.press_and_release("6")
    kb.release("alt")

    time.sleep(0.5)

    # 利用模型推理确认寻找NPC-UI的位置
    wdac = WinDCApiCap(hwnd)
    c_left, c_top, _, _ = get_bdo_rect(hwnd)
    img = wdac.get_hwnd_screenshot_to_numpy_array(collection=debug, save_dir="logs/img/FindNPCUI")
    infer_rst = detector.infer(img)

    if "ui$Find NPC" not in infer_rst:
        return

    bbox_tup = infer_rst["ui$Find NPC"][0]["bbox"]
    target_pos = (bbox_tup[0] + bbox_tup[2]) / 2, (bbox_tup[1] + bbox_tup[3]) / 2 / 2
    target_pos = c_left + target_pos[0], c_top + target_pos[1]
    ms.move(target_pos[0], target_pos[1], duration=0.1)
    ms.wheel(-100)
    ms.wheel(-100)
    ms.wheel(-100)
    ms.wheel(-100)

    # 等待UI动画结束
    time.sleep(2)

    market_npc_icon_pos = classics_op.get_market_npc_gps_pos(hwnd)
    ms.move(market_npc_icon_pos[0], market_npc_icon_pos[1], duration=0.1)
    ms.click()
    kb.press_and_release("T")

    # 再次利用快捷键打开寻找NPC的UI
    kb.press_and_release("esc")


def get_bag_ui_bbox(detector, win_dc: WinDCApiCap, bdo_rect: list[int], debug=False):
    c_left, c_top, _, _ = bdo_rect
    img = win_dc.get_hwnd_screenshot_to_numpy_array(collection=debug, save_dir="logs/img/BagUI")
    infer_rst = detector.infer(img)
    if "ui$Bag" not in infer_rst:
        return None

    bbox_tup = infer_rst["ui$Bag"][0]["bbox"]
    return bbox_tup[0] + c_left, bbox_tup[1] + c_top, bbox_tup[2] + c_left, bbox_tup[3] + c_top


def get_Pila_Fe_scroll_pos_by_model(detector, win_dc: WinDCApiCap, bdo_rect: list[int], debug=False):
    c_left, c_top, _, _ = bdo_rect
    img = win_dc.get_hwnd_screenshot_to_numpy_array(collection=debug, save_dir="logs/img/PilaFeScroll")
    infer_rst = detector.infer(img)
    if "item$Pila Fe Scroll" not in infer_rst:
        return None

    bbox_tup = infer_rst["item$Pila Fe Scroll"][0]["bbox"]
    return (bbox_tup[0] + bbox_tup[2]) / 2 + c_left, (bbox_tup[1] + bbox_tup[3]) / 2 + c_top


def get_Pila_Fe_scroll_pos_by_temple(win_dc: WinDCApiCap, client_rect) -> [tuple, None]:
    """
    用过模版匹配找到卷轴中心点的位置
    :param win_dc:
    :param client_rect:
    :return:
    """
    if not win_dc.is_available():
        return None
    cur_windows_left, cur_windows_top, _, _ = client_rect
    sc_hots = win_dc.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/PilaFeScroll.bmp")
    template_h, template_w = template.shape[:2]
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        return cur_windows_left + pt_left + template_w / 2, cur_windows_top + pt_top + template_h / 2
    return None


def use_Pila_Fe_scroll(detector, hwnd, debug=False):
    """
    寻找背包里的卷轴并右击使用召唤
    :param save_dir:
    :param debug:
    :param detector: 模型检测器
    :param hwnd: 句柄
    :return:
    """
    find = False
    item_pos = None
    retry_scroll_cnt = 0
    max_retry_scroll_cnt = 16
    win_dc = WinDCApiCap(hwnd)
    bdo_rect = get_bdo_rect(hwnd)

    bag_ui_bbox = get_bag_ui_bbox(detector, win_dc, bdo_rect, debug=debug)
    if bag_ui_bbox is None:
        return find, item_pos

    into_pos = (bag_ui_bbox[0] + bag_ui_bbox[2]) / 2, (bag_ui_bbox[1] + bag_ui_bbox[3]) / 2
    out_pos = bag_ui_bbox[0] - 50, bag_ui_bbox[1] - 50
    step = 4
    while retry_scroll_cnt <= max_retry_scroll_cnt:
        ms.move(out_pos[0] - 30, out_pos[0] - 30)
        item_pos = get_Pila_Fe_scroll_pos_by_temple(win_dc, bdo_rect)
        if item_pos is not None:
            find = True
            break
        else:
            ms.move(into_pos[0], into_pos[1], duration=0.1)
            for _ in range(step):
                ms.wheel(-100)
            retry_scroll_cnt += step
            continue

    return find, item_pos


def found_target(detector, hwnd, label, debug=False, save_dir="") -> bool:
    win_dc = WinDCApiCap(hwnd)
    img = win_dc.get_hwnd_screenshot_to_numpy_array(collection=debug, save_dir=save_dir)
    infer_rst = detector.infer(img)
    if label not in infer_rst or len(infer_rst[label]) < 1:
        return False
    return True


def found_Pila_Fe_scroll_using_check_ui(detector, hwnd, debug=False) -> bool:
    return found_target(detector, hwnd, "ui$Pila Fe Scroll Using Check", debug=debug,
                        save_dir="logs/img/PilaFeScrollUsingCheck")


def found_boss_Magram(detector, hwnd, retry: int, debug: bool = False) -> bool:
    """
    发旋目标 “玛格岚”
    :param detector:
    :param hwnd:
    :param retry:
    :param debug:
    :return:
    """
    rst = False
    for i in range(retry + 1):
        rst = rst or found_target(detector, hwnd, "boss$Magram", debug=debug, save_dir="logs/img/Margram")
        if rst:
            break
    return rst


def found_task_over(detector, hwnd, retry: int, debug: bool = False) -> bool:
    """
    发现目标提示“任务结束的标志”
    :param detector:
    :param hwnd:
    :param retry:
    :param debug:
    :return:
    """
    rst = False
    for i in range(retry + 1):
        rst = rst or found_target(detector, hwnd, "flag$Task Over", debug=debug, save_dir="logs/img/TaskOver")
        if rst:
            break
    return rst


def found_flag_deviate_from_destination(detector, hwnd, retry: int, debug: bool = False) -> bool:
    """
    发现目标提示“已看到远方目的地”
    :param detector:
    :param hwnd:
    :param retry:
    :param debug:
    :return:
    """
    rst = False
    for i in range(retry + 1):
        rst = rst or found_target(detector, hwnd, "flag$Deviate from destination", debug=debug,
                                  save_dir="logs/img/DeviateFromDestination")
        if rst:
            break
    return rst


def collect_client_img(hwnd, save_dir):
    win_dc = WinDCApiCap(hwnd)
    win_dc.get_hwnd_screenshot_to_numpy_array(collection=True, save_dir=save_dir)


def get_merge_button_by_temple(win_dc: WinDCApiCap, client_rect) -> [tuple, None]:
    if not win_dc.is_available():
        return None
    cur_windows_left, cur_windows_top, _, _ = client_rect
    sc_hots = win_dc.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/mergeButton.bmp")
    template_h, template_w = template.shape[:2]
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.9
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        return cur_windows_left + pt_left + template_w / 2, cur_windows_top + pt_top + template_h / 2


def clear_bag(detector, hwnd, debug=False):
    """
    呼出仓库女仆清理背包杂物
    :param detector:
    :param hwnd:
    :param debug:
    :return:
    """
    bdo_rect = get_bdo_rect(hwnd)
    win_dc = WinDCApiCap(hwnd)
    c_left, c_top, _, _ = bdo_rect

    kb.press("alt")
    kb.press_and_release("1")
    kb.release("alt")
    time.sleep(1)

    bag_bbox = get_bag_ui_bbox(detector, win_dc, bdo_rect, debug)
    if bag_bbox is not None:
        into_pos = (bag_bbox[0] + bag_bbox[2]) / 2, (bag_bbox[1] + bag_bbox[3]) / 2
        out_pos = bag_bbox[0] - 50, bag_bbox[1] - 50

        step = 4
        cur_step = 0
        max_step = 16
        while cur_step <= max_step:
            ms.move(out_pos[0], out_pos[1])
            img = win_dc.get_hwnd_screenshot_to_numpy_array(collection=debug, save_dir="logs/img/ClearBag")
            infer_rst = detector.infer(img)

            for label in ["item$Memory Fragment", "item$Mutant Bat's Wing", "item$Bashim Mane", "item$Hunter's Seal"]:
                if label not in infer_rst:
                    continue
                for info in infer_rst[label]:
                    item_bbox = info["bbox"]
                    item_center_pos = c_left + (item_bbox[0] + item_bbox[2]) / 2, c_top + (
                                item_bbox[1] + item_bbox[3]) / 2

                    # filter 如果物品的中心点不在背包UI内则不考虑对物品进行移动
                    if not bag_bbox[0] < item_center_pos[0] < bag_bbox[2] \
                            or not bag_bbox[1] < item_center_pos[1] < bag_bbox[3]:
                        continue

                    ms.move(item_center_pos[0], item_center_pos[1], duration=0.1)
                    ms.click(ms.RIGHT)
                    kb.press_and_release("F")
                    kb.press_and_release("return")

            ms.move(into_pos[0], into_pos[1], duration=0.1)
            for i in range(step):
                ms.wheel(-100)
            cur_step += step

    kb.press_and_release("esc")
    kb.press_and_release("esc")


def found_ui_process_bar(detector, hwnd, retry: int, debug: bool = False) -> bool:
    """
    发现目标"进度条"
    :param detector:
    :param hwnd:
    :param retry:
    :param debug:
    :return:
    """
    rst = False
    for i in range(retry + 1):
        rst = rst or found_target(detector, hwnd, "ui$Process Bar", debug=debug, save_dir="logs/img/Process Bar")
        if rst:
            break
    return rst
