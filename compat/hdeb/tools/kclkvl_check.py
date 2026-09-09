#!/usr/bin/env python3
"""kclkvl_check.py — rule-based (no ML) KCL/KVL check on an HDEB document.

Model: linearised DC power flow on network.branches (reactance x_pu, flows in kW).
 KCL: at every bus, sum(scheduled_kw of blocks at bus) - load_kw - net branch outflow == 0
 KVL: declared flows f must be consistent with a bus-angle potential: X·f = A·θ for some θ
      (equivalently sum(x·f) == 0 around every loop). If no flows are declared, they are
      solved from KCL and only KCL residual at the slack + line limits are reported.
Usage: python3 kclkvl_check.py doc.json [--tol-kw 1.0]   exit 0 = pass, 1 = violations
"""
import json, sys
import numpy as np

def check(doc, tol_kw=1.0):                                                        # --- 20-line core ---
    net = doc["network"]; bus = [b["id"] for b in net["buses"]]; ix = {b: i for i, b in enumerate(bus)}
    br = net["branches"]; nb, nl = len(bus), len(br)
    A = np.zeros((nl, nb)); x = np.array([l["x_pu"] for l in br], float)
    for k, l in enumerate(br): A[k, ix[l["from"]]], A[k, ix[l["to"]]] = 1.0, -1.0
    P = -np.array([b.get("load_kw", 0.0) for b in net["buses"]], float)          # net injection per bus
    for blk in doc["blocks"]:
        b = (blk.get("resource") or {}).get("bus"); p = (blk.get("power") or {}).get("scheduled_kw")
        if b in ix and p is not None: P[ix[b]] += p
    declared = [l.get("flow_kw") for l in br]
    if all(f is not None for f in declared):
        f = np.array(declared, float)
        theta, *_ = np.linalg.lstsq(A, x * f, rcond=None); kvl = x * f - A @ theta   # loop-law residual (kW·pu)
    else:
        s = next((ix[b["id"]] for b in net["buses"] if b.get("slack")), 0); keep = [i for i in range(nb) if i != s]
        B = A.T @ np.diag(1 / x) @ A; theta = np.zeros(nb); theta[keep] = np.linalg.solve(B[np.ix_(keep, keep)], P[keep])
        f = (A @ theta) / x; kvl = np.zeros(nl)                                    # KVL holds by construction
    kcl = A.T @ f - P                                                                # KCL residual per bus (kW)
    over = [(l["id"], float(abs(fk)), l["limit_kw"]) for l, fk in zip(br, f) if l.get("limit_kw") and abs(fk) > l["limit_kw"]]
    viol = {"kcl": {b: float(r) for b, r in zip(bus, kcl) if abs(r) > tol_kw},
            "kvl": {l["id"]: float(r) for l, r in zip(br, kvl) if abs(r) > tol_kw},
            "limits": over, "flows_kw": {l["id"]: float(fk) for l, fk in zip(br, f)}}
    return (not viol["kcl"] and not viol["kvl"] and not over), viol                # --- end core ---

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tol = float(sys.argv[sys.argv.index("--tol-kw") + 1]) if "--tol-kw" in sys.argv else 1.0
    ok, v = check(json.load(open(args[0], encoding="utf-8")), tol)
    print(json.dumps({"pass": ok, **v}, indent=1)); sys.exit(0 if ok else 1)
