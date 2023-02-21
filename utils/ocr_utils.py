# -*- coding: utf-8 -*-
import re
import time
from math import floor
from traceback import format_exc

import cv2
import pytesseract
from PIL import Image

from utils.capture_utils import WinDCApiCap
from utils.log_utils import Logger

lang_en_US = "en-US"
lang_zh = "zh-Hans-CN"


pytesseract.pytesseract.tesseract_cmd = "third_part/tesseract/tesseract.exe"


def get_bag_capacity_by_tesseract_ocr(win_dc: WinDCApiCap, bag_bbox):
    rst = None, None
    if not win_dc.is_available():
        return rst

    try:
        sc = win_dc.get_hwnd_screenshot_to_numpy_array()
        bg_sc = sc[bag_bbox[1]:bag_bbox[3], bag_bbox[0]:bag_bbox[2]]

        bg_sc_h, bg_sc_w = bg_sc.shape[:2]
        capacity_left = round(bg_sc_w * 0.8125)
        capacity_top = round(bg_sc_h * 0.14)
        capacity_bottom = round(bg_sc_h * 0.19)
        capacity_sc = bg_sc[capacity_top:capacity_bottom, capacity_left:]

        img_name = f"{floor(time.time())}.jpg"
        cv2.imwrite(f"logs/img/bagCapacity/{img_name}", capacity_sc)

        color_coverted = cv2.cvtColor(capacity_sc, cv2.COLOR_BGR2RGB)

        pil_image = Image.fromarray(color_coverted)
        string = pytesseract.image_to_string(pil_image, lang="eng",
                                             config="--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789/")
        r = re.match(r"(?P<cur>\d+)/(?P<total>\d+)", string)
        if r is not None:
            _ = r.groupdict()
            cur, total = _["cur"], _["total"]
            cur = int(cur)
            total = int(total)
            rst = cur, total
            print(rst)
    except Exception as e:
        err = format_exc()
        Logger.error(err)
    return rst
