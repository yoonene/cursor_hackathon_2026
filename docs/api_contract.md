# AI Saju Counselor — Frontend ↔ Backend API Contract

## Version

**v7 — Compatibility Intake via `partner` Field + SSE Streaming**  
(v7: `ChatRequest.partner` 필드 추가로 궁합 팝업 결과를 구조화 전송; `ChatResponse.partner_intake_requested` 플래그 추가; `POST /chat/stream` SSE 스트리밍 엔드포인트 추가; `AgentTraceStep.step` enum 확장. v6 변경 내용: English-first `chart_identity` and English `chart_digest` strings on `saju_report`.)

---

# 0. One-page overview

## 0.1 Product flow

```text
1. User enters basic information in a fixed intake form
   - name / nickname
   - date of birth
   - time of birth (optional)
   - gender (optional)

2. Frontend sends the form to POST /reading/start

3. Backend:
   - computes deterministic base saju data
   - generates the full initial interpretation
   - builds the full saju report dashboard

4. Frontend shows:
   - AI's first full reading in chat
   - Full Saju Report tab in the right panel

5. User asks follow-up questions in chat

6. Frontend sends follow-up messages to POST /chat

7. Backend:
   - understands the concern
   - decides which reading is relevant
   - calls the appropriate tool if needed
   - updates the Counseling Board

8. Frontend shows:
   - the AI counselor's reply
   - the live Counseling Board
   - the Full Saju Report remains available in a separate tab
```

---

## 0.2 System overview

```text
┌────────────────────┐
│   Intake Form      │
│ - name             │
│ - birth date       │
│ - birth time       │
│ - gender           │
└─────────┬──────────┘
          │
          │ POST /reading/start
          ▼
┌──────────────────────────────────────┐
│ Backend                              │
│ FastAPI                              │
│                                      │
│ 1. Compute base saju                 │
│ 2. Generate full initial reading     │
│ 3. Build saju_report                 │
│ 4. Build initial counseling_board    │
└─────────┬────────────────────────────┘
          │
          │ InitialReadingResponse
          ▼
┌──────────────────────────────────────┐
│ Frontend                             │
│ - Chat area: first interpretation    │
│ - Right panel: Full Saju Report tab  │
└─────────┬────────────────────────────┘
          │
          │ user follow-up message
          ▼
┌────────────────────┐        POST /chat        ┌──────────────────────────────┐
│       User         │ ───────────────────────▶ │            Backend           │
└────────────────────┘                         │ 1. Understand message        │
                                               │ 2. Decide next reading       │
                                               │ 3. Run tool if needed        │
                                               │ 4. Build latest board state  │
                                               └──────────────┬───────────────┘
                                                              │
                                                              │ ChatResponse
                                                              ▼
                                               ┌──────────────────────────────┐
                                               │           Frontend           │
                                               │ - Chat response              │
                                               │ - Counseling Board update    │
                                               │ - Full Report still available│
                                               └──────────────────────────────┘
```

---

## 0.3 Right-panel structure

```text
┌──────────────────────────────────────────────┐
│ [ Full Saju Report ] [ Counseling Board ]    │
├──────────────────────────────────────────────┤
│ Full Saju Report tab                         │
│ - saju_report (chart_identity + chart_digest)│
│ - full dashboard shown first                 │
│ - static after creation                      │
├──────────────────────────────────────────────┤
│ Counseling Board tab                         │
│ - profile_summary (chart_identity_summary)  │
│ - counseling_board.active_reading           │
│ - counseling_board.insight_summaries        │
│ - counseling_board.history                  │
└──────────────────────────────────────────────┘
```

---

## 0.4 Response ownership

```text
Backend owns:
- meaning
- state
- tool routing
- which tab is recommended
- which active-reading template should be shown
- the complete latest right-panel snapshot

Frontend owns:
- layout
- visuals
- animations
- template-specific components
- tab interaction
```

---

# 1. Core principles

## 1.1 Product principle

This is **not** a menu-based fortune app. It is a conversational AI saju counselor.

The user does not choose features such as:
- Compatibility
- Love fortune
- Career fortune
- Best timing

Instead, after the initial full reading, the user speaks naturally and the backend decides:
- what the user is asking,
- whether a reading is needed,
- which tool should be used,
- which visual template should be shown.

---

## 1.2 Three UX phases

### Phase 1 — Fixed intake
The user enters basic structured information through a form.

### Phase 2 — Full initial reading
The backend generates a full initial saju interpretation and a static `saju_report` dashboard.

### Phase 3 — Conversational counseling
The user continues in chat. The backend updates the live `counseling_board` based on the conversation.

---

## 1.3 Source of truth

- `saju_report` is the source of truth for the **Full Saju Report** tab.
- `counseling_board` is the source of truth for the **Counseling Board** tab.
- `ui_event` is only an animation hint.
- The frontend must render correctly even if `ui_event` is absent.

---

## 1.4 Full snapshot rule

After the initial reading is created, the backend returns the **full latest right-panel snapshot** on every response:

- `saju_report`
- `counseling_board`

Even though `saju_report` becomes static, it is still included on every response for the hackathon MVP so that:
- frontend logic stays simple,
- refresh/recovery is easy,
- the frontend does not need to merge partial state.

