# Mapping: HDEB 0.1 ↔ OpenEnvelope 0.0.3 ↔ existing open standards

Confidence: ★ verified primary · ◆ credible secondary · ◇ unverified. Mappings to S2 are read from the S2 JSON schema repo ★; Shapeshifter/CIM/OpenADR mappings are conceptual ◆ and need field-level confirmation.

| Concept | HDEB 0.1 | OpenEnvelope 0.0.3 | S2 (EN 50491-12-2) ★ | Shapeshifter / UFTP ◆ | IEC 62325 CIM ◆ | OpenADR 3 ◆ |
|---|---|---|---|---|---|---|
| Time window | `window.start/end/resolution_min` | L0 `window.{start,end,step_min}` | `FRBC.Timer`, instruction `execution_time` | `FlexRequest.ISP` intervals | `Period.timeInterval`, `resolution` | `intervalPeriod` |
| Power envelope | `power.min_kw/max_kw` | L0 `bounds.p` | `FRBC.OperationMode` element power ranges; `PEBC` power envelope | `FlexOffer.Power` per ISP | `Point.quantity` | `payloads` per interval |
| Ramp | `power.ramp_*` | L0 `constraints[diff]` | `FRBC.OperationMode` transitions / timers | — | — | — |
| Storage / SOC | `storage.*` | L0 `params.storage` + `constraints` | `FRBC.StorageDescription`, `FillLevel` | — | — | — |
| Schedule | `kind=schedule`, `power.scheduled_kw` | L1 `series.p` (kind=schedule) | `FRBC.Instruction` | `FlexOrder` | `Schedule_MarketDocument` | `event` |
| Cleared / measured | `kind=cleared/measured` | L1 kind=cleared/measured | `FRBC.UsageForecast` / metering | `FlexSettlement` | `Publication_MarketDocument` | `report` |
| Price / bid | `price.*`, `market_block.*` | L2 `price`, `divisible`, `linked`, `exclusive_group` | — | `FlexOffer.Price` | `Bid_MarketDocument`, `BidTimeSeries.blockBid`, `linkedBidsIdentification`, `exclusiveBidsIdentification` | `priceMap` |
| Hierarchy | `parent_id`, `hierarchy_level` | `resource_ref` + explicit `aggregation_of[]` refs | RM ↔ CEM (two roles only) | AGR ↔ DSO/CRO | `RegisteredResource` / `Domain` | `program` → `ven` |
| Fallback | `fallback.*` | L0 `fallback` | `FRBC` "no instruction" default mode ◇ | — | — | — |
| Provenance | `provenance.*` | every layer `provenance` | — | `sender/recipient domain` | `sender_MarketParticipant` | — |
| Verification result | *(absent)* | **L3 Attestation** | — | — | — | — |
| Consent / residency | *(absent)* | **L0 consent** | — | — | — | — |

## HDEB → OpenEnvelope (lossless direction)

```
HDEB block  ──▶  OpenEnvelope Envelope (window, bounds from power.min/max, constraints from ramp/storage, fallback, provenance)
            ──▶  OpenEnvelope Position (if power.scheduled_kw / energy.kwh present; kind from HDEB.kind)
            ──▶  OpenEnvelope Offer   (if price or market_block present)
parent_id   ──▶  Envelope.aggregation_of[] on the parent
ext[*]      ──▶  same namespace, unchanged
```

OpenEnvelope → HDEB is lossy (constraint sets that are not expressible as min/max/ramp/SOC, and all of L3, are dropped).

## JEPX-specific

JEPX spot_summary carries only system totals and area prices; it yields OpenEnvelope **Position(kind=cleared)** at system level and **Offer-less price references** at area level. Per-participant offers (L2) never appear in public data.
