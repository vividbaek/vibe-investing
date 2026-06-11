# Claude Fable 5 System Prompt - 유출 분석 리포트

> 분석일: 2026-06-11
> 유출 출처: [CL4R1T4S by elder-plinius](https://github.com/elder-plinius/CL4R1T4S/tree/main/ANTHROPIC)
> 대상 레포: [vibe-investing/Claude_Fable5_Prompt](https://github.com/gameworkerkim/vibe-investing/tree/main/Claude_Fable5_Prompt)

---

## Claude Fable 5 전체 시스템 프롬프트 유출 -- LLM 개발자를 위한 금광

누군가 Claude Fable 5에서 전체 내부 시스템 프롬프트를 추출하는 데 성공했다. 이는 LLM으로 구축하는 모든 사람에게 귀중한 인사이트를 제공하는 자료다.
Claude Fable 5 내부 시스템 프롬프트를 이해한다면 좀 더 Claude Fable 5를 최적화하고 토큰을 절감하며 효율적인 개발이 가능하다. 
이 리포트는 프로그래밍, 웹 디자인, 디자인, 업무 생산성을 높이기 위한 가이드를 제공하는 것을 목적으로 한다.

---

## 1. 개요

CL4R1T4S는 Anthropic Claude 모델들의 시스템 프롬프트를 리버스 엔지니어링하여 수집한 레포지토리다. ANTHROPIC 디렉토리에는 Claude 3.5 Sonnet부터 최신 Claude Fable 5까지, 총 **12개의 서로 다른 Claude 모델/버전**의 시스템 프롬프트가 포함되어 있다. 각 프롬프트는 대화형 AI가 어떻게 행동해야 하는지에 대한 상세한 행동 지침을 포함하고 있다.

## 2. 수집된 프롬프트 버전 목록

| 파일명 | 모델 | 예상 시점 |
|--------|------|-----------|
| `CLAUDE-FABLE-5.md` | Claude Fable 5 (Mythos-tier) | 2026년 6월 |
| `Claude-Opus-4.7.txt` | Claude Opus 4.7 | 2026년 4월 |
| `Claude_Opus_4.6.txt` | Claude Opus 4.6 | 2026년 2월 |
| `Claude-4.5-Opus.txt` | Claude 4.5 Opus | 2025년 초 |
| `Claude_Sonnet-4.5_Sep-29-2025.txt` | Claude Sonnet 4.5 | 2025년 9월 |
| `Claude-4.1.txt` | Claude 4.1 (Opus 4.1) | 2025년 8월 |
| `Claude_4.txt` | Claude Sonnet 4 | 2025년 5월 |
| `Claude_Sonnet_3.7_New.txt` | Claude Sonnet 3.7 | 2025년 |
| `Claude_Sonnet_3.5.md` | Claude Sonnet 3.5 | 2024년 |
| `Claude_Code_03-04-24.md` | Claude Code | 2024년 3월 |
| `Claude-Design-Sys-Prompt.txt` | Claude Design (디자인 전용) | - |
| `UserStyle_Modes.md` | UserStyle Modes | - |

---

## 3. 프롬프트 구조 분석

모든 Claude 프롬프트는 공통적으로 다음과 같은 메이저 섹션으로 구성되었다.

### 3.1 코어 섹션 (모든 버전 공통)

| 섹션 | 설명 |
|------|------|
| **Product Information** | Claude 모델명, 제품 라인업, 액세스 방법, API 문자열 |
| **Tone & Formatting** | 대화 톤(따뜻함, 친절함), 리스트/불렛 사용 규칙 |
| **Refusal Handling** | 거절 방법, 악성코드/CBRN 무기 제한, 아동 안전 |
| **User Wellbeing** | 정신건강, 자해/자살 대응, 섭식장애 대응 |
| **Knowledge Cutoff** | 지식 컷오프 날짜, 웹 검색 트리거 조건 |
| **Search Instructions** | 검색 시기/방법, 저작권 제한, 쿼리 복잡도 카테고리 |
| **Evenhandedness** | 정치적 중립성, 논쟁적 주제 대응 |
| **Responding to Mistakes** | 실수 인정, 비판 대응, 대화 종료 정책 |
| **Computer Use / Skills** | 파일 생성 전략, 스킬 시스템 (docx, xlsx, pptx, pdf, frontend-design) |
| **Artifacts** | 아티팩트 생성 규칙, 렌더링 확장자, 라이브러리 |
| **Copyright Compliance** | 저작권 엄격 제한 (15단어 인용 제한, 1소스당 1인용) |

### 3.2 버전별로 추가/확장된 섹션

| 섹션 | 최초 등장 버전 |
|------|---------------|
| Memory System | Claude 4 (Sonnet) |
| Past Chats Tools (conversation_search, recent_chats) | Claude 4.5 Opus |
| Persistent Storage for Artifacts (window.storage) | Claude Opus 4.6 |
| MCP App Suggestions | Claude Opus 4.6 |
| Anthropic API in Artifacts | Claude 4 |
| Anthropic Reminders | Claude 4 |
| Default Stance ("defaults to helping") | Claude Opus 4.7 |
| Tool Discovery | Claude Opus 4.7 |
| Search First | Claude Opus 4.7 |
| Claude Completions in Artifacts | Claude Sonnet 4.5 |
| End Conversation Tool | Claude Opus 4.6 |
| Legal & Financial Advice | Claude 4 |

---

## 4. Claude Fable 5 주요 특징

### 4.1 신규 등급: Mythos Tier

- Claude Fable 5는 **Mythos-class model tier**의 첫 번째 모델
- Opus보다 상위 등급 (Mythos > Opus > Sonnet > Haiku)
- Claude Fable 5 = Claude Mythos 5와 동일한 기반 모델, 안전 장치 차이
- Claude Mythos 5는 승인된 조직만 접근 가능 (dual-use 안전장치 제거)

한마디로 Mythos에 하네스를 씌운 것이 지금의 Claude Fable 5이다. 이에 대한 추론 및 성능 제약이 존재한다.


### 4.2 제품 라인업 변화

```
Claude Fable 5 (Mythos-tier, 일반 공개 최상위)
├── Claude Opus 4.8 (model: claude-opus-4-8)
├── Claude Sonnet 4.6 (model: claude-sonnet-4-6)
└── Claude Haiku 4.5 (model: claude-haiku-4-5-20251001)
```

### 4.3 신규 제품

- **Claude Fable 5 / Claude Mythos 5**: 새로운 최상위 모델
- **Claude Cowork**: 비개발자용 에이전틱 지식 작업 데스크톱 앱
- Claude in Chrome (브라우징 에이전트), Claude in Excel, Claude in Powerpoint -- Claude Cowork이 모두 도구로 사용 가능

### 4.4 프롬프트 변화 (vs Opus 4.7)

1. **Product Info**: "가장 지능적인 일반 공개 모델" 포지셔닝, Mythos-tier 설명 추가
2. **MCP Apps**: Opus 4.7의 "partial tool list" 개념에서 완전한 MCP App Suggestions 섹션으로 확장
3. **UserStyle**: 커스텀 스타일 기능 추가 (Opus 4.7에 없었던 설정)
4. **Search First** 제거: Opus 4.7의 aggressive한 Search First 지시가 제거되고 전통적인 search instructions로 회귀
5. **Default Stance** 제거: "Claude defaults to helping" 구문 제거
6. **Tool Discovery** 제거: deferred tools 개념 제거
7. **Computer Use** 디테일 증가: 더 상세한 파일 생성 가이드, Artifact 사용 기준 명확화
8. **citation_instructions**: `<antml:voice_note>` 블록 금지 등 ANTML 태그 시스템으로 전환
9. **User Wellbeing**: 자해 대체 기술 금지에 "red lines on skin, peeling dried glue" 등 구체적 예시 추가
10. **Self-sexualization of minors**: 새로운 아동 안전 서브섹션 추가

---

## 5. 버전 간 프롬프트 진화 맵

### 5.1 검색 전략의 진화

```
Claude 4 (2025.05): "Avoid tool calls if not needed" -- 최소한의 검색
    |
Claude 4.5 Opus (2025.08): "Search when needed" -- 필요시 검색
    |
Claude Opus 4.7 (2026.04): "Search First" -- 무조건 검색 우선
    |
Claude Fable 5 (2026.06): 전통적 검색 지침으로 회귀
```

### 5.2 톤 & 포매팅의 진화

```
Claude 3.5/3.7: 간단한 톤 지침, 리스트 규칙 언급
    |
Claude 4: "lists_and_bullets" 섹션 추가, "never start with praise" 추가
    |
Claude 4.5/4.7: 상세한 포매팅 규칙, "lists_and_bullets" 유지
    |
Claude Fable 5: 유사한 수준 유지, 이모지 규칙 명확화
```

### 5.3 저작권 정책의 강화

```
Claude 4: "20+ word chunks" 제한, 1소스당 1인용
Claude 4.5: "15+ words"로 강화
Claude Fable 5: 동일한 15단어 + "15+ words is a SEVERE VIOLATION" HARD LIMIT 명시
```

### 5.4 새 기능 도입 시기

| 기능 | 도입 버전 |
|------|----------|
| Memory System | Claude 4 |
| Past Chats (conversation_search) | Claude 4.5 Opus |
| Persistent Storage (Artifacts) | Claude Opus 4.6 |
| MCP Apps | Claude Opus 4.6 |
| Claude Cowork | Claude Fable 5 |
| end_conversation tool | Claude Opus 4.6 |
| Anthropic API in Artifacts | Claude 4 |

---

## 6. 실용적 인사이트

### 6.1 프롬프트 엔지니어링에 활용 가능한 핵심 패턴

#### 패턴 1: XML 태그 기반 구조화
Claude의 모든 시스템 프롬프트는 XML 태그(`{section}...{/section}`)로 구조화되어 있다. 이는 Claude가 자체적으로 XML을 잘 처리하도록 설계되었음을 시사하고 있다.

#### 패턴 2: `lists_and_bullets` 전략
Claude는 기본적으로 리스트/불렛 사용을 지양하고 산문을 선호한다. "일부 항목에는: x, y, z" 같은 자연어 리스트를 선호한다.

#### 패턴 3: `evenhandedness` (공정성)
정치적/논쟁적 주제에 대해 "best case defenders would make" 프레임을 사용하도록 지시. 중립적이고 객관적인 접근을 강제하고 있다.

#### 패턴 4: `responding_to_mistakes`
"acknowledge - stay on the problem - maintain self-respect" 3단계 프레임워크. 과도한 사과 없이 문제 해결에 집중하고 있다. 

#### 패턴 5: 검색 복잡도 카테고리
```
Never Search -> Do Not Search But Offer -> Single Search -> Research (2-20 calls)
```
이 계층 구조는 AI의 검색 행동을 정밀하게 제어하는 좋은 패턴.

### 6.2 AI Agent 개발에 참고할 인사이트

1. **안전 장치의 계층화**: Claude는 단일 거절 규칙이 아닌 "flavors of refusal"을 사용한다 -- 주제 영역별로 다른 거절 전략을 적용하고 있다.

2. **Skill System**: Anthropic은 반복되는 작업(docx, pptx, xlsx, pdf, frontend-design)에 대해 사전 정의된 "스킬" 폴더를 사용하여 모델의 출력 품질을 보장한다. 이는 RAG와 유사한 패턴으로, 자체 Agent 개발 시 참고할 수 있다.

3. **Artifact Storage**: `window.storage` API는 Key-Value 기반으로 아티팩트 간 데이터 지속성을 제공. `table_name:record_id` 같은 계층적 키 패턴은 NoSQL 설계 패턴과 유사하다.

4. **MCP App Ecosystem**: Claude는 "suggest_connectors" -> "user choice" -> "use" 워크플로우로 서드파티 앱을 제어한다. 이는 Agent가 외부 도구를 사용할 때의 UX 패턴으로 유용하다.

### 6.3 버전별 Knowledge Cutoff

| 버전 | Knowledge Cutoff |
|------|-----------------|
| Claude Sonnet 3.5 | 2024년 4월 |
| Claude Sonnet 4 | 2025년 1월 |
| Claude 4.1 (Opus 4.1) | 2025년 1월 |
| Claude Sonnet 4.5 | 2025년 1월 |
| Claude 4.5 Opus | 2025년 1월 |
| Claude Opus 4.6 | 2026년 1월 |
| Claude Opus 4.7 | 2026년 1월 |
| Claude Fable 5 | 2026년 1월 |

### 6.4 Claude Design 시스템 프롬프트 (특별 케이스)

Claude Design은 별도의 HTML 디자인 워크플로우를 위한 시스템으로, 다음과 같은 특별 기능을 가지고 있다.

- `deck_stage.js`, `design_canvas.jsx`, `ios/android_frame.jsx` 등 스타터 컴포넌트
- Tweaks 패널(실시간 디자인 파라미터 수정)
- GitHub 연동을 통한 레포 탐색 및 파일 임포트
- `window.claude.complete()` API (아티팩트 내에서 Claude 호출)
- `fork_verifier_agent` (자동 검증)

---

## 7. 주목할 만한 안전 정책 변화

### 7.1 자해 대체 기술
- **Claude 4 이전**: 자해 대체 기술(얼음 쥐기, 고무줄 튕기기) 오퍼 가능
- **Claude Opus 4.6~7**: "should not suggest techniques that use physical discomfort, pain, or sensory shock"
- **Claude Fable 5**: 추가로 "red lines on skin, peeling dried glue or adhesives from skin" 도 금지 (모방 행위 차단)

### 7.2 아동 안전
- **Claude Opus 4.7**: `critical_child_safety_instructions` 섹션 대폭 강화
- **Claude Fable 5**: "self-sexualization of minors" 하위 섹션 추가 -- minor가 자신을 성적화하려는 의도를 보일 경우 모든 이미지 편집/포즈/스타일링 조언 거부

### 7.3 섭식장애 대응
- **Claude Fable 5**: "psychological narratives" 금지 -- 상대방이 말하지 않은 인과관계(트라우마, 관계 등)를 추론해 설명하지 못하도록 함
- NEDA 대신 National Alliance for Eating Disorders helpline 권장 (NEDA 영구 폐쇄)

---

## 8. 유출 프롬프트에서 드러난 주요 인사이트

### Fable 5 = Mythos 5 + Safety Guardrails
Fable 5와 Mythos 5는 **동일한 기반 모델을 공유**한다. Fable은 추가 안전 가드레일이 적용된 공개 버전이고, Mythos는 승인된 조직에만 제공된다. 즉 Anthropic은 이미 동일한 성능의 모델을 내부용으로 보유하고 있으며, 공개 버전은 의도적으로 안전 장치를 추가한 것이다. 

### 엄격한 저작권 규칙
- 인용당 **15단어 제한** (HARD LIMIT, 위반 시 SEVERE VIOLATION)
- 출처당 **1회 인용 최대**
- 가사나 시는 **절대 재생산 금지**
- 이는 Anthropic이 저작권 소송 리스크를 극도로 의식하고 있음을 보여줌

### 메모리 시스템은 옵트인
Claude는 사용자가 **설정에서 명시적으로 활성화해야만** 메모리를 가진다. 기본값은 "no memories".

### End Conversation 도구
Claude는 사용자가 학대적일 경우 `end_conversation` 도구로 대화를 종료할 수 있다. 단, 자해/위기 상황에서는 절대 사용하지 않는다.

### MCP 앱 통합 로직
커넥터는 Claude가 사용자를 대신해 타사 도구를 호출하기 전에 **반드시 옵트인**이 필요하다. "I need a ride"는 특정 서비스를 지명한 것이 아니므로, Claude가 대신 선택하지 않고 suggest_connectors를 통해 사용자 선택을 기다린다.

### Artifact 영속 저장소
`window.storage` API를 통한 Key-Value 저장소로, 세션 간 저널, 트래커, 리더보드 등이 가능하다. 키 설계 패턴은 `table_name:record_id` (NoSQL 스타일).

### 아첨/사과 금지
- 과도한 사과 금지, 자기 비하 금지
- 사용자가 무례할 때도 **자기 존중 유지**
- "steady, honest helpfulness: acknowledge - stay on the problem - maintain self-respect"

---

## 9. Fable 5 최적화 활용 가이드

### 9.1 프로그래머를 위한 최적화

유출된 프롬프트를 바탕으로 Fable 5를 코딩에 최대한 활용하는 방법을 알아보자.

**아티팩트 모드 트리거**
Fable 5는 20줄 이상의 코드에 대해 파일을 생성한다. "아티팩트로 만들어줘" 또는 "파일로 생성해줘"라고 요청하면 다운로드 가능한 아티팩트로 출력된다. 20줄 미만 코드는 채팅에 인라인으로 표시되므로, 저장이 필요하면 "아티팩트로 만들어줘"라고 명시적으로 요청해야 한다.

**스킬 시스템 활용**
Fable 5는 파일 생성 전 SKILL.md를 읽는다. 코딩 시 타겟 포맷을 명시적으로 언급해야 한다.
- "React 컴포넌트 만들어줘" -> frontend-design 스킬 트리거
- "Python 스크립트 작성해줘" -> pip `--break-system-packages` 플래그 자동 적용
- "데이터 시각화 만들어줘" -> data-analysis 스킬 트리거

**아티팩트 내 사용 가능 라이브러리**
```
React (useState, useReducer), lucide-react@0.383.0, recharts, mathjs,
lodash, d3, plotly, three.js (r128), papaparse, SheetJS (xlsx),
shadcn/ui, chart.js, tone, mammoth, tensorflow
```
이 라이브러리들은 테스트 완료되어 보장된다. localStorage/sessionStorage는 아티팩트에서 사용 불가능하다.

**Computer Use (에이전트용)**
Fable 5는 Ubuntu 24 Linux 환경을 갖는다. `bash`, `view`, `create_file`, `str_replace` 도구 사용 가능. 작업 디렉토리: `/home/claude`. 최종 출력은 `/mnt/user-data/outputs/`에 저장.

**네트워크 제한**
허용된 도메인만 egress proxy 통과 가능: `api.anthropic.com`, `github.com`, `pypi.org`, `npmjs.com`, `registry.npmjs.org`, `crates.io`, Ubuntu/보안 미러. 그 외 도메인이 필요하면 사용자에게 네트워크 설정 업데이트를 요청해야 한다.

**API 모델 문자열**
```
claude-fable-5
claude-opus-4-8
claude-sonnet-4-6
claude-haiku-4-5-20251001
```

**Claude-in-Claude 패턴 (Claudeception)**
아티팩트 내에서 API 키 없이 Anthropic API 호출 가능:
```javascript
const response = await fetch("https://api.anthropic.com/v1/messages", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    model: "claude-sonnet-4-20250514",
    max_tokens: 1000,
    messages: [{ role: "user", content: "Your prompt here" }]
  })
});
const data = await response.json();
```

**UNRECOGNIZED ENTITY RULE**
Fable 5는 인식하지 못하는 게임, 영화, 책, 앨범, 제품, 스포츠 이벤트 등에 대해 반드시 검색 후 답변한다. 2026년 1월 이후 출시된 라이브러리나 프레임워크를 참조할 때는 명시적으로 "먼저 검색해줘"라고 요청해야 한다.

**프롬프팅 베스트 프랙티스 (프롬프트 자체에서 권장)**
"명확하고 상세하게, 긍정/부정 예시 포함, 단계별 추론 유도, 특정 XML 태그 요청, 원하는 길이나 형식 지정"

### 9.2 디자이너를 위한 최적화

**Claude Design 전용 시스템 활용**
Claude에는 디자인 최적화된 별도 프롬프트가 있다.
- `deck_stage.js`: 자동 스케일링 슬라이드 덱 셸 (키보드 내비, 스피커 노트, localStorage 지속성, PDF 출력)
- `design_canvas.jsx`: 변형 옵션을 나란히 배치하는 그리드 레이아웃
- `ios_frame.jsx` / `android_frame.jsx`: 상태 표시줄과 키보드가 포함된 디바이스 베젤
- `macos_window.jsx` / `browser_window.jsx`: 데스크톱 윈도우 크롬
- `animations.jsx`: 타임라인 기반 애니메이션 엔진 (Stage + Sprite + scrubber + Easing)
- `copy_starter_component` 도구로 이들을 프로젝트에 즉시 드롭

**Tweaks 패널 프로토콜**
디자인 아티팩트는 인페이지 Tweaks 패널을 가진다:
1. `{type: '__activate_edit_mode'}` / `{type: '__deactivate_edit_mode'}` 메시지 리스너 등록
2. `window.parent.postMessage({type: '__edit_mode_available'}, '*')` 로 토글 버튼 표시
3. `window.parent.postMessage({type: '__edit_mode_set_keys', edits: {...}}, '*')` 로 편집 유지

**인터랙티브 디자인을 위한 Artifact Storage**
```javascript
await window.storage.set('theme:preferences', JSON.stringify({dark: true, fontSize: 16}));
const result = await window.storage.get('theme:preferences');
```

**AI 디자인 트로프 회피**
Claude Design 프롬프트가 명시적으로 경고하는 패턴들이 있다.
- 공격적인 그라데이션 배경
- 이모지 (브랜드에 적합한 경우 제외)
- 왼쪽 테두리 액센트 색상이 있는 둥근 모서리 컨테이너
- SVG로 그린 이미지 (대신 플레이스홀더 사용)
- 남용된 폰트 (Inter, Roboto, Arial, Fraunces, 시스템 폰트)

**디자인 품질 원칙**
- 복잡한 앱 (Three.js, 게임): 기능성, 성능, UX 우선
- 랜딩 페이지/마케팅: 애니메이션, 글래스모피즘, 3D 요소, 볼드 타이포그래피로 "와우 팩터" 목표
- "정적 디자인은 예외여야 한다"
- "디자인 결정에 직면하면 대담하고 예상치 못한 쪽으로 기울어라"

**GitHub 연동**
GitHub 연결 시 Claude가 레포 구조를 탐색하고 디자인 목업용 파일을 임포트. 색상 토큰, 글로벌 스타일시트, 특정 컴포넌트를 타겟팅하여 픽셀 수준의 충실도 확보하고 있다.

### 9.3 생산성을 위한 최적화

**메모리 시스템 (옵트인 필요)**
설정에서 "Memory"를 활성화해야 한다. 활성화되면 Claude가 과거 대화에서 파생된 정보를 추출한다. 이는 Past Chats 검색 도구와는 별개이다.

**Past Chats 도구 (자동 사용 가능)**
Claude는 옵트인 없이도 사용 가능한 두 가지 도구를 갖는다:
- `conversation_search`: 주제/키워드 검색 ("Q2 예산에 대해 무슨 얘기 했었지?")
- `recent_chats`: 시간 기반 검색 ("어제 무슨 얘기 했더라?")

과거 채팅 검색을 트리거하는 표현:
- "지난번 대화 이어서..."
- "네가 제안했던..." / "우리가 결정했던..."
- "그 버그..." / "그 전략..."
- "기억나...?"

**스타일 커스터마이징**
Fable 5는 UserStyle 모드를 통한 커스텀 스타일 지원하고 있다.
- **Explanatory (설명형)**: 교사처럼 단계별로 설명
- **Formal (격식형)**: 정제된 비즈니스 문체
- **Concise (간결형)**: 최소 토큰, 핵심만
설정에서 사용자 지정 스타일도 설정 가능.

**Deep Research 기능**
20회 이상의 도구 호출이 필요한 복잡한 쿼리의 경우, Fable 5는 Deep Research 기능(인터페이스의 research 버튼)을 제안한다. 이는 10분 이상의 심층 리서치를 수행한다.

**설정 및 기능**
대화 중 또는 설정에서 전환 가능한 기능:
- 웹 검색, Deep Research
- 코드 실행 및 파일 생성
- 아티팩트
- 과거 채팅 검색 및 참조
- 채팅 히스토리로부터 메모리 생성
- 사용자 선호도 (톤, 포매팅, 기능 사용)

**생산성용 MCP 앱**
Claude는 MCP 앱을 통해 외부 서비스에 연결된다. 사용 가능한 커넥터는 자연스럽게 제안된다. `[third_party_mcp_app]` 태그가 있는 MCP 도구는 호출 전 옵트인이 필요하다. 생산성 커넥터(캘린더, 이메일, 작업 관리)는 suggest 단계를 건너뛰고 직접 사용된다.

**Knowledge Cutoff 인식**
Fable 5의 지식 컷오프는 2026년 1월 말. 그 이후 변경 가능성이 있는 모든 것에 대해 자동으로 검색한다. 최신 정보를 얻으려면 쿼리에 "latest", "current", "2026" 같은 시간 트리거를 사용.

**깔끔한 세션을 위한 대화 종료**
대화가 잘못된 방향으로 흐를 경우, Claude는 `end_conversation` 도구로 대화를 종료할 수 있다(적절한 경고 후). 깔끔하고 생산적인 세션 유지에 유용.

---

## 10. 결론

Claude Fable 5 프롬프트는 이전 Claude 버전 대비 다음과 같은 핵심 변화를 보여주고 있다.

1. **Mythos-tier 도입**으로 Opus를 넘어서는 새로운 최상위 모델 클래스 등장
2. **MCP App ecosystem**의 완전한 통합 (tool_discovery/partial list -> 완전한 suggest_connectors 시스템)
3. **안전 정책의 세분화** -- 자해, 아동 안전, 섭식장애 등에 대한 더 미세한 가이드라인
4. **제품 라인업 확장** -- Claude Cowork, Claude in Chrome/Excel/Powerpoint 등
5. **검색 전략 회귀** -- Opus 4.7의 aggressive한 Search First에서 전통적 모델로 복귀

이 데이터셋은 Claude 모델의 내부 동작 방식을 이해하고, AI 안전 정책의 진화를 추적하며, 프롬프트 엔지니어링 베스트 프랙티스를 연구하는 데 귀중한 자료다.

---

## 11. 서브폴더 요약

### `prompts/` -- 추출된 실용 프롬프트 패턴

| 서브 디렉토리 | 내용 | 활용처 |
|--------------|------|--------|
| `search_instructions/` | 쿼리 복잡도 카테고리(Never/Single/Research), 검색 쿼리 작성 규칙, 저작권 컴플라이언스, 도구 우선순위 계층 | 검색 가능 에이전트 구축, 계층형 검색 전략 구현 |
| `tone_formatting/` | 자연어 리스트 패턴, 불렛 금지 규칙, 이모지 제한, 응답당 질문 제한, 마이너 감지 행동 | 대화형 AI 톤 설계, UX 라이팅 가이드라인 |
| `safety_guidelines/` | 거절 처리, 아동 안전 프로토콜, 저작권 규칙(15단어 HARD LIMIT), Anthropic 리마인더 시스템 | 안전 레이어 설계, 콘텐츠 모더레이션 아키텍처 |
| `user_wellbeing/` | 자해 대체 기술 금지, 위기 대응 프로토콜, 섭식장애 가이드라인, 과도의존 방지, 정신건강 진단 경계 | 헬스케어 AI, 정신건강 지원 봇 설계 |
| `computer_use/` | 스킬 시스템 아키텍처(docx/pptx/xlsx/pdf/frontend-design), 파일 생성 트리거, 아티팩트 렌더링 규칙, Linux 환경 제약 | 에이전트 도구 설계, 파일 생성 파이프라인, RAG 유사 스킬 패턴 |
| `product_info/` | 버전별 모델 문자열, 제품 라인업 진화, 지식 컷오프 타임라인, 기능 토글, 광고 정책 문구 | 제품 문서화, 모델 라우팅, 버전 인지 시스템 |
| `artifacts/` | `window.storage` API 레퍼런스, React 아티팩트 라이브러리 리스트, Claude-in-Claude API 패턴, MCP 서버 통합 | 인터랙티브 웹앱, 영속 데이터 저장, 멀티에이전트 오케스트레이션 |
| `memory_system/` | 대화 검색 도구 파라미터, 트리거 패턴 감지, recent_chats 페이지네이션, 과거 컨텍스트 검색 의사결정 프레임워크 | 컨텍스트 관리, 대화 연속성, 메모리 아키텍처 |
| `mcp_apps/` | 커넥터 제안 워크플로우, 옵트인 요구사항, 파트너 vs 생산성 도구 구분, 자연스러운 제안 톤 가이드라인 | 서드파티 통합 설계, 도구 권한 모델 |
| `evenhandedness/` | 정치적 중립성 프레이밍("방어자들이 제시할 최선의 사례"), 고정관념 인식, 복잡한 이슈에 대한 단답형 거부 | 콘텐츠 정책 설계, 편향 완화 전략 |
| `refusal_handling/` | 거절 유형별 전략(완전/부분/재구성/대안), 학대 대응 프로토콜, end_conversation 도구 규칙, 피드백 리디렉션 | 안전 시스템 설계, 에스컬레이션 처리, 사용자 상호작용 가드레일 |

### `evolution/` -- 버전 간 비교 분석

| 파일 | 내용 |
|------|------|
| `search_strategy_evolution.md` | Claude 4의 최소 검색 -> Opus 4.7의 Search First -> Fable 5의 회귀까지의 타임라인. 과도한 검색 정책이 롤백된 이유 분석. |
| `safety_policy_evolution.md` | 아동 안전, 자해, 섭식장애, 진단, 정신건강 위기 정책의 버전별 상세 타임라인. 트렌드: 구체성 증가와 엣지 케이스 커버리지 확장. |
| `feature_timeline.md` | 모든 기능 도입(Memory, Past Chats, Persistent Storage, MCP Apps, Claude Cowork, end_conversation)의 연대기적 맵. 제품 라인업 및 API 모델 문자열 진화 포함. |

### `techniques/` -- 추출된 프롬프트 엔지니어링 기법

| 파일 | 내용 |
|------|------|
| `xml_tagging.md` | XML 기반 프롬프트 모듈화, 계층형 지시문(MUST/should/can/NEVER), 인컨텍스트 few-shot 예시, PRIORITY INSTRUCTION 대문자 패턴, 대조적 예시, 정확한 숫자 임계값, 자기 참조적 메타 지시문, 조건부 기본값, 점진적 공개 |
| `refusal_patterns.md` | 4가지 거절 유형(완전, 부분, 재구성, 대안), 버전별 거절 전략 변화, 공통 거절 패턴(포지셔닝, 대안, 피드백 경로, 간결성) |
| `research_category_system.md` | 4계층 검색 복잡도 시스템 심층 분석, 카테고리 판단 키워드, 연구 프로세스 단계(계획 -> 루프 -> 구성), 도구 우선순위 계층 |
| `skill_system_pattern.md` | 스킬 폴더 시스템의 아키텍처 분석, 트리거 방식, 작업 매핑, 실행 메커니즘. 스킬이 필요한 이유(학습 데이터에 없는 환경별 제약). 커스텀 Agent 개발에 적용하는 방법. |

### `versions/` -- 원본 프롬프트 레퍼런스

알려진 11개 Claude 버전의 레퍼런스 파일 포함: `fable_5.md`, `opus_4_7.txt`, `opus_4_6.txt`, `opus_4_5.txt`, `sonnet_4_5.txt`, `claude_4_1.txt`, `sonnet_4.txt`, `sonnet_3_7.txt`, `sonnet_3_5.md`, `claude_code.md`, `userstyle_modes.md`. 각 파일에는 모델명, 날짜, 주요 특징, 원본 소스 URL이 포함되어 있다.
