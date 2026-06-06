"""ARDS-X — vendored from canonical Python (01.Trading Strategy/ARDS …/quant/).

Adapted for Azure Functions:
  - 절대 import → 상대 import (`from . import config` 등)
  - CACHE_DIR → /tmp (Function 인스턴스 ephemeral, yfinance batch 매번 새로 받음)
  - run._load_state / _save_state → 외부 injectable callback (Blob 으로 우회)
"""
