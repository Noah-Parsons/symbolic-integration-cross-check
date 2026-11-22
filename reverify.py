"""Re-check stored CAS results with the current parser and oracle (no CAS calls)."""
import json, random, collections, sys
import sympy as sp
import crosscheck as C

rows = [json.loads(l) for l in open(sys.argv[1] if len(sys.argv) > 1 else "results.jsonl")]
for r in rows:
    f = sp.sympify(r["integrand"])
    for s in ("sympy", "maxima", "giac"):
        cell = r[s]
        if cell["verdict"] in ("UNEVAL", "TIMEOUT", "ERROR"):
            continue
        text = str(cell["result"]).split(" [")[0]
        try:
            F = C.sympy_from_srepr(text) if s == "sympy" else C.parse(s, text)
            cell["verdict"] = C.check_derivative(f, F, random.Random(r["id"]))
        except Exception as e:
            cell["verdict"] = "unparsed"
            cell["why"] = type(e).__name__
json.dump(rows, open("verified.json", "w"))
for s in ("sympy", "maxima", "giac"):
    print(s, dict(collections.Counter(r[s]["verdict"] for r in rows)))
for r in rows:
    flag = {s: r[s]["verdict"] for s in ("sympy", "maxima", "giac") if r[s]["verdict"] in ("wrong", "branch", "unparsed", "inconclusive")}
    if flag:
        print(r["id"], r["integrand"][:55], flag)
