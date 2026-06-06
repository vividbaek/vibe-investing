# cron-worker — 스케줄 전용 Worker

Pages 가 Cron Trigger 를 지원하지 않으므로 주기 작업만 담당. 결과는 D1/R2 에 미리 저장 →
Pages Functions(API)는 읽기만 + CDN 엣지 캐시.

## 크론
| cron (UTC) | 핸들러 | 동작 | 상태 |
|---|---|---|---|
| `30 21 * * 1-5` | `runDailySignals` + `runMoversSnapshot` | 일봉 시그널 + **급등/급락 Top10(장종료 후 1회)** → D1/R2 | ✅ |
| `*/10 * * * *` | `runMarketSnapshot` | 지수/섹터/VIX/ETF 시세 → R2 market-latest.json + stats_cache (movers 제외) | ✅ Yahoo 키리스 |

> **급등/급락(movers)**: 장 종료 후 1회만 갱신(`runMoversSnapshot`, 일1회 크론) → D1 movers + R2 `movers-latest.json`(s-maxage=1800). 스크리너가 비면(휴장/실패) 스킵해 **직전값 유지**. 프론트는 `/api/movers`(D1)로 조회.

## 10분 시세 스냅샷 (`market.ts`) — 키 불필요
- 지수(SPY/QQQ/DIA/IWM)+VIX+섹터 ETF11: Yahoo **chart meta**(현재가÷전일종가→등락%)
- 급등/급락 Top10: Yahoo **사전정의 스크리너**(`day_gainers`/`day_losers`, 키 불필요)
- 리스크 게이지(0~100, heuristic): 지수등락 + VIX + 섹터폭 → RISK_OFF/NEUTRAL/RISK_ON
- 산출: R2 `market-latest.json`(`/api/market`) + D1 `movers`(`/api/movers`) + `stats_cache.last_update`
- 장외시간(UTC 13:00–21:30 밖) 조기 스킵.

## 데이터 소스 (무료, 키 불필요)
- **Yahoo chart API** (`providers/yahoo.ts`) — 가격/지수/금리/VIX. 엔진 심볼(`^GSPC` 등) 그대로, adjclose.
  - ※ Stooq 는 봇 차단(PoW)으로 Worker fetch 불가 → Yahoo 채택.
- **FRED CSV** (`providers/fred.ts`) — 거시 시리즈. **best-effort**: 막히면 누락 → ARDS 엔진이 시장 프록시로 자동 폴백.

## R2 캐시 폴백 (`cache.ts`) — 가용성
"가져온 데이터를 스토리지에 넣고 꺼내 쓴다." fetch 성공분은 R2(`cache/<kind>/<id>.json`)에 갱신 저장,
**실패분은 직전 저장본으로 폴백(stale)** → Yahoo/FRED 가 한 번 삐끗(429·일시장애)해도 마지막 정상 데이터로 계속 동작.
둘 다 없으면 누락(엔진 결측 처리). `data_quality` 에 `*_from_cache` / 누락 수 기록.
(Stooq 처럼 Worker 가 직접 못 받는 소스를 외부 로더로 같은 키에 적재해 두는 용도로도 확장 가능.)

## 파이프라인 (`daily.ts` → `signals.ts`)
1. `loadHystState`(R2 `state/ards-regime.json`) — 직전 히스테리시스 상태
2. Yahoo/FRED 수집(부분 성공 허용)
3. `computeSignals`(순수): `runArds` + `runAmqs` → 시그널 행 + 페이로드 + 새 상태
4. `persistSignals`(D1 signals upsert) + R2 `signals/latest.json`(s-maxage=300) + `saveHystState`

## 시그널 매핑 (D1 signals)
- **ARDS**: 1행, ticker `QQQ`(국면 대표). action→`BUY|SELL|HOLD`, 추세붕괴+비매도면 `SHORT_TERM_RISK`. detail=verdict.
- **AMQS**: 종목별, 티어→`BUY|SELL|HOLD`(EXCLUDED 등 제외). score=총점, detail에 레짐·서브테마.

## 알려진 단순화 (후속)
- **AMQS marketCaps 미공급** → 사전필터의 시총 조건 스킵(변동성·베타·갭다운 필터는 적용). 시총 소스 연결 시 보강.
- 10분 시세 스냅샷(`runMarketSnapshot`)은 Finnhub 키 확보 후 구현(#9b).
- Workers 무료 subrequest 한도 50/req → 현재 ~40심볼. 초과 시 두 크론으로 분할 또는 배치.

## 로컬 테스트
```bash
npm run dev:cron        # wrangler dev -c cron-worker/wrangler.toml --test-scheduled
npm test                # 파서·computeSignals·persist 단위테스트 (test/cron)
```
