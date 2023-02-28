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


def get_bag_ui_bbox(detector, win_dc: WinDCApiCap, bdo_rect: list[int], debug=False) -> [tuple, None]:
    c_left, c_top, _, _ = bdo_rect
    img = win_dc.get_hwnd_screenshot_to_numpy_array(collection=debug, save_dir="logs/img/BagUI")
    infer_rst = detector.infer(img)
    if "ui$Bag" not in infer_rst:
        return None

    bbox_tup = infer_rst["ui$Bag"][0]["bbox"]
    return bbox_tup[0] + c_left, bbox_tup[1] + c_top, bbox_tup[2] + c_left, bbox_tup[3] + c_top


def get_bag_work_area_ui_bbox(bag_bbox, bdo_rect: list[int], debug=False) -> [tuple, None]:
    c_left, c_top, _, _ = bdo_rect

    bag_bbox_w = bag_bbox[2] - bag_bbox[0]
    bag_bbox_h = bag_bbox[3] - bag_bbox[1]

    exp_work_area_left = bag_bbox[0]
    exp_work_area_right = bag_bbox[0] + round(bag_bbox_w * 0.995)
    exp_work_area_top = bag_bbox[1] + round(bag_bbox_h * 0.178)
    exp_work_area_bottom = bag_bbox[1] + round(bag_bbox_h * 0.74)

    return exp_work_area_left, exp_work_area_top, exp_work_area_right, exp_work_area_bottom


def get_Pila_Fe_scroll_pos_by_model(detector, win_dc: WinDCApiCap, bdo_rect: list[int], debug=False) -> list:
    poses = []
    c_left, c_top, _, _ = bdo_rect
    img = win_dc.get_hwnd_screenshot_to_numpy_array(collection=debug, save_dir="logs/img/PilaFeScroll")
    infer_rst = detector.infer(img)
    if "item$Pila Fe Scroll" not in infer_rst:
        return poses

    bbox_obj = infer_rst["item$Pila Fe Scroll"]
    for obj in bbox_obj:
        bbox = obj["bbox"]
        poses.append(((bbox[0] + bbox[2]) / 2 + c_left, (bbox[1] + bbox[3]) / 2 + c_top))
    return poses


def get_Pila_Fe_scroll_poses_by_temple(win_dc: WinDCApiCap, client_rect) -> list:
    """
    用过模版匹配找到卷轴中心点的位置
    :param win_dc:
    :param client_rect:
    :return:
    """
    poses = []
    if not win_dc.is_available():
        return poses
    cur_windows_left, cur_windows_top, _, _ = client_rect
    sc_hots = win_dc.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/PilaFeScroll.bmp")
    template_h, template_w = template.shape[:2]
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        poses.append([cur_windows_left + pt_left + template_w / 2, cur_windows_top + pt_top + template_h / 2])
    return poses


def get_Pila_Fe_scroll_poses(detector, win_dc: WinDCApiCap, bdo_rect: list[int],
                             bbox: [tuple, list] = (-9999, -9999, 9999, 9999)) -> list:
    poses = get_Pila_Fe_scroll_pos_by_model(detector, win_dc, bdo_rect)
    poses = [i for i in filter(lambda x: bbox[0] < x[0] < bbox[2] and bbox[1] < x[1] < bbox[3], poses)]
    if len(poses) < 1:
        poses = get_Pila_Fe_scroll_poses_by_temple(win_dc, bdo_rect)
        poses = [i for i in filter(lambda x: bbox[0] < x[0] < bbox[2] and bbox[1] < x[1] < bbox[3], poses)]
    return poses


