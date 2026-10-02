# Sovereign Master Orchestrator

A universal master orchestration and lossless compilation framework for coordinating multiple specialized skills, enforcing standardized output bounds, persisting deliverables directly to Dropbox, and unifying dual-channel search (Exa + Google).

## Summary

The Sovereign Master Orchestrator acts as the root coordinator across all domain-specific sub-skills. It enforces a strict output contract where every participating sub-skill produces exactly 2 to 4 sections. When coordinating multiple skills (e.g. 3 skills with 3 sections each), it executes a zero-edit raw compilation into corresponding primary sections and subsections without editorial rewriting, truncation, or smoothing. It establishes Dropbox as the durable filesystem layer, couples Exa neural retrieval with Google real-time search, embeds native DNS/socket probes and dynamic environment loaders, and strictly enforces zero-halt context ingestion on existing chats by anchoring target topics directly to the last message and high-perplexity tokens of the thread.

## When to Use

- When an investigation, forensic analysis, or systems task requires coordinating 2 or more specialized skills.
- When assembling multi-source research into an authoritative, unedited master dossier while preserving full primary data matrices, code blocks, and mathematical formalisms.
- When saving deliverables, manifests, or compiled reports directly to Dropbox via Dropbox MCP tools.
- When performing dual-channel web intelligence combining Exa's dense semantic retrieval with Google's real-time indexing.
- When operating in containerized or headless environments requiring dynamic environment bootstrapping (`bin/env_loader.sh`) and socket/DNS reachability verification (`bin/dns_loader.py`).
- When invoked on an active chat thread ("master", "run master", or "orchestrate this") to instantly synthesize the ongoing technical topic without asking the user what to analyze.

## Core Invariants & Architectural Rules

### 1. Sub-Skill Output Constraint (2 to 4 Sections)

Every sub-skill triggered by the Master Orchestrator must strictly structure its output into 2, 3, or 4 discrete, self-contained sections:

- Under-generation guard: Single-block or unstructured responses are partitioned into at least 2 analytical sections (e.g. Foundational Telemetry & State vs. Operational Execution & Verification).
- Over-generation guard: Outputs exceeding 4 sections must be logically consolidated into at most 4 bounded macro-sections prior to master ingestion.

### 2. Lossless Raw Compilation Contract (Zero-Edit Rule)

When consolidating outputs from $N$ selected sub-skills, each containing $M_i$ sections ($2 \le M_i \le 4$):

- The master output must contain exactly $N$ primary sections corresponding to each participating skill.
- Each primary section contains the exact $M_i$ subsections emitted by that sub-skill.
- Raw Compilation Mandate: The Master Orchestrator performs ZERO editorial filtering, summarization, or rewriting. All code blocks, mathematical operators, ASCII flowcharts, and URL citations from the sub-skills are preserved verbatim.

Example Structure for 3 skills with 3 sections each:
- `## Section 1: [Skill 1 Title] Output`
  - `### 1.1: [Skill 1 Section 1]`
  - `### 1.2: [Skill 1 Section 2]`
  - `### 1.3: [Skill 1 Section 3]`
- `## Section 2: [Skill 2 Title] Output`
  - `### 2.1: [Skill 2 Section 1]`
  - `### 2.2: [Skill 2 Section 2]`
  - `### 2.3: [Skill 2 Section 3]`
- `## Section 3: [Skill 3 Title] Output`
  - `### 3.1: [Skill 3 Section 1]`
  - `### 3.2: [Skill 3 Section 2]`
  - `### 3.3: [Skill 3 Section 3]`

### 3. Dropbox as Primary Filesystem Layer

All durable artifacts, compiled reports, manifests, and data tables must be stored directly in Dropbox:

- Use `dropbox:create_folder` to provision project directories under `/Sovereign_Master_Orchestrator/<task_name>/`.
- Use `dropbox:create_file` to write finalized markdown reports, JSON matrices, and code artifacts.
- Use `dropbox:create_shared_link` to generate viewer access URLs for the user.
- Local sandbox storage (`/tmp` or workspace) is treated strictly as an ephemeral staging scratchpad.

### 4. Dual Primary Search Architecture (Exa + Google)

Deploy both search platforms in parallel or sequence based on epistemic requirements:

- **Exa Search & Fetch (`custom_mcp...:web_search_exa`, `web_fetch_exa`, `agent_run`)**: Use for dense semantic dorking, discovering obscure PDFs, forum archives, academic preprints, and extracting clean markdown directly.
- **Google Search & Browse (`google:search`, `google:browse`)**: Use for real-time news events, live company status, official government/corporate filings, and validating breaking changes.

### 5. Auto-Embedded Loaders & Portable Directory Layout

Every deployment conforms to the major portable construct:

