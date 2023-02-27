# -*- coding: utf-8 -*-
"""
@Project : BDOSuffering
@File : crypt_utils.py
@Author : FF
@Time : 2023/2/27 20:30
"""
from Crypto.Cipher import AES
import os


# 加密配置文件
def encrypt_config_file(file_path, key, remove_nocrypt_file=False):
    # 读取配置文件
    with open(file_path, 'rb') as f:
        plaintext = f.read()

    # 加密
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    # 写入加密后的文件
    with open(file_path + '.enc', 'wb') as f:
        [f.write(x) for x in (cipher.nonce, tag, ciphertext)]

    # 删除明文文件
    if remove_nocrypt_file:
        os.remove(file_path)


# 解密配置文件
def decrypt_config_file(file_path, key):
    # 读取加密文件
    with open(file_path, 'rb') as f:
        nonce, tag, ciphertext = [f.read(x) for x in (16, 16, -1)]

    # 解密
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)

    # 写入明文文件
    with open(file_path[:-4], 'wb') as f:
        f.write(plaintext)