The backend may store it once and resend it. It does **not** need to recompute it every turn.

---

## 1.5 Definition of `recommended_tab`

```ts
type RecommendedTab = "saju_report" | "counseling_board";
```

`recommended_tab` tells the frontend which tab should be foregrounded after the latest backend response.

Examples:
- After `POST /reading/start` → `"saju_report"`
- After the first follow-up counseling turn → `"counseling_board"`

The frontend may still allow the user to manually switch tabs.

---

## 1.6 Definition of `active_reading`

`active_reading` is the **current focus of the counseling conversation**, not merely the latest assistant message.

Examples:
- User says “I see” after a compatibility result → keep `compatibility_result` active.
- User switches topic to career → switch active reading to `fortune_flow`.

This prevents the Counseling Board from changing too frequently and feeling noisy.

---

# 2. API endpoints

## Required endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/reading/start` | Submit intake form, create session, generate initial full reading and report |
| `POST` | `/chat` | Send a follow-up counseling message and receive the latest board state (JSON) |
| `POST` | `/chat/stream` | Same as `/chat` but response delivered as Server-Sent Events (SSE) |
| `POST` | `/session/reset` | Reset a session |
| `POST` | `/demo/load` | Load seeded demo scenarios |
| `GET` | `/health` | Health check |

## Optional endpoint

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/session/{session_id}` | Fetch current session state for debugging/development |

---

# 3. `POST /reading/start`

## 3.1 Purpose

Starts a new reading from the fixed intake form.

This endpoint:
1. receives the user's basic birth information,
2. creates or initializes the session,
3. computes base saju data,
4. generates the full first interpretation,
5. builds the `saju_report`,
6. builds the initial `counseling_board`,
7. recommends the `saju_report` tab.

---

## 3.2 Request

```json
{
  "session_id": "demo-session-001",
  "display_name": "Yoonhye",
  "birth_date": "1998-04-21",
  "birth_time": "14:30",
  "gender": "female"
}
```

### Request type

```ts
type StartReadingRequest = {
  session_id: string;
  display_name?: string;
  birth_date: string;      // ISO date: YYYY-MM-DD
  birth_time?: string;     // HH:MM, optional
  gender?: "female" | "male" | "other" | "prefer_not_to_say";
};
```

---

## 3.3 Response

```ts
type InitialReadingResponse = {
  session_id: string;
  assistant_message: string;
  current_stage: "initial_report";
  recommended_tab: "saju_report";
  thinking_state: string | null;
  saju_report: SajuReport;
  counseling_board: CounselingBoard;
  ui_event: UIEvent;
  agent_trace?: AgentTraceStep[];
};
```

---

## 3.4 Example response

```json
{
  "session_id": "demo-session-001",
  "assistant_message": "Your fire energy is quite alive. When your heart moves, you tend to act before you overthink. At the same time, with less water in the chart, feelings can linger inside longer than people realize. In relationships, you may seem open and direct on the surface, while still watching the other person’s response very carefully underneath.",
  "current_stage": "initial_report",
  "recommended_tab": "saju_report",
  "thinking_state": null,
  "saju_report": {
    "id": "saju_report_user_001",
    "title": "Yoonhye’s Full Saju Report",
    "overall_summary": "A chart with strong momentum and deep emotional sensitivity.",
    "elements": {
      "wood": 2,
      "fire": 4,
      "earth": 1,
      "metal": 2,
      "water": 1
    },
    "dominant_elements": ["fire"],
    "lacking_elements": ["earth", "water"],
    "keywords": ["direct", "deep-feeling", "change-oriented"],
    "personality": {
      "title": "Personality",
      "summary": "When your heart moves, you tend to act before you overthink. At the same time, you often hold onto thoughts longer than others realize."
    },
    "relationship_style": {
      "title": "Relationship Style",
      "summary": "You may appear open and direct on the surface, while quietly watching the other person’s response very carefully underneath."
    },
    "career_style": {
      "title": "Career Style",
      "summary": "You tend to thrive more in environments with movement, growth, and room to shape things than in static settings."
    },
    "emotional_pattern": {
      "title": "Emotional Pattern",
      "summary": "You can look composed from the outside, yet once something settles in your heart, it may stay with you for quite a while."
    },
    "strengths": ["drive", "resilience", "intuitive judgment"],
    "cautions": ["emotional overheating", "holding things in too long", "late-arriving fatigue after decisions"],
    "one_line_verdict": "You become strongest when you learn to pause without losing your fire.",
    "chart_identity": {
      "day_pillar": {
        "ganji_hanja": "丙午",
        "ganji_reading_en": "Bing Wu",
        "stem_hanja": "丙",
        "branch_hanja": "午",
        "english_name": "Red Horse",
        "animal": "horse",
        "animal_label": "Horse",
        "color": "red"
      },
      "day_master": {
        "stem_hanja": "丙",
        "stem_roman": "Bing",
        "element": "fire",
        "element_label": "Fire",
        "polarity": "yang",
        "english_name": "Yang Fire",
        "display_label": "丙 · Yang Fire"
      },
      "visual_tokens": {
        "theme": "fire",
        "accent": "red",
        "animal": "horse"
      }
    },
    "chart_digest": {
      "pillars_hanja": {
        "year": "戊寅",
        "month": "甲子",
        "day": "丙午",
        "hour": "壬辰"
      },
      "day_stem_label_en": "Byeong Fire",
      "day_pillar_reading_en": "Bing Wu",
      "day_branch_animal_label": "Horse",
      "pillar_lines_en": [
        "Year pillar 戊寅 — stem Wu (Mu Earth), branch Yin (Tiger)",
        "Month pillar 甲子 — stem Jia (Gap Wood), branch Zi (Rat)",
        "Day pillar 丙午 — stem Bing (Byeong Fire), branch Wu (Horse)",
        "Hour pillar 壬辰 — stem Ren (Im Water), branch Chen (Dragon)"
      ],
      "day_master_strength_en": "Strong (index +3: support vs drain balance)",
      "signals_gloss_en": {
        "personality": [
          "Strong drive—you tend to initiate and push forward decisively.",
          "Goal-setting, learning, and expansion energies come online easily."
        ],
        "career": [
          "Strong suit in running procedures, refinement, and delivery."
        ]
      }
    }
  },
  "counseling_board": {
    "profile_summary": {
      "id": "profile_user_001",
      "title": "Yoonhye’s Base Flow",
      "one_line_summary": "Strong momentum paired with deep emotional sensitivity.",
      "elements": {
        "wood": 2,
        "fire": 4,
        "earth": 1,
        "metal": 2,
        "water": 1
      },
      "dominant_elements": ["fire"],
      "lacking_elements": ["earth", "water"],
      "keywords": ["direct", "deep-feeling", "change-oriented"],
      "chart_identity_summary": {
        "day_pillar_hanja": "丙午",
        "day_pillar_label": "Red Horse",
        "day_master_label": "Yang Fire",
        "display_label": "丙午 · Red Horse · Yang Fire",
        "theme": "fire",
        "accent": "red",
        "animal": "horse"
      }
    },
    "active_reading": null,
    "insight_summaries": [],
    "history": []
  },
  "ui_event": {
    "type": "report_initialized",
    "target_id": "saju_report_user_001"
  },
  "agent_trace": [
    {
      "step": "tool_call",
      "label": "Computed base saju profile",
      "tool_name": "analyze_base_saju",
      "status": "completed"
    },
    {
      "step": "view_model",
      "label": "Built full saju report",
      "status": "completed"
    }
  ]
}
```

---

# 4. `POST /chat`

## 4.1 Purpose

Handles all **follow-up counseling** after the initial full reading has already been created.

This endpoint:
1. receives the user's new message,
2. loads the existing session state,
3. interprets the user's concern,
4. decides whether a tool is needed,
5. runs the relevant tool if appropriate,
6. updates the `counseling_board`,
7. returns the latest full right-panel snapshot.

---

## 4.2 Request

일반 메시지:

```json
{
  "session_id": "demo-session-001",
  "message": "I’m thinking of confessing soon."
}
```

궁합 팝업 제출 시 (`message` 없이 `partner`만 전송 가능):

```json
{
  "session_id": "demo-session-001",
  "message": "",
  "partner": {
    "display_name": "Minsoo",
    "birth_date": "1996-08-15",
    "birth_time": null,
    "gender": "male"
  }
}
```

### Request type

```ts
type GenderType = "female" | "male" | "other" | "prefer_not_to_say";

