#!/usr/bin/env python3
"""jepx_to_hdeb.py — JEPX spot_summary CSV -> HDEB v0.1 document.

Input format (verified 2026-09-04 against jepx.jp, UTF-8, 19 columns):
  受渡日, 時刻コード(1-48), 売り入札量(kWh), 買い入札量(kWh), 約定総量(kWh),
  システムプライス(円/kWh), エリアプライス×9 (北海道,東北,東京,中部,北陸,関西,中国,四国,九州),
  売りブロック入札総量, 売りブロック約定総量, 買いブロック入札総量, 買いブロック約定総量 (kWh)

Output: one `system`-level cleared block per 30-min slot, with nine `area` child blocks
carrying area prices. Area-level cleared volumes are NOT in this file -> energy.kwh = null.

Data © Japan Electric Power Exchange. JEPX terms require attribution ("出所を明示").
Usage:
  python3 jepx_to_hdeb.py spot_summary_2026.csv -o out.json [--date 2026/04/01] [--areas 東京,関西]
  python3 jepx_to_hdeb.py --fetch 2026 -o out.json   # downloads from jepx.jp
"""
import argparse, csv, io, json, sys, urllib.request
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
AREAS = [("北海道","JP-HOKKAIDO"),("東北","JP-TOHOKU"),("東京","JP-TOKYO"),("中部","JP-CHUBU"),
         ("北陸","JP-HOKURIKU"),("関西","JP-KANSAI"),("中国","JP-CHUGOKU"),("四国","JP-SHIKOKU"),("九州","JP-KYUSHU")]
EXPECTED_COLS = 19
SRC_URL = "https://www.jepx.jp/js/csv_read.php?dir=spot_summary&file=spot_summary_{year}.csv"

def _num(s):
    s = s.strip()
    return None if s in ("", "-") else float(s)

def slot_window(date_str, code):
    d = datetime.strptime(date_str, "%Y/%m/%d").replace(tzinfo=JST)
    start = d + timedelta(minutes=30 * (int(code) - 1))
    return start, start + timedelta(minutes=30)

def convert(text, src, retrieved_at, only_date=None, only_areas=None, gen="jepx_to_hdeb.py/0.1"):
    rows = list(csv.reader(io.StringIO(text)))
    header, body = rows[0], [r for r in rows[1:] if r and r[0]]
    if len(header) != EXPECTED_COLS:
        raise SystemExit(f"unexpected column count {len(header)} != {EXPECTED_COLS}; header={header}")
    if not header[0].startswith("受渡日") or "システムプライス" not in header[5]:
        raise SystemExit("header does not look like JEPX spot_summary; refusing to guess")
    blocks = []
    for i, r in enumerate(body, start=2):
        date, code = r[0], r[1]
        if only_date and date != only_date: continue
        start, end = slot_window(date, code)
        sid = f"urn:jepx:spot:{date.replace('/','-')}:{int(code):02d}:system"
        prov = {"source": "JEPX spot_summary", "url": src, "retrieved_at": retrieved_at,
                "license": "JEPX website terms: reuse permitted with attribution", "attribution": "© Japan Electric Power Exchange",
                "generator": gen, "raw_ref": f"line {i}"}
        kwh = _num(r[4])
        blocks.append({
            "hdeb_version": "0.1", "block_id": sid, "parent_id": None, "hierarchy_level": "system", "kind": "cleared",
            "resource": {"type": "market", "bus": None, "area": "JP", "voltage_kv": None},
            "window": {"start": start.isoformat(), "end": end.isoformat(), "resolution_min": 30},
            "power": {"scheduled_kw": None if kwh is None else kwh * 2.0},   # 30-min energy -> average kW
            "energy": {"kwh": kwh, "direction": "bidirectional"},
            "price": {"currency": "JPY", "unit": "per_kWh", "value": _num(r[5]), "reference": "system"},
            "market_volume": {"sell_bid_kwh": _num(r[2]), "buy_bid_kwh": _num(r[3]), "cleared_kwh": kwh},
            "market_block": {"sell_block_bid_kwh": _num(r[15]), "sell_block_cleared_kwh": _num(r[16]),
                             "buy_block_bid_kwh": _num(r[17]), "buy_block_cleared_kwh": _num(r[18])},
            "provenance": prov, "ext": {"jp.jepx": {"時刻コード": int(code), "受渡日": date}}})
        for k, (jp, iso) in enumerate(AREAS):
            if only_areas and jp not in only_areas and iso not in only_areas: continue
            blocks.append({
                "hdeb_version": "0.1", "block_id": sid.replace(":system", f":{iso}"), "parent_id": sid,
                "hierarchy_level": "area", "kind": "cleared",
                "resource": {"type": "market", "bus": None, "area": iso, "voltage_kv": None},
                "window": {"start": start.isoformat(), "end": end.isoformat(), "resolution_min": 30},
                "power": {}, "energy": {"kwh": None, "direction": "bidirectional"},
                "price": {"currency": "JPY", "unit": "per_kWh", "value": _num(r[6 + k]), "reference": "area"},
                "provenance": prov})
    return {"hdeb_version": "0.1", "generated_at": retrieved_at, "blocks": blocks}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?", help="local spot_summary_YYYY.csv")
    ap.add_argument("--fetch", metavar="YEAR", help="download from jepx.jp instead of local file")
    ap.add_argument("-o", "--out", default="-")
    ap.add_argument("--date", help="keep only this 受渡日, e.g. 2026/04/01")
    ap.add_argument("--areas", help="comma list of areas to keep (JP names or ISO-like codes)")
    a = ap.parse_args()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if a.fetch:
        src = SRC_URL.format(year=a.fetch)
        req = urllib.request.Request(src, headers={"User-Agent": "hdeb-open/0.1 (+jepx attribution honoured)"})
        raw = urllib.request.urlopen(req, timeout=60).read()
        try: text = raw.decode("utf-8-sig")
        except UnicodeDecodeError: text = raw.decode("cp932")
    elif a.csv:
        src = a.csv; text = open(a.csv, encoding="utf-8-sig").read()
    else:
        ap.error("need CSV path or --fetch YEAR")
    doc = convert(text, src, now, a.date, set(a.areas.split(",")) if a.areas else None)
    out = json.dumps(doc, ensure_ascii=False, indent=1)
    (sys.stdout if a.out == "-" else open(a.out, "w", encoding="utf-8")).write(out)
    print(f"{len(doc['blocks'])} blocks", file=sys.stderr)

if __name__ == "__main__":
    main()
