import time

import operation.classics_op as classics_op
# from operation.classics_op import get_market_npc_gps_pos, use_scroll
from utils.capture_utils import WinDCApiCap
from utils.muti_utils import RetrySig, StopSig, OverSig
from utils.simulate_utils import MouseSimulate as ms, KeyboardSimulate as kb
from utils.win_utils import get_bdo_rect


def back_to_market(detector, hwnd):
    """
    打开寻找NPC UI
    :return:
    """
    # 利用快捷键打开寻找NPC的UI
    kb.press("alt")
    kb.press_and_release("6")
    kb.release("alt")

    time.sleep(0.1)

    # 利用模型推理确认寻找NPC-UI的位置
    wdac = WinDCApiCap(hwnd)
    c_left, c_top, _, _ = get_bdo_rect(hwnd)
    img = wdac.get_hwnd_screenshot_to_numpy_array()
    infer_rst = detector.infer(img)

    if "FindNPCUI" not in infer_rst:
        # TODO 需要为RetrySig指定需要重复做的事情
        raise RetrySig(redo=[])

    bbox_tup = infer_rst["FindNPCUI"][0]["bbox"]
    target_pos = (bbox_tup[0] + bbox_tup[2]) / 2, (bbox_tup[1] + bbox_tup[3]) / 2 / 2
    target_pos = c_left + target_pos[0], c_top + target_pos[1]
    ms.move(target_pos[0], target_pos[1], duration=0.1)
    ms.wheel_scroll(-100)
    ms.wheel_scroll(-100)
    ms.wheel_scroll(-100)
    ms.wheel_scroll(-100)

    # 等待UI动画结束
    time.sleep(2)

    market_npc_icon_pos = classics_op.get_market_npc_gps_pos(hwnd)
    ms.move(market_npc_icon_pos[0], market_npc_icon_pos[1], duration=0.1)
    ms.click()
    kb.press_and_release("T")

    # 再次利用快捷键打开寻找NPC的UI
    kb.press_and_release("esc")


def get_bag_ui_bbox(detector, win_dc: WinDCApiCap, bdo_rect: list[int]):
    c_left, c_top, _, _ = bdo_rect
    img = win_dc.get_hwnd_screenshot_to_numpy_array()
    infer_rst = detector.infer(img)
    if "BagUI" not in infer_rst:
        # TODO 需要为RetrySig指定需要重复做的事情
        raise RetrySig(redo=[])

    bbox_tup = infer_rst["BagUI"][0]["bbox"]
    return bbox_tup[0] + c_left, bbox_tup[1] + c_top, bbox_tup[2] + c_left, bbox_tup[3] + c_top


def get_Pila_Fe_scroll_pos(detector, win_dc: WinDCApiCap, bdo_rect: list[int]):
    c_left, c_top, _, _ = bdo_rect
    img = win_dc.get_hwnd_screenshot_to_numpy_array()
    infer_rst = detector.infer(img)
    if "CallVolume" not in infer_rst:
        return None

    bbox_tup = infer_rst["CallVolume"][0]["bbox"]
    return (bbox_tup[0] + bbox_tup[2]) / 2 + c_left, (bbox_tup[1] + bbox_tup[3]) / 2 + c_top


def use_Pila_Fe_scroll(detector, hwnd):
    """
    寻找背包里的卷轴并右击使用召唤
    :param detector: 模型检测器
    :param hwnd: 句柄
    :return:
    """
    find = False
    retry_scroll_cnt = 0
    max_retry_scroll_cnt = 16
    win_dc = WinDCApiCap(hwnd)
    bdo_rect = get_bdo_rect(hwnd)

    bag_ui_bbox = get_bag_ui_bbox(detector, win_dc, bdo_rect)
    into_pos = (bag_ui_bbox[0] + bag_ui_bbox[2]) / 2, (bag_ui_bbox[1] + bag_ui_bbox[3]) / 2
    out_pos = bag_ui_bbox[0] - 50, bag_ui_bbox[1] - 50
    step = 4
    while retry_scroll_cnt <= max_retry_scroll_cnt:
        ms.move(out_pos[0] - 30, out_pos[0] - 30)
        item_pos = classics_op.get_call_volume_pos(hwnd)
        if item_pos is not None:
            classics_op.use_scroll(item_pos)
            find = True
            break
        else:
            ms.move(into_pos[0], into_pos[1], duration=0.1)
            for _ in range(step):
                ms.wheel_scroll(-100)
            retry_scroll_cnt += step
            continue

    if find:
        return
    else:
        raise OverSig
