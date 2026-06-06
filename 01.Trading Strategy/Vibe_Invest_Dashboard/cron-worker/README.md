# cron-worker — 스케줄 전용 Worker

Pages 가 Cron Trigger 를 지원하지 않으므로 주기 작업만 담당. 결과는 D1/R2 에 미리 저장 →
Pages Functions(API)는 읽기만 + CDN 엣지 캐시.

## 크론
| cron (UTC) | 핸들러 | 동작 | 상태 |
|---|---|---|---|
| `30 21 * * 1-5` | `runDailySignals` | 일봉 수집 → ARDS/AMQS 엔진 → D1 signals + R2 스냅샷 + 상태 영속화 | ✅ |
| `*/10 * * * *` | `runMarketSnapshot` | 시세/급등락 → R2 + D1 | ⏸ 스텁(Finnhub 키 필요) |

## 데이터 소스 (무료, 키 불필요)
- **Yahoo chart API** (`providers/yahoo.ts`) — 가격/지수/금리/VIX. 엔진 심볼(`^GSPC` 등) 그대로, adjclose.
  - ※ Stooq 는 봇 차단(PoW)으로 Worker fetch 불가 → Yahoo 채택.
- **FRED CSV** (`providers/fred.ts`) — 거시 시리즈. **best-effort**: 막히면 누락 → ARDS 엔진이 시장 프록시로 자동 폴백.

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
