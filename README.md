# Open Envelope

**An open, vendor-neutral interchange standard for what a flexible electrical resource *can do* — and a verification object that lets anyone check whether a plan stays inside it.**

Site: https://open-envelope.vercel.app (after Vercel import) · License: Apache-2.0 (code) / CC BY 4.0 (spec prose) · Status: draft 0.0.3

> open & secure — don't trust, verify it.

## Four layers

| Layer | Object | What it carries |
|---|---|---|
| L0 | **Envelope** | window × bounds × linear constraint set `A·u ≤ b` × discrete **modes** × params (storage, ramp) × fallback × **consent** × provenance |
| L1 | **Position** | a trajectory inside the envelope: `schedule` / `cleared` / `measured` |
| L2 | **Offer** | market wrapper: price, divisibility, linked / exclusive groups, market_ref |
| L3 | **Attestation** | rule_set@version · input_sha256 · verdict · violations[] · signature — reproducible by anyone |

Aggregation across device → site → aggregator → area → system must declare `approximation ∈ {inner, outer, exact}`; `inner` + rule `agg.sum` is the checkable form of *realizability* in the recent literature.

The validator **only judges** (KCL/KVL, envelope membership, ramp, SOC, modes, market consistency, consent). It never issues instructions — that line is at once a technical, commercial and regulatory boundary.

## Repository

```
envelope/        schema 0.0.3 · RFC-0 proposal · examples (envelope, aggregated, attestation)
registry/        standards.yaml (35 standards: OPC · LF Energy · IEC/IEEE · China GB/DL/T/团标)
                 profiles/  mapping file format + S2 → L0 example
compat/hdeb/     frozen bridge format 0.1 · JEPX spot → blocks converter · 20-line KCL/KVL checker
tests/           pytest (6) · JEPX fixture 2026-04-01
docs/            SOURCES.md (57 sources, confidence-tiered) · verification log · mapping notes
site/            the published pages (Vercel): index, architecture, glossary, standards-library
site/internal/   strategy review & review-landscape (noindex; internal language)
```

## Quick start

```bash
pip install -r requirements.txt
python -m pytest -q
python compat/hdeb/tools/kclkvl_check.py compat/hdeb/examples/site_schedule_pass.json   # exit 0
python compat/hdeb/tools/jepx_to_hdeb.py tests/fixtures/jepx_spot_summary_2026-04-01.csv --areas 東京 -o out.json
```

## Pages (site/)

- **/** — hub: status, reading paths by role, falsifiable markers, pending decisions
- **/architecture** — reference architecture v0.3: end-to-end integration (fig. 1), OPC UA & LF Energy mapping, aggregation semantics, validation pipeline, rule set, lifecycle, deployment, governance
- **/standards-library** — how existing standards map onto the four layers; China's stack coincides with IEC at the device layer and diverges at the VPP layer
- **/glossary** — 126 terms, searchable
- **/internal/review**, **/internal/review-landscape** — strategy and landscape (not indexed)

## Deploy (Vercel)

Import this repo in Vercel → Framework preset *Other* → no build step. `vercel.json` sets `outputDirectory: site`, clean URLs and `noindex` on `/internal/`.

## Contributing

A mapping in `registry/profiles/` is accepted only with paired test vectors. Anything that makes the free validator depend on a non-public model is declined. Extension namespaces (`ext["…"]`) are first-come, non-exclusive.

## Relation to existing standards

Open Envelope does not compete with S2 (EN 50491-12-2), Shapeshifter/UFTP, IEC 62325 CIM or OpenADR 3; it is the missing object representation between them. See `site/standards-library.html` and `registry/standards.yaml`.
