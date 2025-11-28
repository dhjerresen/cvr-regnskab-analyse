"""
logging.py
-----------
Minimal logging wrapper for consistent console messages.
"""

import datetime

def log(msg: str):
    """
    Prints a timestamped log message.
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
