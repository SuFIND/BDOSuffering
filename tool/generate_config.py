# -*- coding: utf-8 -*-
"""
@Project : BDOSuffering
@File : generate_config.py
@Author : FF
@Time : 2023/2/27 20:31
"""
from utils.crypt_utils import encrypt_config_file

key = b''
config_path = "config/basic.toml"

if __name__ == '__main__':
    encrypt_config_file(config_path, key, remove_nocrypt_file=False)