type PartnerCompatibilityPayload = {
  display_name?: string | null;   // 최대 80자; 빈 문자열은 null 처리
  birth_date: string;             // ISO date: YYYY-MM-DD (필수)
  birth_time?: string | null;     // HH:MM, optional
  gender?: GenderType | null;
};

type ChatRequest = {
  session_id: string;             // 1–120자
  message?: string;               // 최대 4000자; partner 없을 때 필수
  partner?: PartnerCompatibilityPayload | null;  // 궁합 팝업 제출 결과
};
```

> **규칙**: `message`와 `partner` 중 최소 하나는 반드시 있어야 합니다.  
> `partner`만 있을 경우 백엔드가 메시지를 `"(상대 사주 정보 폼 제출)"`로 처리합니다.

---

## 4.3 Response

```ts
type ChatResponse = {
  session_id: string;
  assistant_message: string;
  current_stage: CurrentStage;
  recommended_tab: RecommendedTab;
  thinking_state: string | null;
  saju_report: SajuReport;
  counseling_board: CounselingBoard;
  ui_event: UIEvent | null;
  agent_trace?: AgentTraceStep[];
  partner_intake_requested: boolean;  // true이면 프론트가 궁합 정보 입력 팝업을 표시해야 함
};
```

---

## 4.4 Example response

```json
{
  "session_id": "demo-session-001",
  "assistant_message": "Then let’s look at when your words are most likely to land gently. The flow around May 14 looks the softest for opening your heart.",
  "current_stage": "open_counseling",
  "recommended_tab": "counseling_board",
  "thinking_state": null,
  "saju_report": {
    "id": "saju_report_user_001",
    "title": "Yoonhye’s Full Saju Report",
    "overall_summary": "A chart with strong momentum and deep emotional sensitivity.",
    "elements": {
      "wood": 2,
      "fire": 4,
      "earth": 1,
      "metal": 2,
      "water": 1
    },
    "dominant_elements": ["fire"],
    "lacking_elements": ["earth", "water"],
    "keywords": ["direct", "deep-feeling", "change-oriented"],
    "personality": {
      "title": "Personality",
      "summary": "When your heart moves, you tend to act before you overthink. At the same time, you often hold onto thoughts longer than others realize."
    },
    "relationship_style": {
      "title": "Relationship Style",
      "summary": "You may appear open and direct on the surface, while quietly watching the other person’s response very carefully underneath."
    },
    "career_style": {
      "title": "Career Style",
      "summary": "You tend to thrive more in environments with movement, growth, and room to shape things than in static settings."
    },
    "emotional_pattern": {
      "title": "Emotional Pattern",
      "summary": "You can look composed from the outside, yet once something settles in your heart, it may stay with you for quite a while."
    },
    "strengths": ["drive", "resilience", "intuitive judgment"],
    "cautions": ["emotional overheating", "holding things in too long", "late-arriving fatigue after decisions"],
    "one_line_verdict": "You become strongest when you learn to pause without losing your fire.",
    "chart_identity": {
      "day_pillar": {
        "ganji_hanja": "丙午",
        "ganji_reading_en": "Bing Wu",
        "stem_hanja": "丙",
        "branch_hanja": "午",
        "english_name": "Red Horse",
        "animal": "horse",
        "animal_label": "Horse",
        "color": "red"
      },
      "day_master": {
        "stem_hanja": "丙",
        "stem_roman": "Bing",
        "element": "fire",
        "element_label": "Fire",
        "polarity": "yang",
        "english_name": "Yang Fire",
        "display_label": "丙 · Yang Fire"
      },
      "visual_tokens": {
        "theme": "fire",
        "accent": "red",
        "animal": "horse"
      }
    },
    "chart_digest": {
      "pillars_hanja": {
        "year": "戊寅",
        "month": "甲子",
        "day": "丙午",
        "hour": "壬辰"
      },
      "day_stem_label_en": "Byeong Fire",
      "day_pillar_reading_en": "Bing Wu",
      "day_branch_animal_label": "Horse",
      "pillar_lines_en": [
        "Year pillar 戊寅 — stem Wu (Mu Earth), branch Yin (Tiger)",
        "Month pillar 甲子 — stem Jia (Gap Wood), branch Zi (Rat)",
        "Day pillar 丙午 — stem Bing (Byeong Fire), branch Wu (Horse)",
        "Hour pillar 壬辰 — stem Ren (Im Water), branch Chen (Dragon)"
      ],
      "day_master_strength_en": "Strong (index +3: support vs drain balance)",
      "signals_gloss_en": {
        "personality": [
          "Strong drive—you tend to initiate and push forward decisively.",
          "Goal-setting, learning, and expansion energies come online easily."
        ],
        "career": [
          "Strong suit in running procedures, refinement, and delivery."
        ]
      }
    }
  },
  "counseling_board": {
    "profile_summary": {
      "id": "profile_user_001",
      "title": "Yoonhye’s Base Flow",
      "one_line_summary": "Strong momentum paired with deep emotional sensitivity.",
      "elements": {
        "wood": 2,
        "fire": 4,
        "earth": 1,
        "metal": 2,
        "water": 1
      },
      "dominant_elements": ["fire"],
      "lacking_elements": ["earth", "water"],
      "keywords": ["direct", "deep-feeling", "change-oriented"],
      "chart_identity_summary": {
        "day_pillar_hanja": "丙午",
        "day_pillar_label": "Red Horse",
        "day_master_label": "Yang Fire",
        "display_label": "丙午 · Red Horse · Yang Fire",
        "theme": "fire",
        "accent": "red",
        "animal": "horse"
      }
    },
    "active_reading": {
      "id": "timing_love_confession",
      "semantic_key": "timing:love:confession",
      "template": "timing_recommendation",
      "title": "Best Time to Confess",
      "domain": "love",
      "action_type": "confession",
      "headline_keyword": "Forward Momentum",
      "one_line_summary": "The middle of the week opens most gently for expressing your feelings.",
      "recommended_window": {
        "label": "Strongest Window",
        "date_range": "Around May 14",
        "reason": "Your words are more likely to land softly, and the other person may be more open to receiving them."
      },
      "timeline": [
        {
          "label": "Mon–Tue",
          "keyword": "Observe",
          "tone": "muted"
        },
        {
          "label": "Wed–Thu",
          "keyword": "Talk",
          "tone": "highlight"
        },
        {
          "label": "Fri",
          "keyword": "Move Forward",
          "tone": "strong"
        }
      ],
      "caution_window": {
        "label": "Use Caution",
        "date_range": "Around May 12",
        "reason": "You may feel more hurried than the situation actually requires."
      }
    },
    "insight_summaries": [
      {
        "id": "insight_compatibility_user_minsoo",
        "semantic_key": "compatibility:user:minsoo",
        "label": "Strong pull with Minsoo",
        "type": "compatibility_result",
        "short_summary": "82 points · pace needs care"
      },
      {
        "id": "insight_timing_love_confession",
        "semantic_key": "timing:love:confession",
        "label": "Strong confession window",
        "type": "timing_recommendation",
        "short_summary": "Around May 14"
      }
    ],
    "history": [
      {
        "id": "compatibility_user_minsoo",
        "semantic_key": "compatibility:user:minsoo",
        "template": "compatibility_result",
        "title": "Relationship Flow with Minsoo",
        "summary": "82 points · strong attraction",
        "created_at": "2026-05-09T19:20:00Z",
        "updated_at": "2026-05-09T19:20:00Z"
      },
      {
        "id": "timing_love_confession",
        "semantic_key": "timing:love:confession",
        "template": "timing_recommendation",
        "title": "Best Time to Confess",
        "summary": "The flow is softest around May 14",
        "created_at": "2026-05-09T19:25:00Z",
        "updated_at": "2026-05-09T19:25:00Z"
      }
    ]
  },
  "ui_event": {
    "type": "template_changed",
    "from_template": "compatibility_result",
    "to_template": "timing_recommendation",
    "target_id": "timing_love_confession"
  },
  "agent_trace": [
    {
      "step": "tool_call",
      "label": "Analyzed favorable timing for confession",
      "tool_name": "analyze_favorable_timing",
      "status": "completed"
    }
  ]
}
```

---

---

## 4.5 궁합 수집 플로우 (Compatibility Intake Flow)

백엔드가 궁합 계산을 위해 상대방 정보가 필요하다고 판단하면 다음과 같이 동작합니다.

### 흐름 요약

```text
1. 사용자: "민수랑 궁합 봐줘" 등 궁합 관련 메시지 전송