def use_Pila_Fe_scroll(detector, hwnd, debug=False):
    """
    寻找背包里的卷轴并右击使用召唤
    :param debug:
    :param detector: 模型检测器
    :param hwnd: 句柄
    :return:
    """
    find = False
    item_pos = None
    reason = ""

    retry_scroll_cnt = 0
    max_retry_scroll_cnt = 16
    win_dc = WinDCApiCap(hwnd)
    bdo_rect = get_bdo_rect(hwnd)

    bag_ui_bbox = get_bag_ui_bbox(detector, win_dc, bdo_rect, debug=debug)
    if bag_ui_bbox is None:
        reason = "找不到背包UI"
        return find, item_pos, reason

    into_pos = (bag_ui_bbox[0] + bag_ui_bbox[2]) / 2, (bag_ui_bbox[1] + bag_ui_bbox[3]) / 2
    out_pos = bag_ui_bbox[0] - 50, bag_ui_bbox[1] - 50
    step = 4
    while retry_scroll_cnt <= max_retry_scroll_cnt:
        ms.move(out_pos[0] - 30, out_pos[1] - 30, duration=0.1)
        item_poses = get_Pila_Fe_scroll_poses(detector, win_dc, bdo_rect, bag_ui_bbox)
        for pos in item_poses:
            if not bag_ui_bbox[0] < pos[0] < bag_ui_bbox[2] \
                    or not bag_ui_bbox[1] < pos[1] < bag_ui_bbox[3]:
                continue

            find = True
            item_pos = pos
            break
        if find:
            break

        ms.move(into_pos[0], into_pos[1], duration=0.1)
        for _ in range(step):
            ms.wheel(-100)
        retry_scroll_cnt += step

    return find, item_pos, reason


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


def found_boss_Magram_dead_or_Khalk_appear(detector, hwnd, retry: int, debug: bool = False) -> bool:
    """
    没有发旋目标 “玛格岚”，或者发现了目标柯尔克
    :param detector:
    :param hwnd:
    :param retry:
    :param debug:
    :return:
    """
    rst = False
    for i in range(retry + 1):
        found_magram = found_target(detector, hwnd, "boss$Magram", debug=debug, save_dir="logs/img/Margram")
        found_khalk = found_target(detector, hwnd, "boss$Khalk", debug=debug, save_dir="logs/img/Khalk")
        rst = rst or (not found_magram or found_khalk)
        if rst:
            break
    return rst


def found_task_over(detector, hwnd, retry: int, interval_delay: float, debug: bool = False) -> bool:
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
        time.sleep(interval_delay)
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


def collect_client_img(win_dc: WinDCApiCap, save_dir):
    """
    保存指定程序的窗口截图
    :param win_dc:
    :param save_dir:
    :return:
    """
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


def clear_bag(detector, hwnd, useWarehouseMaidShortcut, debug=False):
    """
    呼出仓库女仆清理背包杂物
    :param detector:
    :param hwnd:
    :param useWarehouseMaidShortcut: 仓库女仆快捷键
    :param debug:
    :return:
    """
    bdo_rect = get_bdo_rect(hwnd)
    win_dc = WinDCApiCap(hwnd)
    c_left, c_top, _, _ = bdo_rect

    kb.press("alt")
    kb.press_and_release(useWarehouseMaidShortcut)
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
                    time.sleep(0.1)
                    ms.click(ms.RIGHT)
                    time.sleep(0.1)
                    kb.press_and_release("F")
                    time.sleep(0.3)
                    kb.press_and_release("return")

            ms.move(into_pos[0], into_pos[1], duration=0.1)
            for i in range(step):
                ms.wheel(-100)
            cur_step += step

    kb.press_and_release("esc")
    kb.press_and_release("esc")


