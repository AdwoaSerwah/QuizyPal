#!/usr/bin/env python3

import secrets
secret_key = secrets.token_hex(32)  # 32-byte secret key
print(secret_key)