2. 백엔드 → ChatResponse:
   - current_stage: "collecting_compatibility_info"
   - counseling_board.active_reading.template: "compatibility_pending"
   - partner_intake_requested: true   ← 프론트가 팝업을 표시해야 하는 신호

3. 프론트:
   - partner_intake_requested === true 이면 상대방 생년월일 입력 팝업 표시

4. 사용자: 팝업에서 상대 정보 입력 후 제출

5. 프론트 → POST /chat (또는 /chat/stream):
   {
     "session_id": "...",
     "message": "",       ← 빈 메시지도 허용
     "partner": {
       "display_name": "민수",
       "birth_date": "1996-08-15",
       "birth_time": null,
       "gender": "male"
     }
   }

6. 백엔드:
   - 궁합 계산 수행
   - current_stage: "open_counseling"
   - counseling_board.active_reading.template: "compatibility_result"
   - partner_intake_requested: false
```

### 팝업 표시 규칙

| 조건 | 프론트 동작 |
|---|---|
| `partner_intake_requested === true` | 상대방 정보 입력 팝업 열기 |
| `partner_intake_requested === false` | 팝업 없음, 일반 응답 처리 |

> **중요**: 팝업 결과는 반드시 `ChatRequest.partner` 필드로 전송해야 합니다.  
> 텍스트 메시지로 생년월일을 입력해도 백엔드가 파싱을 시도하지만, `partner` 구조화 필드 사용이 권장됩니다.

---

---

# 4.6 `POST /chat/stream` (SSE 스트리밍)

## 4.6.1 Purpose

`POST /chat`와 동일한 입력을 받되, 응답을 **Server-Sent Events(SSE)** 스트림으로 분할하여 전송합니다.  
LLM 답변을 토큰 단위로 점진적으로 표시하는 채팅 UI에 적합합니다.

---

## 4.6.2 Request

`POST /chat`와 동일한 `ChatRequest` JSON 사용.

---

## 4.6.3 Response — SSE 이벤트 흐름

`Content-Type: text/event-stream`으로 응답합니다.

```text
event: prelude
data: { ...PreludePayload }

