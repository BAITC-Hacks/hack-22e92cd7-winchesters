# InVision U — Solution Architecture

## 1. System Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend (Next.js + React)"]
        LP[Landing Page<br/>/ ]
        APP[Application Form<br/>6-step with sidebar]
        TEACH[Teaching Challenge<br/>/teach]
        DASH[Admissions Dashboard<br/>/dashboard]
    end

    subgraph Backend["Backend (FastAPI)"]
        API[REST API — 16 endpoints]
        subgraph Scoring["Scoring Engine"]
            SE[Signal Extractor<br/>Pure Python]
            BL[Baseline Scorer<br/>Rule-based]
            AI[AI Scorer<br/>Claude Sonnet 4]
            AGG[Score Aggregator<br/>Configurable weights]
        end
        subgraph Detection["AI Detection"]
            LANG[Language Detection<br/>KZ / RU / EN]
            STYL[Statistical Stylometry<br/>7 metrics, no AI]
            QUAL[Qualitative Analysis<br/>Claude Sonnet 4]
            COMB[Combined Score<br/>40/60 blend]
        end
        subgraph Feynman["Feynman Teaching Engine"]
            CHAT[AI Student — Arman<br/>Claude as confused 10-year-old]
            QUIZ[Knowledge Transfer Quiz<br/>3 topic-specific questions]
            FEVAL[Teaching Evaluator<br/>Clarity, Patience, Empathy, Adaptability]
        end
        PII[PII Anonymizer]
        OVR[Committee Override<br/>Human-in-the-Loop]
    end

    subgraph Storage["Data Layer"]
        DB[(candidates.json<br/>15 candidates, 3 languages)]
        CACHE[In-Memory Cache]
    end

    subgraph External["External Services"]
        CLAUDE[Claude API<br/>Sonnet 4]
    end

    LP -->|Start Application| APP
    APP -->|POST /api/candidates| API
    APP -->|After Submit| TEACH
    TEACH -->|Chat + Finish| API
    DASH -->|Score, Rank, Override| API
    API --> SE
    SE --> BL
    SE --> AI
    AI --> PII
    PII -->|anonymized data| CLAUDE
    BL --> AGG
    AI --> AGG
    AGG --> CACHE
    API --> LANG
    LANG --> STYL
    STYL --> QUAL
    QUAL --> COMB
    API --> CHAT
    CHAT --> CLAUDE
    CHAT --> QUIZ
    QUIZ --> FEVAL
    OVR -->|override score| AGG
    API --> DB
    API --> CACHE

    style Frontend fill:#e0e7ff,stroke:#4f46e5
    style Backend fill:#f0fdf4,stroke:#10b981
    style Storage fill:#fef3c7,stroke:#f59e0b
    style External fill:#fce7f3,stroke:#ec4899
```

## 2. Applicant Flow

```mermaid
flowchart LR
    subgraph Apply["Application (6 steps)"]
        S1[Personal Info] --> S2[Education]
        S2 --> S3[Essay & Motivation]
        S3 --> S4[Extracurriculars]
        S4 --> S5[Video Presentation]
        S5 --> S6[Review & Submit]
    end

    subgraph Feynman["Teaching Challenge"]
        F1[Pick Topic] --> F2[Chat with Arman]
        F2 --> F3[Arman Takes Quiz]
        F3 --> F4[Get Teaching Score]
    end

    S6 -->|Submit| F1
    F4 --> DONE[Application Complete]

    style Apply fill:#f0fdf4,stroke:#10b981
    style Feynman fill:#ede9fe,stroke:#7c3aed
```

## 3. Scoring Pipeline (3-Stage)

```mermaid
flowchart LR
    subgraph Stage1["Stage 1: Signal Extraction (Pure Python)"]
        C[Candidate Data] --> EX[extract_signals]
        EX --> AC[Academic Signals]
        EX --> LD[Leadership Signals]
        EX --> GR[Growth Signals<br/>delta = current - starting]
        EX --> CM[Communication Signals]
        EX --> MO[Motivation Signals]
    end

    subgraph Stage2["Stage 2: Dual Scoring"]
        AC & LD & GR & CM & MO --> BAS[Baseline Scorer<br/>Rule-based, instant]
        AC & LD & GR & CM & MO --> AIS[AI Scorer<br/>Claude + raw text]
    end

    subgraph Stage3["Stage 3: Aggregation"]
        BAS --> W[Weighted Sum<br/>Committee-configurable]
        AIS --> W
        W --> REC[Recommend / Consider / Needs Attention]
    end

    style Stage1 fill:#ede9fe,stroke:#7c3aed
    style Stage2 fill:#e0f2fe,stroke:#0284c7
    style Stage3 fill:#f0fdf4,stroke:#16a34a
