---
title: M3 / ERP Integration
tags: [m3-erp-integration]
project: m3-erp-integration
status: active
phase: planning
---

# M3 / ERP Integration

**Status:** Active — Planning  
**System:** Infor M3 (MOVEX)

## Objective

Establish clean, reliable integration patterns between the modernized MES and M3/Infor, making ERP data accessible to the AI Platform without creating brittle point-to-point connections.

## Integration Principles

- **API-first** — avoid direct DB integrations where possible
- **Event-driven** — favor pub/sub over polling
- **Decoupled** — MES and ERP changes should not cascade

## Key Integration Points

| Data Domain | Direction | Priority |
|-------------|-----------|----------|
| Production orders | M3 → MES | High |
| Work center status | MES → M3 | High |
| Quality events | MES → M3 | Medium |
| Inventory updates | Bidirectional | Medium |

## Signals to Watch

Filter the Signal Tracker by `m3-erp-integration` for all relevant intelligence on ERP integration patterns, Infor APIs, and event-driven architectures.
