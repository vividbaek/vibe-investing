"""Vibe Investing dashboard — ARDS + AMQS strategy engines + runner.

원본은 `01.Trading Strategy/{ARDS …,AMQS …}/` 의 캐노니컬 Python 구현이며
여기로 vendor 함. 변경은 Azure 환경 어댑팅에 한정 — 룰/상수 변경 금지.

- ards/ : ARDS-X regime classifier (vendored quant/*.py + 경로 수정)
- amqs/ : AMQS-AI-Infra strategy (vendored script/strategy.py, 무수정)
- blob_state.py : 히스테리시스 상태를 Blob 에 영속화 (로컬 파일 대체)
- runner.py : Azure Functions 에서 호출하는 async 오케스트레이터
"""
