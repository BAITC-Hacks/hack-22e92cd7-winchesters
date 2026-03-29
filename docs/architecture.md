# InVision U — Solution Architecture

## 1. System Architecture (High-Level)

```mermaid
graph TB
    subgraph Frontend["Frontend (Next.js + React)"]
        APP[Application Form<br/>/apply]
        DASH[Evaluation Dashboard<br/>/]
    end

    subgraph Backend["Backend (FastAPI)"]
        API[REST API Layer]
        subgraph Scoring["Scoring Engine"]
            SE[Signal Extractor<br/>Pure Python]
            BL[Baseline Scorer<br/>Rule-based]
            AI[AI Scorer<br/>Claude Sonnet 4]
            AGG[Score Aggregator<br/>Weighted]
        end
        subgraph Detection["AI Detection"]
            STYL[Statistical Stylometry<br/>7 metrics, no AI]
            QUAL[Qualitative Analysis<br/>Claude Sonnet 4]
            COMB[Combined Score<br/>40/60 blend]
        end
        PII[PII Anonymizer]
        OVR[Committee Override<br/>Human-in-the-Loop]
    end

    subgraph Storage["Data Layer"]
        DB[(candidates.json)]
        CACHE[In-Memory Cache]
    end

    subgraph External["External Services"]
        CLAUDE[Claude API<br/>Sonnet 4]
    end

    APP -->|POST /api/candidates| API
    DASH -->|GET, POST| API
    API --> SE
    SE --> BL
    SE --> AI
    AI --> PII
    PII -->|anonymized data| CLAUDE
    BL --> AGG
    AI --> AGG
    AGG --> CACHE
    API --> STYL
    STYL --> QUAL
    QUAL --> PII
    QUAL --> COMB
    OVR -->|override score| AGG
    API --> DB
    API --> CACHE

    style Frontend fill:#e0e7ff,stroke:#4f46e5
    style Backend fill:#f0fdf4,stroke:#10b981
    style Storage fill:#fef3c7,stroke:#f59e0b
    style External fill:#fce7f3,stroke:#ec4899
```

## 2. Scoring Pipeline (3-Stage)

```mermaid
flowchart LR
    subgraph Stage1["Stage 1: Signal Extraction (Pure Python)"]
        C[Candidate Data] --> EX[extract_signals]
        EX --> AC[Academic Signals<br/>GPA, achievements, skills]
        EX --> LD[Leadership Signals<br/>roles, projects, keywords]
        EX --> GR[Growth Signals<br/>starting_level → current_level<br/>delta = how far they came]
        EX --> CM[Communication Signals<br/>essay metrics, interview]
        EX --> MO[Motivation Signals<br/>keywords, evidence]
    end

    subgraph Stage2["Stage 2: Dual Scoring"]
        AC & LD & GR & CM & MO --> BAS[Baseline Scorer<br/>Rule-based heuristics<br/>Deterministic]
        AC & LD & GR & CM & MO --> AIS[AI Scorer<br/>Signals + Raw Text → Claude<br/>Nuanced understanding]
    end

    subgraph Stage3["Stage 3: Aggregation"]
        BAS --> W[Weighted Sum<br/>5 dimensions]
        AIS --> W
        W --> REC[Recommendation<br/>shortlist / review / decline]
        W --> RNK[Ranking]
    end

    style Stage1 fill:#ede9fe,stroke:#7c3aed
    style Stage2 fill:#e0f2fe,stroke:#0284c7
    style Stage3 fill:#f0fdf4,stroke:#16a34a
```

## 3. AI Detection Pipeline

```mermaid
flowchart LR
    subgraph Input
        ESS[Essay Text]
        INT[Interview Transcript]
    end

    subgraph S1["Stage 1: Statistical Stylometry (No AI)"]
        ESS --> COMP[compute_stylometry]
        INT --> COMP
        COMP --> TTR[TTR<br/>Vocabulary richness]
        COMP --> SV[Sentence Variance<br/>AI = low, Human = high]
        COMP --> HP[Hapax Ratio<br/>Unique word frequency]
        COMP --> FR[Formality Ratio<br/>AI filler phrases]
        COMP --> VO[Vocab Overlap<br/>Essay vs Interview gap]
        COMP --> AWL[Avg Word Length]
        COMP --> ASL[Avg Sentence Length]
        TTR & SV & HP & FR & VO & AWL & ASL --> SS[Statistical Score<br/>0-100]
    end

    subgraph S2["Stage 2: Claude Qualitative"]
        ESS --> CL[Claude Analysis]
        INT --> CL
        SS -.->|metrics as context| CL
        CL --> QS[Qualitative Score<br/>voice, depth, specificity]
    end

    subgraph S3["Stage 3: Combined"]
        SS -->|40%| BLEND[Weighted Blend]
        QS -->|60%| BLEND
        BLEND --> FINAL[Authenticity Score<br/>0-100 + flags]
    end

    style S1 fill:#fef3c7,stroke:#d97706
    style S2 fill:#e0e7ff,stroke:#4f46e5
    style S3 fill:#f0fdf4,stroke:#16a34a
```

