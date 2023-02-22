import random
import time
from ctypes import windll

import keyboard
import mouse

# 定义使用keyboard库仿真但是未能达到预期的按键
VK_CODE = {
    '/': 191,
    "left shift": 16,
    "right shift": 16,
    "d": 68,
}

SCAN_CODE = {
    '/': 53,
    "left shift": 42,
    "right shift": 54,
    "d": 32,
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

    @classmethod
    def move(cls, x, y, absolute=True, duration=0) -> bool:
        mouse.move(x, y, absolute=absolute, duration=duration)
        cls.human_delay()
        return True

    @classmethod
    def click(cls, button=LEFT) -> bool:
        mouse.press(button=button)
        cls.human_delay()
        mouse.release(button=button)
        cls.human_delay()
        return True

    @classmethod
    def press(cls, button=LEFT) -> bool:
        mouse.press(button=button)
        cls.human_delay()
        return True

    @classmethod
    def release(cls, button=LEFT) -> bool:
        mouse.release(button=button)
        cls.human_delay()
        return True

    @classmethod
    def wheel(cls, delta) -> bool:
        mouse.wheel(delta)
        cls.human_delay()
        return True

    @classmethod
    def drag(cls, start_x, start_y, end_x, end_y, button=LEFT, duration=0):
        if mouse.is_pressed(button):
            mouse.release(button)
        cls.move(start_x, start_y, duration=duration)
        cls.press(button)
        cls.move(end_x, end_y, duration=duration)
        cls.release(button)


class KeyboardSimulate(HumanSimulate):
    MinOpDelay = 50
    MaxOpDelay = 80

    @classmethod
    def press_and_release(cls, key: str) -> bool:
        key = key.lower()
        if key in VK_CODE and key in SCAN_CODE:
            hex_vk_code = VK_CODE[key]
            scan_code = SCAN_CODE[key]
            keybd_event(hex_vk_code, scan_code, 0, 0)
            keybd_event(hex_vk_code, scan_code, 2, 0)
        else:
            keyboard.press_and_release(key)
        cls.human_delay()
        return True

    @classmethod
    def press(cls, key) -> bool:
        if key in VK_CODE and key in SCAN_CODE:
            hex_vk_code = VK_CODE[key]
            scan_code = SCAN_CODE[key]
            keybd_event(hex_vk_code, scan_code, 0, 0)
        else:
            keyboard.press(key)
        cls.human_delay()
        return True

    @classmethod
    def release(cls, key) -> bool:
        if key in VK_CODE and key in SCAN_CODE:
            hex_vk_code = VK_CODE[key]
            scan_code = SCAN_CODE[key]
            keybd_event(hex_vk_code, scan_code, 2, 0)
        else:
            keyboard.release(key)
        cls.human_delay()
        return True