event: delta
data: { "text": "..." }

event: delta
data: { "text": "..." }

...

event: complete
data: { ...ChatResponse }
```

---

## 4.6.4 이벤트 타입별 Payload

| 이벤트 | 타이밍 | Payload |
|---|---|---|
| `prelude` | LLM 스트림 시작 전; 도구 실행 직후 | `PreludePayload` (아래 참조) |
| `delta` | LLM 토큰마다 1회 | `{ text: string }` |
| `complete` | 스트림 종료 후 상태 저장 완료 | `ChatResponse` 전체 (JSON) |

### `PreludePayload` 타입

```ts
type PreludePayload = {
  session_id: string;
  current_stage: CurrentStage;
  recommended_tab: RecommendedTab;     // 항상 "counseling_board"
  partner_intake_requested: boolean;
  saju_report: SajuReport;
  counseling_board: CounselingBoard;
  ui_event: UIEvent | null;
  tool_agent_trace: AgentTraceStep[];  // 도구 실행 trace (LLM turn 제외)
};
```

> `prelude` 이벤트는 도구 계산 결과(보드 갱신, ui_event)를 LLM 응답 전에 미리 화면에 반영하기 위한 것입니다.  
> `complete` 이벤트의 `ChatResponse`에는 LLM trace까지 포함된 최종 `agent_trace`가 담깁니다.

---

## 4.6.5 SSE 처리 예시 (TypeScript)

```ts
const res = await fetch("/chat/stream", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ session_id, message }),
});

