---
title: "SSRN Working Papers — HoKwang Kim (Dennis Kim)"
title_ko: "SSRN 작업 논문 모음 — 김호광 (Dennis Kim)"
author:
  name: "HoKwang Kim"
  name_ko: "김호광"
  alias: "Dennis Kim"
  affiliation: "Betalabs Inc."
  email: "gameworker@gmail.com"
  orcid: "0009-0002-0962-2175"
  ssrn_author_id: "11276088"
  github: "gameworkerkim"
papers_count: 4
total_pages: 113
languages: ["en", "ko"]
last_updated: "2026-05-12"
license: "CC-BY-4.0 (preprint text); MIT (associated code)"
description: "Index of four SSRN working papers spanning cryptocurrency market microstructure, exchange airdrop economics, and multilingual LLM evaluation in equity selection."
description_ko: "암호화폐 시장 미시구조, 거래소 에어드롭 경제학, 다국어 LLM 주식 선별 평가 등 4편의 SSRN 작업 논문 인덱스"
keywords:
  - "cryptocurrency"
  - "market microstructure"
  - "token unlock"
  - "airdrop"
  - "BNB Chain"
  - "Binance"
  - "beta decomposition"
  - "volatility ratio"
  - "large language model"
  - "LLM evaluation"
  - "contrarian investing"
  - "pharmaceutical sector"
  - "event study"
keywords_ko:
  - "암호화폐"
  - "시장 미시구조"
  - "토큰 언락"
  - "에어드롭"
  - "BNB 체인"
  - "바이낸스"
  - "베타 분해"
  - "변동성 비율"
  - "거대언어모델"
  - "LLM 평가"
  - "역발상 투자"
  - "제약 섹터"
  - "이벤트 스터디"
---

# SSRN Working Papers — HoKwang Kim (Dennis Kim)

> **English follows after the Korean section.**
> **한국어 다음에 영어 섹션이 이어집니다.**

