# -*- coding: utf-8 -*-
import re
import asyncio
import base64
import copy
import math
import time
import traceback

import numpy
import cv2
import winsdk
import pytesseract
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.globalization import Language
from winsdk.windows.graphics.imaging import *
from winsdk.windows.security.cryptography import CryptographicBuffer
from PIL import Image

from utils.capture_utils import WinDCApiCap
from utils.log_utils import Logger

lang_en_US = "en-US"
lang_zh = "zh-Hans-CN"


class rect:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h

    def __repr__(self):
        return 'rect(%d, %d, %d, %d)' % (self.x, self.y, self.width, self.height)

    def right(self):
        return self.x + self.width

    def bottom(self):
        return self.y + self.height

    def set_right(self, value):
        self.width = value - self.x

    def set_bottom(self, value):
        self.height = value - self.y


def dump_rect(rtrect: winsdk.windows.foundation.Rect):
    return rect(rtrect.x, rtrect.y, rtrect.width, rtrect.height)


def dump_ocrword(word):
    return {
        'bounding_rect': dump_rect(word.bounding_rect),
        'text': word.text
    }


def merge_words(words):
    if len(words) == 0:
        return words
    new_words = [copy.deepcopy(words[0])]
    words = words[1:]
    for word in words:
        lastnewword = new_words[-1]
        lastnewwordrect = new_words[-1]['bounding_rect']
        wordrect = word['bounding_rect']
        if len(word['text']) == 1 and wordrect.x - lastnewwordrect.right() <= wordrect.width * 0.2:
            lastnewword['text'] += word['text']
            lastnewwordrect.x = min((wordrect.x, lastnewwordrect.x))
            lastnewwordrect.y = min((wordrect.y, lastnewwordrect.y))
            lastnewwordrect.set_right(max((wordrect.right(), lastnewwordrect.right())))
            lastnewwordrect.set_bottom(max((wordrect.bottom(), lastnewwordrect.bottom())))
        else:
            new_words.append(copy.deepcopy(word))
    return new_words


def dump_ocrline(line):
    words = list(map(dump_ocrword, line.words))
    merged = merge_words(words)
    return {
        'text': line.text,
        'words': words,
        'merged_words': merged,
        'merged_text': ' '.join(map(lambda x: x['text'], merged))
    }


def dump_ocrresult(ocrresult):
    lines = list(map(dump_ocrline, ocrresult.lines))
    return {
        'text': ocrresult.text,
        # 'text_angle': ocrresult.text_angle.value if ocrresult.text_angle else None,
        'lines': lines,
        'merged_text': ' '.join(map(lambda x: x['merged_text'], lines))
    }


def ibuffer(s):
    """create winsdk IBuffer instance from a bytes-like object"""
    return CryptographicBuffer.decode_from_base64_string(base64.b64encode(s).decode('ascii'))


def swbmp_from_pil_image(img):
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    pybuf = img.tobytes()
    rtbuf = ibuffer(pybuf)
    return SoftwareBitmap.create_copy_from_buffer(rtbuf, BitmapPixelFormat.RGBA8, img.width, img.height,
                                                  BitmapAlphaMode.STRAIGHT)


async def ensure_coroutine(awaitable):
    return await awaitable


def blocking_wait(awaitable):
    return asyncio.run(ensure_coroutine(awaitable))


def recognize_pil_image(img, lang):
    lang = Language(lang)
    assert (OcrEngine.is_language_supported(lang))
    eng = OcrEngine.try_create_from_language(lang)
    swbmp = swbmp_from_pil_image(img)
    return dump_ocrresult(blocking_wait(eng.recognize_async(swbmp)))


def recognize_file(filename, lang=lang_zh):
    img = Image.open(filename)
    return recognize_pil_image(img, lang)


def recognize_numpy(img: numpy.ndarray, lang=lang_zh):
    img_pil = Image.fromarray(img)
    return recognize_pil_image(img_pil, lang)


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
        capacity_top = round(bg_sc_h * 0.15)
        capacity_bottom = round(bg_sc_h * 0.2)
        capacity_sc = bg_sc[capacity_top:capacity_bottom, capacity_left:]

        img_name = f"{math.floor(time.time())}.jpg"
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
        err = traceback.format_exc()
        Logger.error(err)
    return rst