const reader = res.body!.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });

  const lines = buffer.split("\n");
  buffer = lines.pop()!;

  let eventName = "";
  for (const line of lines) {
    if (line.startsWith("event: ")) {
      eventName = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      const payload = JSON.parse(line.slice(6));
      if (eventName === "prelude") {
        applyPrelude(payload);   // 보드/탭 즉시 반영
      } else if (eventName === "delta") {
        appendText(payload.text); // 토큰 스트리밍
      } else if (eventName === "complete") {
        finalizeResponse(payload); // 전체 응답 확정
      }
    }
  }
}
```

---

# 5. Shared types

## 5.1 `CurrentStage`

```ts
type CurrentStage =
  | "initial_report"
  | "open_counseling"
  | "collecting_compatibility_info"
  | "collecting_tool_inputs";
```

> Note: `onboarding` is no longer part of chat state because intake happens through the fixed form before the reading starts.

---

## 5.2 `RecommendedTab`

```ts
type RecommendedTab = "saju_report" | "counseling_board";
```

---

## 5.3 `CounselingBoard`

```ts
type CounselingBoard = {
  profile_summary: ProfileSummary | null;
  active_reading: ActiveReading | null;
  insight_summaries: InsightSummary[];
  history: HistoryItem[];
};
```

---

## 5.4 `AgentTraceStep`

개발/디버깅용으로 각 응답에 포함되는 처리 단계 기록입니다.

```ts
type AgentTraceStep = {
  step:
    | "tool_call"      // 사주 계산 / 운세 도구 실행
    | "view_model"     // UI 뷰 모델 빌드
    | "graph_node"     // 내부 파이프라인 노드
    | "routing"        // 인텐트 라우팅 결정
    | "llm_call";      // LLM 호출 (counselor reply)
  label: string;
  tool_name?: string | null;
  status: "pending" | "completed" | "skipped" | "failed";
};
```

---

# 6. `saju_report`

## 6.1 Purpose

The full static report dashboard shown immediately after the intake form is submitted and available later as a separate tab.

---

## 6.2 Type

```ts
type ElementKey = "wood" | "fire" | "earth" | "metal" | "water";

type DayPillarIdentity = {
  ganji_hanja: string;
  ganji_reading_en: string; // Romanized stem + branch e.g. "Xin Mao", "Bing Wu"
  stem_hanja: string;
  branch_hanja: string;
  english_name: string; // symbolic English, e.g. "White Rabbit" (stem phase color + branch animal)
  animal: string;
  animal_label: string;
  color: string;
};

type DayMasterIdentity = {
  stem_hanja: string;
  stem_roman: string; // e.g. "Xin", "Bing"
  element: ElementKey;
  element_label: string;
  polarity: "yin" | "yang";
  english_name: string; // e.g. "Yin Metal"
  display_label: string;
};

type ChartVisualTokens = {
  theme: ElementKey;
  accent: string;
  animal: string;
};

type ChartIdentity = {
  day_pillar: DayPillarIdentity;
  day_master: DayMasterIdentity;
  visual_tokens: ChartVisualTokens;
};

type TraditionalChartDigest = {
  pillars_hanja: Record<string, string>; // Hanja pillar pairs e.g. year "戊寅"
  day_stem_label_en: string; // English stem-element label e.g. "Sin Metal"
  day_pillar_reading_en: string; // Romanized day pillar pair e.g. "Xin Mao"
  day_branch_animal_label: string; // e.g. "Rabbit"
  pillar_lines_en: string[]; // Year / Month / Day / Hour one-liners (English prose; may cite Hanja)
  day_master_strength_en?: string; // Plain English strength note or ""
  signals_gloss_en: Partial<Record<string, string[]>>; // Rule hits → English one-line gloss
};

type SajuReport = {
  id: string;
  title: string;
  overall_summary: string;
  elements: {
    wood: number;
    fire: number;
    earth: number;
    metal: number;
    water: number;
  };
  dominant_elements: string[];
  lacking_elements: string[];
  keywords: string[];
  personality: ReportSection;
  relationship_style: ReportSection;
  career_style: ReportSection;
  emotional_pattern: ReportSection;
  strengths: string[];
  cautions: string[];
  one_line_verdict: string;
  chart_identity?: ChartIdentity | null; // English-ready labels for visualization (recommended)
  chart_digest?: TraditionalChartDigest | null; // 없음·null 과 구버전 응답 호환
};

type ReportSection = {
  title: string;
  summary: string;
};
```

---

## 6.3 Full Saju Report UI contents

The frontend should be able to render:

1. Five-element balance
2. Dominant elements
3. Lacking elements
4. Core keywords
5. Overall summary
6. Personality
7. Relationship style
8. Career style
9. Emotional pattern
10. Strengths
11. Cautions
12. One-line verdict
13. **`chart_identity` (when present)** — day pillar + day master + theme tokens (**English labels**); primary source for visuals
14. **`chart_digest` (when present)** — extended English explanations plus Hanja keys (optional)

---

# 7. `counseling_board.profile_summary`

## 7.1 Purpose

A compact summary of the full report, shown at the top of the Counseling Board.

This is **not** a second full report.

---

## 7.2 Type

```ts
type ChartIdentitySummary = {
  day_pillar_hanja: string;
  day_pillar_label: string;
  day_master_label: string;
  display_label: string;
  theme: ElementKey;
  accent: string;
  animal: string;
};