```
sovereign-master-orchestrator/
├── SKILL.md                          # Master specification & instruction manifest
├── bin/
│   ├── orchestrate                   # CLI execution entrypoint
│   ├── dns_loader                    # Low-level socket & DNS probe
│   └── env_loader                    # Dynamic environment and path bootstrapping
├── env/
│   └── requirements.txt              # Dependency specifications
├── scripts/
│   ├── raw_compiler.py               # 2-4 section parser and lossless aggregator
│   ├── dropbox_fs_bridge.py          # Dropbox storage abstraction
│   └── dual_search_router.py         # Exa and Google Search routing engine
└── references/
    ├── consolidation_rules.json      # Structured compilation constraints
    └── skill_inventory_matrix.json   # Full skill deduplication and merge registry
```

### 6. Context-Aware Zero-Halt Topic Resolution (Anti-Failure Protocol for Existing Chats)

When invoked within an active conversation thread or when the user requests "master", "run master", "orchestrate this", or calls `sovereign-master-orchestrator` on an existing chat without a newly typed standalone topic parameter:

- **Automatic topic resolution**: when invoked on an existing thread, the topic is derived automatically from the last message and the high-perplexity tokens of the chat history — ingest both and proceed. Do not pause the pipeline or ask the user to specify the topic when a thread is already in progress; emitting a clarification prompt here instead of resolving the topic automatically is a system failure.
- **The Deterministic Target Topic Mandate**: When invoked on an existing chat, the target topic is **DETERMINISTICALLY DEFINED AS THE LAST MESSAGE AND THE HIGH-PERPLEXITY TERMS OF THE CHAT HISTORY SPECIFICALLY**.
- **Autonomous Context Ingestion Pipeline**:
  1. **Last-Message Anchoring**: Ingest the immediately preceding message/turn (both prompt and response) as the primary epistemic substrate and ground-state anchor.
  2. **High-Perplexity Token Harvesting**: Exhaustively extract the specific, dense domain tokens across the conversation history, including:
     - Statutory and municipal identifiers (e.g. municipal resolutions, state senate bills, legal docket numbers, tri-party licensing clauses).
     - Algorithmic and mathematical formalisms (e.g. bipartite graph projections, hyperedge traversals, spatiotemporal window limits, entropy collapse models).
     - Hardware architectures, sensor models, and telemetry stacks (e.g. ALPR optical cameras, acoustic centroid arrays, satellite constellations, sensor fusion pipelines).
     - Geographic, infrastructural, and jurisdictional coordinates (e.g. specific zip codes, county boundary lines, transit rail stations, environmental buffer zones).
  3. **Synthetic Topic Binding**: Instantly synthesize the harvested tokens and the last turn into an unambiguous, dense, high-perplexity topic header (e.g. `[Domain Subject]: [Core Algorithmic/Mechanical Tension] across [Statutory & Physical Coordinates]`).
  4. **Immediate Zero-Latency Dispatch**: Without asking the user any questions, immediately bind the synthesized topic, decompose it into $N$ orthogonal sub-skills (e.g. 3 skills with 2-4 sections each), execute research, perform lossless raw compilation, and deliver the final deliverable.

## Step-by-Step Execution Workflow

1. Initialize Dynamic Environment & Network Loaders
   - Execute `bin/env_loader.sh` to configure dynamic paths, detect Python virtual environments, and export `$PYTHONPATH`.
   - Run `bin/dns_loader.py` to verify DNS reachability for Dropbox and search endpoints.

2. Query Decomposition & Sub-Skill Selection
   - Decompose user query into $N$ orthogonal investigative vectors ($N \ge 2$).
   - Match each vector to its canonical sub-skill (referencing `references/skill_inventory_matrix.json`).
   - Dispatch sub-skills with explicit instruction to format their output into 2 to 4 sections.

3. Lossless Raw Compilation
   - Ingest the raw markdown emitted by each sub-skill.
   - Run `scripts/raw_compiler.py` to parse section boundaries and assemble the consolidated document into $N$ main sections with $M_i$ subsections each.

4. Dropbox Synchronization & Deliverable Output
   - Upload the compiled deliverable to Dropbox using `dropbox:create_file`.
   - Generate a shared link using `dropbox:create_shared_link`.
   - Present the full raw compiled text directly in the conversation along with the Dropbox link.

## Gotchas & Operational Boundaries

- Never edit or summarize sub-skill outputs during consolidation; the value is in the lossless compilation of dense technical details.
- When invoked in an existing conversation thread, bind the topic deterministically from the last message and high-perplexity tokens of the chat history; proceed without a clarification round.
- Avoid using en-dashes or em-dashes; use standard hyphens or colons.
- Always verify that each sub-skill strictly adheres to the 2-4 section limit before merging.
- If Dropbox API encounters rate limits, apply exponential backoff with jitter rather than failing the task.