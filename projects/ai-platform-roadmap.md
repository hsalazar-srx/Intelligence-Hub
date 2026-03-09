---
title: AI Platform Roadmap
tags: [ai-platform]
project: ai-platform
status: active
phase: strategy
---

# AI Platform Roadmap

**Status:** Active — Strategy & Foundation  
**Dependency:** MES Modernization (data layer prerequisite)

## Objective

Build an organizational AI platform that augments manufacturing operations, integrates with M3/ERP, and delivers measurable value — starting with the data foundation unlocked by MES modernization.

## Platform Components (Target Architecture)

| Layer | Component | Notes |
|-------|-----------|-------|
| Data | Clean manufacturing event stream | Output of MES Phase 2 |
| Inference | LLM / ML model layer | To be evaluated |
| Integration | M3/ERP connectors | Phase 3 dependency |
| Applications | Use-case specific agents | TBD by business need |
| Governance | Eval, monitoring, access control | Build from day one |

## Candidate Use Cases

- Predictive maintenance signals from MES data
- M3 data querying via natural language
- Document intelligence (SOPs, quality docs)
- Operational reporting automation

## Principles

1. **Data before models** — clean data is the prerequisite
2. **Composable over monolithic** — same principle as MES approach
3. **Governance from day one** — not bolted on later
4. **Build on proven patterns** — RAG, not fine-tuning, for enterprise knowledge

## Signals to Watch

Filter the Signal Tracker by `ai-platform` for all relevant intelligence.