type ProfileSummary = {
  id: string;
  title: string;
  one_line_summary: string;
  elements: {
    wood: number;
    fire: number;
    earth: number;
    metal: number;
    water: number;
  };
  dominant_elements: string[];
  lacking_elements: string[];
  keywords: string[];
  chart_identity_summary?: ChartIdentitySummary | null; // absent in older mock payloads
};
```

---

# 8. `counseling_board.active_reading`

## 8.1 Active-reading template enum

```ts
type ActiveTemplate =
  | "general_reading"
  | "compatibility_pending"
  | "compatibility_result"
  | "fortune_flow"
  | "timing_recommendation";
```

---

## 8.2 `general_reading`

Used for:
- general counseling,
- ambiguous concerns,
- clarification states,
- moments when no specialized visual reading is active.

```ts
type GeneralReadingTemplate = {
  id: string;
  semantic_key: string;
  template: "general_reading";
  title: string;
  headline?: string;
  body: string;
  highlighted_traits?: string[];
  prompt_to_user?: string;
};
```

---

## 8.3 `compatibility_pending`

Used when:
- the AI has entered a compatibility flow,
- counterpart information is still missing,
- or compatibility is currently being processed.

```ts
type CompatibilityPendingTemplate = {
  id: string;
  semantic_key: string;
  template: "compatibility_pending";
  title: string;
  left_person: {
    name: string;
  };
  right_person?: {
    name?: string;
  };
  status_message: string;
  missing_fields?: string[];
};
```

---

## 8.4 `compatibility_result`

```ts
type CompatibilityResultTemplate = {
  id: string;
  semantic_key: string;
  template: "compatibility_result";
  title: string;
  score: number;
  label: string;
  people: Array<{
    name: string;
    dominant_element?: string;
  }>;
  connection: {
    type: "supportive" | "balanced" | "tense";
    label: string;
  };
  strengths: string[];
  friction_points: string[];
  one_line_advice: string;
};
```

---

## 8.5 `fortune_flow`

Used when showing the current flow of a life domain.

Examples:
- “How does my career flow look this week?”
- “How is my love flow today?”
- “What is happening with money lately?”

```ts
type FortuneFlowTemplate = {
  id: string;
  semantic_key: string;
  template: "fortune_flow";
  title: string;
  domain: "love" | "career" | "money" | "relationships" | "health" | "overall";
  period: "today" | "this_week" | "this_month" | "current_phase";
  headline_keyword: string;
  one_line_summary: string;
  segments: Array<{
    label: string;
    keyword: string;
    tone?: "muted" | "soft" | "highlight" | "strong";
  }>;
  recommended_action?: string;
};
```

---

## 8.6 `timing_recommendation`

Used when recommending the best time for a specific action.

Examples:
- “When should I confess?”
- “When would be a good time to change jobs?”
- “When should I have an important conversation?”

```ts
type TimingRecommendationTemplate = {
  id: string;
  semantic_key: string;
  template: "timing_recommendation";
  title: string;
  domain: "love" | "career" | "money" | "relationships" | "health" | "general";
  action_type: string;
  headline_keyword: string;
  one_line_summary: string;
  recommended_window: {
    label: string;
    date_range: string;
    reason: string;
  };
  timeline?: Array<{
    label: string;
    keyword: string;
    tone?: "muted" | "soft" | "highlight" | "strong";
  }>;
  caution_window?: {
    label: string;
    date_range: string;
    reason: string;
  };
};
```

---

# 9. `insight_summaries`

## 9.1 Purpose

Compact accumulated insights shown in the lower section of the Counseling Board.

---

## 9.2 Type

```ts
type InsightSummary = {
  id: string;
  semantic_key: string;
  label: string;
  type:
    | "general_reading"
    | "compatibility_result"
    | "fortune_flow"
    | "timing_recommendation";
  short_summary: string;
};
```

---

# 10. `history`

## 10.1 Purpose

Summary data for a past-readings drawer or modal.

---

## 10.2 Type

```ts
type HistoryItem = {
  id: string;
  semantic_key: string;
  template: ActiveTemplate;
  title: string;
  summary: string;
  created_at: string;
  updated_at: string;
};
```

---

# 11. `semantic_key` and upsert rule

## 11.1 Purpose

Used by the backend to avoid duplicate counseling readings and update existing ones when the same semantic reading is revisited.

---

## 11.2 Examples

```text
compatibility:user:minsoo
fortune_flow:career:this_week
fortune_flow:love:today
timing:love:confession
timing:career:job_change
```

---

## 11.3 Upsert flow

```text
New tool result
   ↓
Generate semantic_key
   ↓
Does a reading with the same semantic_key already exist?
   ├── Yes → update existing reading
   └── No  → create new reading
   ↓
Rebuild full counseling_board snapshot
```

---

# 12. `ui_event`

## 12.1 Purpose

Animation hint only.

Rendering must rely on `saju_report` and `counseling_board`, not on `ui_event`.

---

## 12.2 Type

```ts
type UIEvent =
  | {
      type: "report_initialized";
      target_id: string;
    }
  | {
      type: "tab_recommended";
      recommended_tab: RecommendedTab;
    }
  | {
      type: "profile_initialized";
      target_id: string;
    }
  | {
      type: "template_changed";
      from_template: ActiveTemplate | null;
      to_template: ActiveTemplate;
      target_id: string;
    }
  | {
      type: "active_reading_updated";
      target_id: string;
      changed_fields: string[];
    }
  | {
      type: "insight_added";
      target_id: string;
    }
  | {
      type: "reading_completed";
      target_id: string;
    }
  | {
      type: "reading_updated";
      target_id: string;
    }
  | null;