def found_ui_process_bar(detector, hwnd, retry: int, interval_delay: float, debug: bool = False) -> bool:
    """
    发现目标"进度条"
    :param interval_delay:
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
        time.sleep(interval_delay)

    return rst


def get_target_bboxes(detector, win_dc, client_rect, label, filter_bbox, absolute) -> list:
    """
    获取指定标签目标的bbox
    :param detector:
    :param win_dc:
    :param client_rect: absolute为真时，需要偏移的位置
    :param label: 指定的标签
    :param filter_bbox: 过滤区域
    :param absolute:
    :return:
    """
    c_left, c_top, _, _ = client_rect
    rst = []
    img = win_dc.get_hwnd_screenshot_to_numpy_array()
    infer_rst = detector.infer(img)
    if label not in infer_rst:
        return rst
    for obj in infer_rst[label]:
        bbox = obj["bbox"]
        if not filter_bbox[0] < bbox[0] or not bbox[2] < filter_bbox[2] \
                or not filter_bbox[1] < bbox[1] or not bbox[3] < filter_bbox[3]:
            continue
        if absolute:
            bbox[0] += c_left
            bbox[1] += c_top
            bbox[2] += c_left
            bbox[3] += c_top
            rst.append(bbox)
        else:
            rst.append(bbox)
    return rst


def get_target_bbox_center_poses(detector, win_dc, client_rect, label, filter_bbox, absolute) -> list:
    """
    获取指定标签目标的bbox中心点位置
    :param detector:
    :param win_dc:
    :param client_rect: absolute为真时，需要偏移的位置
    :param label: 指定的标签
    :param filter_bbox: 过滤区域
    :param absolute:
    :return:
    """
    bboxes = get_target_bboxes(detector, win_dc, client_rect, label, filter_bbox, absolute)
    rst = []
    for bbox in bboxes:
        center_pos = (bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2
        rst.append(center_pos)
    return rst


def go_into_or_out_hutton(detector, hwnd):
    """
    进入赫顿领域
    :param detector:
    :param hwnd:
    :return:
    """
    success = False
    win_dc = WinDCApiCap(hwnd)
    bdo_rect = get_bdo_rect(hwnd)
    poses = get_target_bbox_center_poses(detector, win_dc, bdo_rect, "icron$Hutton", [-9999, -9999, 9999, 9990], True)
    if len(poses) > 0:
        kb.press_and_release("left ctrl")
        pos = poses.pop()
        ms.move(pos[0], pos[1], duration=0.1)
        ms.click(ms.LEFT)
        time.sleep(0.5)
        kb.press_and_release("return")
        success = True
        time.sleep(20)
        kb.press_and_release("left ctrl")
    else:
        kb.press_and_release("left ctrl")
        ms.move(bdo_rect[2] - 590, bdo_rect[1] + 15, duration=0.1)
        ms.click(ms.LEFT)
        time.sleep(0.5)
        kb.press_and_release("return")
        success = True
        time.sleep(20)
        kb.press_and_release("left ctrl")

    return success


def get_auto_sort_on_poses_by_temple(win_dc: WinDCApiCap, client_rect) -> list:
    """
    用过模版匹配找到开启自动排列的坐标位置
    :param win_dc:
    :param client_rect:
    :return:
    """
    poses = []
    if not win_dc.is_available():
        return poses
    cur_windows_left, cur_windows_top, _, _ = client_rect
    sc_hots = win_dc.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/autoSortOn.bmp")
    template_h, template_w = template.shape[:2]
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        poses.append([cur_windows_left + pt_left + template_w / 2, cur_windows_top + pt_top + template_h / 2])
    return poses


def get_auto_sort_off_poses_by_temple(win_dc: WinDCApiCap, client_rect) -> list:
    """
    用过模版匹配找到关闭自动排列的坐标位置
    :param win_dc:
    :param client_rect:
    :return:
    """
    poses = []
    if not win_dc.is_available():
        return poses
    cur_windows_left, cur_windows_top, _, _ = client_rect
    sc_hots = win_dc.get_hwnd_screenshot_to_numpy_array()
    trans_hots = cv2.cvtColor(sc_hots, cv2.COLOR_RGBA2RGB)
    template = cv2.imread("data/temple/autoSortOff.bmp")
    template_h, template_w = template.shape[:2]
    res = cv2.matchTemplate(trans_hots, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.7
    loc = np.where(res >= threshold)
    for pt_left, pt_top in zip(*loc[::-1]):
        poses.append([cur_windows_left + pt_left + template_w / 2, cur_windows_top + pt_top + template_h / 2])
    return poses


def bag_auto_sort_on(hwnd):
    win_dc = WinDCApiCap(hwnd)
    client_rect = get_bdo_rect(hwnd)
    poses = get_auto_sort_off_poses_by_temple(win_dc, client_rect)
    for pos in poses:
        ms.move(pos[0], pos[1], duration=0.1)
        ms.click()

def bag_auto_sort_off(hwnd):
    win_dc = WinDCApiCap(hwnd)
    client_rect = get_bdo_rect(hwnd)
    poses = get_auto_sort_on_poses_by_temple(win_dc, client_rect)
    for pos in poses:
        ms.move(pos[0], pos[1], duration=0.1)
        ms.click()