```

## 4. AI Detection Pipeline

```mermaid
flowchart LR
    subgraph Input
        ESS[Essay Text]
        INT[Interview Transcript]
    end

    subgraph S1["Stage 1: Language Detection + Stylometry"]
        ESS --> DETECT[detect_language<br/>KZ / RU / EN]
        DETECT --> COMP[compute_stylometry]
        INT --> COMP
        COMP --> METRICS[7 Metrics<br/>TTR, sentence variance,<br/>hapax, formality, overlap,<br/>word length, sentence length]
        METRICS --> SS[Statistical Score<br/>Language-specific thresholds]
    end

    subgraph S2["Stage 2: Claude Qualitative"]
        ESS --> CL[Claude Analysis]
        INT --> CL
        SS -.->|metrics as context| CL
        CL --> QS[Qualitative Score]
    end

    subgraph S3["Stage 3: Combined"]
        SS -->|40%| BLEND[Weighted Blend]
        QS -->|60%| BLEND
        BLEND --> FINAL[Authenticity Score + Flags]
    end

    style S1 fill:#fef3c7,stroke:#d97706
    style S2 fill:#e0e7ff,stroke:#4f46e5
    style S3 fill:#f0fdf4,stroke:#16a34a
```

## 5. Feynman Teaching Challenge

```mermaid
flowchart TB
    subgraph Session["Teaching Session"]
        START[Candidate picks topic] --> CHAT[Chat with Arman<br/>Claude as confused 10-year-old]
        CHAT -->|4+ exchanges| FINISH[End Session]
        CHAT -->|Arman intentionally<br/>misunderstands once| TEST[Patience Test]
        TEST --> CHAT
    end

    subgraph Evaluation["3 Claude Calls"]
        FINISH --> Q[Quiz Arman<br/>3 topic questions]
        Q --> SCORE[Evaluate Conversation]
        SCORE --> RESULT[Scores: Clarity, Patience,<br/>Empathy, Adaptability,<br/>Quiz Transfer, Overall]
    end

    style Session fill:#ede9fe,stroke:#7c3aed
    style Evaluation fill:#f0fdf4,stroke:#16a34a
```

## 6. Dashboard Features

```mermaid
flowchart TB
    subgraph Dashboard["Admissions Dashboard"]
        STATS[Stats: Total / Recommend / Consider / Needs Attention / Hidden Gems]
        EVAL[Evaluation Settings<br/>Adjustable weight sliders]
        FAIR[Fairness Audit<br/>Score distribution by school type]
        GRID[Candidate Grid<br/>Sparse Profile badges]
    end

    subgraph Detail["Candidate Detail Panel"]
        INFO[Personal Info + Education]
        SCORES[5 Dimension Scores<br/>with explanations + evidence]
        INSIGHT[AI Insight<br/>Baseline vs AI delta]
        DETECT[AI Detection<br/>Stylometry metrics]
        FEYN[Feynman Teaching Score]
        OVERRIDE[Committee Override]
    end

    GRID --> Detail

    style Dashboard fill:#e0f2fe,stroke:#0284c7
    style Detail fill:#fef3c7,stroke:#d97706
```

## 7. Tech Stack

```mermaid
graph LR
    subgraph FE["Frontend"]
        NX[Next.js 16] --> RC[React 19]
        RC --> TW[Tailwind CSS 4]
        RC --> TS[TypeScript]
    end

    subgraph BE["Backend"]
        FA[FastAPI] --> PY[Python 3.12]
        FA --> PD[Pydantic v2]
        PY --> AN[Anthropic SDK]
    end

    subgraph AI["AI Layer"]
        AN --> CS[Claude Sonnet 4]
        CS --> SC[Scoring]
        CS --> DT[Detection]
        CS --> FM[Feynman Chat + Eval]
    end

    subgraph NON["Non-AI Processing"]
        PSE[Signal Extraction]
        PBS[Baseline Scoring]
        PST[Statistical Stylometry]
        PLD[Language Detection]
        PPI[PII Anonymization]
    end

    style FE fill:#e0e7ff,stroke:#4f46e5
    style BE fill:#f0fdf4,stroke:#10b981
    style AI fill:#fce7f3,stroke:#ec4899
    style NON fill:#fef3c7,stroke:#d97706
```