```

---

# 13. Frontend rendering rules

## 13.1 Page flow

```text
Before reading starts:
- show fixed intake form

After POST /reading/start:
- show chat area with assistant's first full interpretation
- show Full Saju Report tab first

After the user begins follow-up counseling:
- chat continues
- recommended_tab usually becomes counseling_board
- Full Saju Report remains available as a separate tab
```

---

## 13.2 Right-panel layout

```text
[Tabs]
  ├── Full Saju Report
  │    └── saju_report
  └── Counseling Board
       ├── profile_summary
       ├── active_reading
       ├── insight_summaries
       └── history
```

---

## 13.3 Active template switch

```tsx
switch (active_reading?.template) {
  case "general_reading":
    return <GeneralReadingView data={active_reading} />;
  case "compatibility_pending":
    return <CompatibilityPendingView data={active_reading} />;
  case "compatibility_result":
    return <CompatibilityResultView data={active_reading} />;
  case "fortune_flow":
    return <FortuneFlowView data={active_reading} />;
  case "timing_recommendation":
    return <TimingRecommendationView data={active_reading} />;
  default:
    return <EmptyStateView />;
}
```

---

## 13.4 Suggested animation behavior

| Event / transition | Suggested UI behavior |
|---|---|
| `report_initialized` | Reveal Full Saju Report dashboard with staged section animation |
| `tab_recommended: saju_report` | Foreground Full Saju Report if appropriate |
| `tab_recommended: counseling_board` | Foreground Counseling Board if appropriate |
| `profile_initialized` | Fade/slide in compact base summary |
| `template_changed` | Crossfade or slide between active templates |
| `reading_completed` | Highlight key result; score count-up; date glow |
| `insight_added` | Soft pop-in for new insight chip |
| `active_reading_updated` | Crossfade changed fields only |

---

# 14. Demo and mock data

## 14.1 Required mock response files

실제 저장 위치: `docs/mocks/`.

```text
docs/mocks/
  01_initial_reading_response.json
  02_counseling_start_general_reading.json
  03_compatibility_pending.json
  04_compatibility_result.json
  05_timing_recommendation_love.json
  06_fortune_flow_career_week.json
  07_timing_recommendation_career.json
```

---

## 14.2 What each mock represents

| File | State |
|---|---|
| `01_initial_reading_response.json` | Response from `/reading/start`; full report generated and report tab shown first |
| `02_counseling_start_general_reading.json` | First follow-up counseling turn; Counseling Board becomes primary |
| `03_compatibility_pending.json` | Compatibility flow entered, waiting for counterpart info |
| `04_compatibility_result.json` | Compatibility result completed |
| `05_timing_recommendation_love.json` | Confession timing recommendation |
| `06_fortune_flow_career_week.json` | Weekly career flow |
| `07_timing_recommendation_career.json` | Best timing for job change |

`01_initial_reading_response.json` includes **`chart_identity`** (inside `saju_report`), **`chart_identity_summary`** (inside `counseling_board.profile_summary`), and an English **`chart_digest`** (`pillar_lines_en`, `signals_gloss_en`, …). Follow-up mocks `02`–`07` may omit these optional fields for brevity; live API responses should populate them consistently.

---

## 14.3 Suggested demo scenarios

```ts
type DemoScenario =
  | "fresh_start"
  | "after_initial_report"
  | "romance_demo"
  | "career_demo";
```

---

# 15. Other endpoints

## 15.1 `POST /session/reset`

### Request

```json
{
  "session_id": "demo-session-001"
}
```

### Response

```json
{
  "session_id": "demo-session-001",
  "reset": true
}
```

---

## 15.2 `POST /demo/load`

### Request

```json
{
  "session_id": "demo-session-001",
  "scenario": "romance_demo"
}
```

---

## 15.3 `GET /health`

### Response

```json
{
  "status": "ok"
}
```

---

# 16. Contract items that must be frozen early

## Freeze early

1. `POST /reading/start` request and response shape
2. `POST /chat` request and response shape
3. `saju_report` schema
4. `counseling_board` schema
5. `recommended_tab` enum
6. `active_reading.template` enum
7. Required fields for each active template
8. `insight_summaries` schema
9. `history` schema
10. `semantic_key` convention
11. `ui_event` enum

## Can evolve later

1. Copy text
2. Optional fields
3. Number of timeline segments
4. Exact visual design
5. `agent_trace` details
6. Additional report sections if needed

---

# 17. Final summary

```text
The product now has three phases:

1. Fixed intake form
2. Full Saju Report
3. Conversational Counseling

The right panel has two tab-level view models:

1. saju_report
   - full static dashboard
   - shown first after POST /reading/start

2. counseling_board
   - compact base summary + live counseling state
   - used for all follow-up chat turns

Backend decides meaning.
Frontend decides presentation.

Backend returns the full latest right-panel snapshot after each response.
Frontend renders the latest snapshot and uses recommended_tab + ui_event to animate it beautifully.
```