## 4. Trajectory Scoring (Growth Delta)

```mermaid
flowchart TB
    subgraph Philosophy["Scoring Philosophy: Additive, Not Punitive"]
        direction TB
        P1["Measures HOW FAR you came<br/>not just WHERE you are"]
        P2["Nobody penalized for privilege<br/>Extra credit for overcoming adversity"]
    end

    subgraph Computation["Growth Delta Computation"]
        SCH[School Type] -->|SCHOOL_ADVANTAGE map| SL[Starting Level<br/>village=25, public=40,<br/>lyceum=60, private=75]
        ADV[Adversity Indicators<br/>from essay/interview] -->|reduce starting level| SL
        GPA[GPA + Achievements] --> CL[Current Level]
        PROJ[Projects + Initiatives] --> CL
        EC[Extracurricular Depth] --> CL
        SL --> DELTA["Delta = Current - Starting"]
        CL --> DELTA
    end

    subgraph Scoring["Score Formula"]
        DELTA -->|"× 0.6"| DC[Delta Component<br/>60% weight]
        CL -->|"× 0.4"| BC[Base Component<br/>40% weight]
        DC --> TOTAL[Growth Score]
        BC --> TOTAL
        SUS[Sustained Commitments<br/>2+ years] -->|bonus +5 each| TOTAL
        SELF[Self-Started Projects] -->|bonus +5 each| TOTAL
    end

    subgraph Example["Example Comparison"]
        E1["Village student<br/>start=25 → current=75<br/>delta=50 → score=60"]
        E2["Elite student<br/>start=75 → current=85<br/>delta=10 → score=40"]
        E3["Elite + self-starter<br/>start=75 → current=95<br/>delta=20 → score=50"]
    end

    style Philosophy fill:#ede9fe,stroke:#7c3aed
    style Computation fill:#e0f2fe,stroke:#0284c7
    style Scoring fill:#f0fdf4,stroke:#16a34a
    style Example fill:#fef3c7,stroke:#d97706
```

## 5. Data Flow (End-to-End)

```mermaid
sequenceDiagram
    participant S as Student
    participant F as Frontend
    participant B as Backend API
    participant SE as Signal Extractor
    participant BL as Baseline Scorer
    participant AI as AI Scorer
    participant C as Claude API
    participant CM as Committee

    S->>F: Fill application form
    F->>B: POST /api/candidates
    B->>B: Store candidate

    CM->>F: Open dashboard
    F->>B: POST /api/scoring/baseline/all
    B->>SE: Extract signals (pure Python)
    SE-->>BL: Structured signals
    BL-->>B: Baseline scores (5 dimensions)
    B-->>F: Ranked candidates

    CM->>F: Request AI scoring
    F->>B: POST /api/scoring/ai/{id}
    B->>SE: Extract signals
    B->>B: Anonymize PII
    B->>C: Signals + raw text (no PII)
    C-->>B: AI scores + explanations
    B-->>F: AI scores with evidence

    CM->>F: Request AI detection
    F->>B: POST /api/analysis/ai-detection/{id}
    B->>B: Compute stylometry (no AI)
    B->>B: Anonymize PII
    B->>C: Essay + metrics context
    C-->>B: Qualitative assessment
    B->>B: Blend 40% stat + 60% qual
    B-->>F: Authenticity score + flags

    CM->>F: Override dimension score
    F->>B: POST /api/scoring/override
    B->>B: Recompute overall score
    B-->>F: Updated scores
```

## 6. Tech Stack

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
        AN --> CS[Claude Sonnet 4<br/>Scoring + Detection]
    end

    subgraph NON["Non-AI Processing"]
        PSE[Signal Extraction<br/>Pure Python]
        PBS[Baseline Scoring<br/>Rule-based]
        PST[Statistical Stylometry<br/>Math only]
        PPI[PII Anonymization<br/>Regex-based]
    end

    style FE fill:#e0e7ff,stroke:#4f46e5
    style BE fill:#f0fdf4,stroke:#10b981
    style AI fill:#fce7f3,stroke:#ec4899
    style NON fill:#fef3c7,stroke:#d97706
```
