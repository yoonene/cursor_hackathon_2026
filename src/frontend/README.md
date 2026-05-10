# AI Saju Counselor — Frontend

> A conversational AI saju counselor. The user receives a full reading first, then continues the session naturally through chat.

---

## Design Direction

**Mood**: Warm, grounded, approachable — a space where anyone feels comfortable opening up.

**Color palette**: Sage green / forest tones

| Token | Value | Usage |
|-------|-------|-------|
| `sage-50` | `#f4f7f4` | Page background |
| `sage-100` | `#e4ece4` | Card backgrounds, subtle fills |
| `sage-200` | `#c8d9c8` | Borders, dividers |
| `sage-400` | `#7fa67f` | Secondary text, muted badges |
| `sage-600` | `#4a7c59` | Primary interactive elements |
| `sage-800` | `#2d5a3d` | Headings, strong accents |
| `sage-900` | `#1a3a27` | Dark text, high contrast |
| `warm-white` | `#fafaf8` | Chat bubble backgrounds |
| `mist` | `#eef2ee` | Right panel background |

**Typography**: Clean sans-serif (Inter). Gentle spacing, no harsh edges.

**Tone**: Still, trustworthy, and softly alive — like sitting across from a counselor in a quiet room.

---

## Tech Stack

| Category | Choice | Reason |
|----------|--------|--------|
| Language | **TypeScript** | API contract is written in TypeScript types — full type safety from day one |
| Framework | **React 18** | Component-based; 5 active-reading templates map cleanly to components |
| Build tool | **Vite** | Fast dev server, minimal config |
| Styling | **Tailwind CSS** | Rapid UI with custom sage palette via config |
| Animation | **Framer Motion** | Crossfade template switches, slide-in cards, count-up scores |
| State | **Zustand** | Lightweight global store for session, phase, saju_report, counseling_board |
| Data fetching | **TanStack Query** | Handles loading/error states; easy to swap mock ↔ real API |
| Charts | **Recharts** | Five-element radar/bar chart in the Saju Report |
| Utilities | **clsx + tailwind-merge** | Conditional class merging |

---

## Screen Layout

### Phase 1 — Intake Form (full screen)
```
┌────────────────────────────────────┐
│                                    │
│         AI Saju Counselor          │
│                                    │
│  ┌──────────────────────────────┐  │
│  │  Name (optional)             │  │
│  │  Date of birth               │  │
│  │  Time of birth (optional)    │  │
│  │  Gender (optional)           │  │
│  │                              │  │
│  │      [ Begin Reading ]       │  │
│  └──────────────────────────────┘  │
│                                    │
└────────────────────────────────────┘
```

### Phase 2 & 3 — Reading + Counseling (split layout)
```
┌──────────────────────┬─────────────────────────────────┐
│                      │  [ Full Saju Report ] [ Counseling Board ] │
│    Chat Area         ├─────────────────────────────────┤
│                      │                                 │
│  AI message bubble   │  Right Panel                    │
│  User message bubble │  (content switches by tab)      │
│                      │                                 │
│  ──────────────────  │                                 │
│  [ Type a message ]  │                                 │
└──────────────────────┴─────────────────────────────────┘
```

---

## Directory Structure

```
src/frontend/
├── src/
│   ├── api/
│   │   ├── client.ts                  # axios instance, base URL, interceptors
│   │   ├── reading.ts                 # POST /reading/start
│   │   └── chat.ts                    # POST /chat, POST /session/reset
│   │
│   ├── types/
│   │   └── api.ts                     # Full TypeScript types from API contract
│   │
│   ├── store/
│   │   └── sessionStore.ts            # Zustand store
│   │                                  # session_id, phase, saju_report, counseling_board, activeTab
│   │
│   ├── mocks/                         # Static JSON for backend-free development
│   │   ├── 01_initial_reading_response.json
│   │   ├── 02_counseling_start_general_reading.json
│   │   ├── 03_compatibility_pending.json
│   │   ├── 04_compatibility_result.json
│   │   ├── 05_timing_recommendation_love.json
│   │   ├── 06_fortune_flow_career_week.json
│   │   └── 07_timing_recommendation_career.json
│   │
│   ├── components/
│   │   ├── intake/
│   │   │   └── IntakeForm.tsx
│   │   ├── chat/
│   │   │   ├── ChatArea.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   └── ChatInput.tsx
│   │   ├── right-panel/
│   │   │   ├── RightPanel.tsx
│   │   │   ├── TabBar.tsx
│   │   │   ├── saju-report/
│   │   │   │   ├── SajuReportTab.tsx
│   │   │   │   ├── ElementChart.tsx
│   │   │   │   └── ReportSection.tsx
│   │   │   └── counseling-board/
│   │   │       ├── CounselingBoard.tsx
│   │   │       ├── ProfileSummary.tsx
│   │   │       ├── InsightChips.tsx
│   │   │       └── active-reading/
│   │   │           ├── ActiveReading.tsx
│   │   │           ├── GeneralReadingView.tsx
│   │   │           ├── CompatibilityPendingView.tsx
│   │   │           ├── CompatibilityResultView.tsx
│   │   │           ├── FortuneFlowView.tsx
│   │   │           └── TimingRecommendationView.tsx
│   │   └── ui/
│   │       ├── ElementBadge.tsx
│   │       ├── KeywordChip.tsx
│   │       └── LoadingDots.tsx
│   │
│   ├── pages/
│   │   └── MainPage.tsx
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
│
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
└── postcss.config.js
```

---

## App State (Zustand)

```ts
type Phase = "intake" | "reading" | "counseling"

type SessionStore = {
  sessionId: string
  phase: Phase
  messages: ChatMessage[]
  sajuReport: SajuReport | null
  counselingBoard: CounselingBoard | null
  activeTab: "saju_report" | "counseling_board"
  isLoading: boolean

  setReadingResult: (...) => void
  setChatResult: (...) => void
  setActiveTab: (tab) => void
  reset: () => void
}
```

---

## Active Reading Templates

| Template | Trigger | Key visuals |
|----------|---------|-------------|
| `general_reading` | Ambiguous or general concern | Headline + body text |
| `compatibility_pending` | Compatibility flow started, info still missing | Two circular nodes + animated connecting line |
| `compatibility_result` | Compatibility analysis complete | Score count-up, relationship label, strengths/friction |
| `fortune_flow` | Domain flow question (love / career / money) | Timeline segments with tone coloring |
| `timing_recommendation` | Best-timing question | Highlighted best window + caution window |

---

## Getting Started

```bash
cd src/frontend
npm install
npm run dev
```

> Set `VITE_USE_MOCK=true` in `.env.local` to use mock JSON instead of the real API (default: true during development).
