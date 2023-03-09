# -*- coding: utf-8 -*-
"""
@Project : BDOSuffering
@File : generate_config.py
@Author : FF
@Time : 2023/2/27 20:31
"""
from utils.crypt_utils import encrypt_config_file, build_key, decrypt_config_file

config_path = "config/private.toml"
key = ''
after_crypt_path = "config/private.toml.enc"

real_key, real_key_bytes = build_key(key)
print("real_key", real_key)

if __name__ == '__main__':
    task = 2
    if task == 1:
        encrypt_config_file(config_path, real_key_bytes, remove_nocrypt_file=False)
    if task == 2:
        toml = decrypt_config_file(after_crypt_path, real_key_bytes)
        print(toml)