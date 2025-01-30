#!/usr/bin/env python3
"""Generates and outputs generated secret key"""
import secrets
secret_key = secrets.token_hex(32)  # 32-byte secret key
print(secret_key)
