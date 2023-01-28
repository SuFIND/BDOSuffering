import random
import time

import keyboard
import mouse
import win32api, win32con
from ctypes import windll
from app.init_resource import global_var

# 定义使用keyboard库仿真但是未能达到预期的按键
VK_CODE = {
    '/': 191,
}

keybd_event = windll.user32.keybd_event


class HumanSimulate:
    MinOpDelay = 60
    MaxOpDelay = 80

    @classmethod
    def human_delay(cls) -> None:
        time.sleep(random.randint(cls.MinOpDelay, cls.MaxOpDelay) / 1000)


class MouseSimulate(HumanSimulate):
    MinOpDelay = 80
    MaxOpDelay = 140
    LEFT = mouse.LEFT
    RIGHT = mouse.RIGHT
    SCROLLUP = 1
    SCROLLDOWN = -1

    @classmethod
    def is_stop(cls) -> bool:
        sig_dic = global_var["process_sig"]
        sig_mutex = global_var["process_sig_lock"]
        with sig_mutex:
            return sig_dic["pause"] or sig_dic["stop"]

    @classmethod
    def move(cls, x, y, absolute=True, duration=0) -> bool:
        if cls.is_stop():
            return False
        mouse.move(x, y, absolute=absolute, duration=duration)
        cls.human_delay()
        return True

    @classmethod
    def click(cls, button=LEFT) -> bool:
        if cls.is_stop():
            return False
        mouse.press(button=button)
        cls.human_delay()
        mouse.release(button=button)
        cls.human_delay()
        return True

    @classmethod
    def press(cls, button=LEFT) -> bool:
        if cls.is_stop():
            return False
        mouse.press(button=button)
        cls.human_delay()
        return True

    @classmethod
    def release(cls, button=LEFT) -> bool:
        if cls.is_stop():
            return False
        mouse.release(button=button)
        cls.human_delay()
        return True

    @classmethod
    def scroll(cls, x, y, scroll_type=SCROLLDOWN) -> bool:
        if cls.is_stop():
            return False
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, x, y, scroll_type, 0)
        cls.human_delay()
        return True


class KeyboardSimulate(HumanSimulate):
    MinOpDelay = 50
    MaxOpDelay = 80

    @classmethod
    def is_stop(cls) -> bool:
        sig_dic = global_var["process_sig"]
        sig_mutex = global_var["process_sig_lock"]
        with sig_mutex:
            return sig_dic["pause"] or sig_dic["stop"]

    @classmethod
    def press_and_release(cls, key) -> bool:
        if cls.is_stop():
            return False
        if key in VK_CODE:
            hex_vk_code = VK_CODE[key]
            scan_code = keyboard.key_to_scan_codes(key)[1]
            keybd_event(hex_vk_code, scan_code, 0, 0)
            keybd_event(hex_vk_code, scan_code, 2, 0)
        else:
            keyboard.press_and_release(key)
        cls.human_delay()
        return True

    @classmethod
    def press(cls, key) -> bool:
        if cls.is_stop():
            return False
        if key in VK_CODE:
            hex_vk_code = VK_CODE[key]
            scan_code = keyboard.key_to_scan_codes(key)[1]
            keybd_event(hex_vk_code, scan_code, 0, 0)
        else:
            keyboard.press(key)
        cls.human_delay()
        return True

    @classmethod
    def release(cls, key) -> bool:
        if cls.is_stop():
            return False
        if key in VK_CODE:
            hex_vk_code = VK_CODE[key]
            scan_code = keyboard.key_to_scan_codes(key)[1]
            keybd_event(hex_vk_code, scan_code, 2, 0)
        else:
            keyboard.release(key)
        cls.human_delay()
        return True