[![ORCID](https://img.shields.io/badge/ORCID-0009--0002--0962--2175-A6CE39?logo=orcid&logoColor=white)](https://orcid.org/0009-0002-0962-2175)
[![SSRN Author](https://img.shields.io/badge/SSRN-Author%20Page-1A5F7A)](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=11276088)
[![Papers](https://img.shields.io/badge/Papers-4-success)](#paper-list)
[![Total Pages](https://img.shields.io/badge/Total%20Pages-113-informational)](#paper-list)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

---

## 한국어 (Korean)

### 저자 정보

| 항목 | 내용 |
|---|---|
| 성명 | 김호광 (HoKwang Kim) |
| 영문 별칭 | Dennis Kim |
| 소속 | Betalabs Inc. (CEO) |
| ORCID | [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175) |
| SSRN 작성자 ID | [11276088](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=11276088) |
| 이메일 | gameworker@gmail.com |
| GitHub | [@gameworkerkim](https://github.com/gameworkerkim) |

### 논문 4편 요약

본 폴더는 2026년 4월~5월에 SSRN에 게재된 4편의 작업 논문(working papers)을 통합 관리한다. 주제는 크게 두 갈래로 나뉜다.

1. **암호화폐 시장 미시구조 (3편)** — Binance 거래소 토큰 언락 이벤트, BNB Chain Megadrop 에어드롭 분배 비대칭, BNB-ETH 베타의 변동성 비율 채널 분해.
2. **다국어 LLM 평가 (1편)** — 동일 프롬프트 하에서 출력 길이와 컨트라리안 종목 발굴률 간 역상관 관계.

총 113 페이지에 걸쳐 *event study*, *variance decomposition*, *DCC-GARCH*, *Spearman 순위 상관* 등 표준 계량경제·통계 기법을 사용했으며, 모든 데이터·코드는 공개 저장소에서 재현 가능하다.

### 논문 목록 (게재 순서)

| # | 제목 | SSRN ID | 게재일 | 페이지 | 파일 |
|---|---|---|---|---|---|
| 1 | 72-Hour Shock — Binance 토큰 언락 52건 예비 증거 | [6632838](https://ssrn.com/abstract=6632838) | 2026-04-24 | 21 | [`01_SSRN-6632838_72-Hour-Shock.md`](./01_SSRN-6632838_72-Hour-Shock.md) |
| 2 | 중앙화 거래소 에어드롭 분배 비대칭 — BNB Chain 생태계 | [6688740](https://ssrn.com/abstract=6688740) | 2026-05-11 | 55 | [`02_SSRN-6688740_Distribution-Asymmetry-BNB.md`](./02_SSRN-6688740_Distribution-Asymmetry-BNB.md) |
| 3 | Less Volume, More Variety — LLM 출력 길이와 컨트라리안 발굴 | [6705598](https://ssrn.com/abstract=6705598) | 2026-05-11 | 9 | [`03_SSRN-6705598_Less-Volume-More-Variety.md`](./03_SSRN-6705598_Less-Volume-More-Variety.md) |
| 4 | Directional Decoupling — BNB-ETH 베타 변동성 비율 채널 분해 | [6750298](https://ssrn.com/abstract=6750298) | 2026-05-12 | 28 | [`04_SSRN-6750298_Directional-Decoupling.md`](./04_SSRN-6750298_Directional-Decoupling.md) |

### 연구의 의의 (Significance)

#### 1. 시장 미시구조 측면

세 편의 암호화폐 논문은 *공개 온체인 데이터*와 *CEX 거래소 데이터*만으로 측정 가능한 새로운 시장 비효율성 패턴을 정량화했다. 
특히 (1) 토큰 언락 직후 72시간 내 가격 하락 패턴, 
(2) 에어드롭 분배 구조에서의 토큰 보유자/재단/소매 투자자 간 비대칭 손익, 
(3) BNB-ETH 페어에서의 *상관관계 일정 + 변동성 비율 압축* 메커니즘은 기존 학술 문헌에서 충분히 다뤄지지 않은 영역이다. 

한국 *DAXA(디지털자산거래소공동협의체)* 및 *KoFIU(금융정보분석원)* 규제 논의에 직접 적용 가능한 실증 근거를 제공한다.

#### 2. LLM 평가 측면

3번 논문은 frontier LLM 4종(ChatGPT, Claude, DeepSeek, Gemini)을 *동일 프롬프트* 조건에서 비교했을 때, **출력 길이가 짧을수록 컨트라리안 종목 발굴률이 비례적으로 높아지는** 역상관 관계(Spearman ρ = −0.80, ChatGPT 이상치 제외 시 ρ = −1.00)를 보고한다. 이는 *토큰 예산 자체가 LLM 앙상블에서 사고 다양성을 유도하는 하이퍼파라미터로 기능할 수 있다*는 함의를 가지며, *compression-forces-selection* 메커니즘으로 해석한다.

결국 LLM이 같더라도 언어에 따라 결과물의 퀄리티가 제약된다는 사실을 확인한다.

#### 3. 방법론적 측면

4편 모두 **공개 데이터 + 공개 코드 + 공개 PDF** 의 *triple-open* 원칙을 따른다. 인용 시 SSRN DOI 가 우선이며, ORCID 와 함께 표기하면 *CrossRef* 및 *Google Scholar* 색인에 정확히 매핑된다. *Reproducible research* 표준을 준수하기 위해 GitHub 저장소에 데이터·스크립트·LaTeX 소스가 함께 공개되어 있다.

---

## English

### Author Information

| Field | Value |
|---|---|
| Name | HoKwang Kim (김호광) |
| Alias | Dennis Kim |
| Affiliation | Betalabs Inc. (CEO) |
| ORCID | [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175) |
| SSRN Author ID | [11276088](https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=11276088) |
| Email | gameworker@gmail.com |
| GitHub | [@gameworkerkim](https://github.com/gameworkerkim) |

### Overview

This folder consolidates four SSRN working papers posted between April and May 2026. Two thematic clusters are covered:

1. **Cryptocurrency market microstructure (3 papers)** — covering token unlock events on Binance, Megadrop airdrop distribution on BNB Chain, and the volatility-ratio channel of BNB-ETH beta decomposition.
2. **Multilingual LLM evaluation (1 paper)** — documenting an inverse relationship between LLM output length and contrarian discovery rate under identical prompts.

The four papers total **113 pages** and employ standard econometric/statistical techniques including event studies, variance decomposition, DCC-GARCH, and Spearman rank correlation. All data and code are publicly available for reproducibility.

### Paper List (in posting order)

| # | Title | SSRN ID | Posted | Pages | File |
|---|---|---|---|---|---|
| 1 | The 72-Hour Shock? Preliminary Evidence from 52 Token Unlock Events on Binance | [6632838](https://ssrn.com/abstract=6632838) | 2026-04-24 | 21 | [`01_SSRN-6632838_72-Hour-Shock.md`](./01_SSRN-6632838_72-Hour-Shock.md) |
| 2 | Distribution Asymmetry of Centralized Exchange Airdrops and the BNB Chain Ecosystem | [6688740](https://ssrn.com/abstract=6688740) | 2026-05-11 | 55 | [`02_SSRN-6688740_Distribution-Asymmetry-BNB.md`](./02_SSRN-6688740_Distribution-Asymmetry-BNB.md) |
| 3 | Less Volume, More Variety: LLM Output Length × Contrarian Discovery in Pharma | [6705598](https://ssrn.com/abstract=6705598) | 2026-05-11 | 9 | [`03_SSRN-6705598_Less-Volume-More-Variety.md`](./03_SSRN-6705598_Less-Volume-More-Variety.md) |
| 4 | Directional Decoupling: Volatility-Ratio-Driven Beta Compression in BNB-ETH | [6750298](https://ssrn.com/abstract=6750298) | 2026-05-12 | 28 | [`04_SSRN-6750298_Directional-Decoupling.md`](./04_SSRN-6750298_Directional-Decoupling.md) |

### Significance

#### 1. Market Microstructure Contribution

The three cryptocurrency papers quantify novel market inefficiency patterns measurable from public on-chain and exchange data alone. Specifically, (1) the 72-hour post-unlock price decline pattern, (2) the asymmetric P&L between BNB holders, foundations, and retail participants in airdrop distributions, and (3) the *correlation-preserving, volatility-ratio-compressing* mechanism in the BNB-ETH pair — three phenomena underexplored in prior literature. The results offer empirical evidence directly applicable to Korean regulatory deliberations under DAXA (Digital Asset Exchange Joint Council) and KoFIU (Korea Financial Intelligence Unit).

#### 2. LLM Evaluation Contribution

Paper #3 reports an inverse relationship: under identical prompts to four frontier LLMs (ChatGPT, Claude, DeepSeek, Gemini), shorter-output models produce proportionally more contrarian (uniquely-discovered) picks. Spearman ρ = −0.80 across all four models, and ρ = −1.00 after excluding ChatGPT as a stale-data outlier. This implies **token budget itself may operate as a hyperparameter inducing thought-diversity in LLM ensembles**, a mechanism we label *compression-forces-selection*.

#### 3. Methodological Contribution

All four papers adhere to a *triple-open* principle: open data, open code, open PDF. Citations should use the SSRN DOI as primary identifier and include the ORCID for accurate mapping in CrossRef and Google Scholar. Reproducibility artifacts (datasets, scripts, LaTeX sources) are mirrored to the author's GitHub repositories.

---

## How to Cite / 인용 방법

### Quick BibTeX

```bibtex
@misc{kim2026_72hr,
  author    = {Kim, HoKwang},
  title     = {The 72-Hour Shock? Preliminary Evidence from 52 Token Unlock Events on Binance},
  year      = {2026},
  month     = {apr},
  publisher = {SSRN},
  doi       = {10.2139/ssrn.6632838},
  url       = {https://ssrn.com/abstract=6632838},
  note      = {SSRN Working Paper No.~6632838}
}

@misc{kim2026_airdrop,
  author    = {Kim, HoKwang},
  title     = {Distribution Asymmetry of Centralized Exchange Airdrops and the {BNB} Chain Ecosystem:
               {BNB} Holder Gain, Foundation Disaster, and the Decoupling Pattern of {BNB} Chain},
  year      = {2026},
  month     = {may},
  publisher = {SSRN},
  doi       = {10.2139/ssrn.6688740},
  url       = {https://ssrn.com/abstract=6688740},
  note      = {SSRN Working Paper No.~6688740}
}

@misc{kim2026_llm,
  author    = {Kim, HoKwang},
  title     = {Less Volume, More Variety: An Inverse Relationship Between {LLM} Output Length and
               Contrarian Discovery in Pharmaceutical Stock Selection},
  year      = {2026},
  month     = {may},
  publisher = {SSRN},
  doi       = {10.2139/ssrn.6705598},
  url       = {https://ssrn.com/abstract=6705598},
  note      = {SSRN Working Paper No.~6705598}
}

@misc{kim2026_decoupling,
  author    = {Kim, HoKwang},
  title     = {Directional Decoupling: Volatility-Ratio-Driven Beta Compression in the
               {BNB}-{ETH} Pair, May 2022 -- April 2026},
  year      = {2026},
  month     = {may},
  publisher = {SSRN},
  doi       = {10.2139/ssrn.6750298},
  url       = {https://ssrn.com/abstract=6750298},
  note      = {SSRN Working Paper No.~6750298}
}
```

> Full bibliography in [`BIBLIOGRAPHY.bib`](./BIBLIOGRAPHY.bib) (BibTeX) and [`BIBLIOGRAPHY.ris`](./BIBLIOGRAPHY.ris) (RIS for Zotero/Mendeley/EndNote).

---

## Folder Structure / 폴더 구조

```
papers/
├── README.md                                       # This file — bilingual index
├── CITATION.cff                                    # Citation File Format (GitHub-recognized)
├── BIBLIOGRAPHY.bib                                # All 4 papers in BibTeX
├── BIBLIOGRAPHY.ris                                # All 4 papers in RIS
├── metadata.json                                   # Machine-readable index (schema.org JSON-LD)
├── 01_SSRN-6632838_72-Hour-Shock.md
├── 02_SSRN-6688740_Distribution-Asymmetry-BNB.md
├── 03_SSRN-6705598_Less-Volume-More-Variety.md
├── 04_SSRN-6750298_Directional-Decoupling.md
└── scripts/
    ├── generate_citations.py                       # Regenerates BibTeX/RIS/APA/CSL-JSON
    ├── validate_metadata.py                        # ICMJE/COPE/CrossRef metadata check
    └── search_papers.py                            # Local full-text search (no dependencies)
```

---

## Scripts (International Publishing Compliance) / 국제 게시 요건 스크립트

Three Python 3.10+ utilities live under [`scripts/`](./scripts) and have **no external dependencies** (stdlib only):

| Script | Purpose | Usage |
|---|---|---|
| [`generate_citations.py`](./scripts/generate_citations.py) | Regenerates BibTeX, RIS, APA, MLA, Chicago, and CSL-JSON citations from each paper's YAML front-matter. | `python scripts/generate_citations.py --format bibtex --out BIBLIOGRAPHY.bib` |
| [`validate_metadata.py`](./scripts/validate_metadata.py) | Validates every paper file against ICMJE/COPE/CrossRef minimum-metadata checklist (DOI, ORCID, title, abstract, keywords, JEL, posted date). | `python scripts/validate_metadata.py` |
| [`search_papers.py`](./scripts/search_papers.py) | Indexed full-text search over the four papers; supports KO/EN queries with token-overlap ranking. | `python scripts/search_papers.py "volatility ratio"` |

All scripts read the YAML front-matter and Markdown body of each `0X_SSRN-XXXXXXX_*.md` file as ground truth. After editing a paper file, rerun `validate_metadata.py` to confirm compliance before re-uploading to SSRN.

---

## License / 라이선스

- **Preprint text & abstracts**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — share and adapt with attribution to HoKwang Kim and SSRN DOI.
- **Associated code & scripts**: MIT License — see individual repository `LICENSE` files.
- **Data**: see each paper's data availability statement.

---

## Contact

- **Author**: HoKwang Kim (Dennis Kim) — Betalabs Inc.
- **Email**: gameworker@gmail.com
- **ORCID**: [0009-0002-0962-2175](https://orcid.org/0009-0002-0962-2175)
- **SSRN Author Page**: <https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=11276088>
- **GitHub**: <https://github.com/gameworkerkim>

---

*Last updated: 2026-05-12 · Maintained by HoKwang Kim · See `CITATION.cff` for the canonical citation entry.*
