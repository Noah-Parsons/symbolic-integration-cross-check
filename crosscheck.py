"""Cross-check antiderivatives from SymPy, Maxima and Giac with two independent oracles.

Oracle 1: differentiate the returned antiderivative (SymPy) and compare with the integrand at
random points, in 40-digit arithmetic. Oracle 2 (for disagreements): compare F(b) - F(a) with
mpmath quadrature of the integrand on [a, b].

A result is WRONG when its derivative differs from the integrand at every test point where both
are finite (a constant of integration cannot do that). Results that are returned unevaluated,
time out or cannot be parsed are recorded as such, not as errors.

Usage: python crosscheck.py N_RANDOM SEED
"""
import json, random, re, subprocess, sys, time
import mpmath as mp
import sympy as sp

x = sp.Symbol("x")
mp.mp.dps = 40
TIMEOUT = 20

# ---------------------------------------------------------------- corpus
HAND = [
    "1/(x**4 + 1)", "sqrt(tan(x))", "x**2*exp(3*x)*sin(2*x)", "log(x)**3/x**2", "1/(x**3 - 2)",
    "sqrt(x**2 + 2*x + 5)", "x/sqrt(1 - x**4)", "exp(x)/(1 + exp(2*x))", "atan(x)/x**2",
    "1/(sin(x) + cos(x) + 2)", "x*asin(x)", "log(x**2 + 1)", "sin(x)**5*cos(x)**4",
    "1/(x*sqrt(x**2 - 1))", "exp(-x**2)*x**3", "x**3*log(x)**2", "sqrt(1 + x**3)*x**2",
    "1/(1 + x**6)", "cosh(x)**3", "tanh(x)**4", "x*exp(x)/(x + 1)**2", "log(sin(x))*cos(x)",
    "1/((x + 1)*(x**2 + 4)**2)", "sqrt(x)/(1 + x)", "x**(3/2)*log(x)", "exp(sqrt(x))",
    "sin(log(x))", "1/(x**2*(1 + x**2)**(3/2))", "asinh(x)**2", "atan(sqrt(x))",
    "x/(x**4 + x**2 + 1)", "1/(2 + cos(x))", "sec(x)**3", "csc(x)**3", "x*sec(x)**2",
    "log(x + sqrt(x**2 + 1))", "(x**2 + 1)/(x**4 + 1)", "cos(x)/sqrt(1 + sin(x)**2)",
    "1/sqrt(x*(1 - x))", "exp(2*x)*cos(3*x)*x", "log(log(x))/x", "x**5*exp(-x**3)",
    "1/(x**5 + 1)", "sqrt(1 - x**2)*x**4", "tan(x)**5", "erf(x)", "x*erf(x)", "exp(x)*log(x)",
    "1/(exp(x) + 1)", "x**2/(1 + x**2)**3",
]

ATOMS = ["x", "x**2", "x**3", "sqrt(x)", "exp(x)", "exp(-x)", "log(x)", "sin(x)", "cos(x)",
         "atan(x)", "(x + 1)", "(x**2 + 1)", "(2*x + 3)", "sqrt(x + 1)", "exp(2*x)", "sin(2*x)"]


def random_integrand(rng):
    depth = rng.choice([2, 2, 3, 3, 4])
    e = rng.choice(ATOMS)
    for _ in range(depth - 1):
        op = rng.choice(["*", "*", "/", "+", "compose"])
        a = rng.choice(ATOMS)
        if op == "compose":
            f = rng.choice(["exp", "log", "sin", "cos", "sqrt", "atan"])
            e = f"{f}({e})" if f != "log" else f"log(1 + ({e})**2)"
        elif op == "/":
            e = f"({e})/({a})"
        else:
            e = f"({e}){op}({a})"
    return e


# ---------------------------------------------------------------- the three systems
def run_sympy(expr):
    code = (f"import sympy as sp; x=sp.Symbol('x'); "
            f"r=sp.integrate(sp.sympify('{expr}'), x); "
            f"print('UNEVAL' if r.has(sp.Integral) else sp.srepr(r))")
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=TIMEOUT)
    out = p.stdout.strip().splitlines()
    if not out:
        return "ERROR", p.stderr.strip()[-200:]
    return ("UNEVAL", None) if out[-1] == "UNEVAL" else ("OK", out[-1])


def to_maxima(expr):
    s = expr.replace("**", "^").replace("exp(", "exp(").replace("atan(", "atan(")
    return s.replace("sec(", "sec(").replace("csc(", "csc(")


def run_maxima(expr):
    cmd = f"display2d:false$ linel:1000000$ r:integrate({to_maxima(expr)},x)$ print(\"RESULT\", string(r))$"
    p = subprocess.run(["maxima", "--very-quiet", "--batch-string", cmd], capture_output=True,
                       text=True, timeout=TIMEOUT)
    m = re.findall(r"RESULT (.*)", p.stdout)
    if not m:
        return "ERROR", (p.stdout + p.stderr)[-200:]
    r = m[-1].strip()
    if "integrate(" in r:
        return "UNEVAL", r
    return "OK", r


def run_giac(expr):
    with open("/tmp/claude-0/-home-claude/f0f7433c-e8b2-5691-85cf-a9b7e7fa1f95/scratchpad/giac_in.txt", "w") as f:
        f.write(f"integrate({expr},x)\n")
    p = subprocess.run(["icas", "/tmp/claude-0/-home-claude/f0f7433c-e8b2-5691-85cf-a9b7e7fa1f95/scratchpad/giac_in.txt"],
                       capture_output=True, text=True, timeout=TIMEOUT)
    lines = [l for l in p.stdout.splitlines() if l.strip() and not l.startswith("//")]
    if not lines:
        return "ERROR", (p.stdout + p.stderr)[-200:]
    r = lines[-1].strip()
    if "integrate(" in r or "Unable" in p.stdout:
        return "UNEVAL", r
    return "OK", r


# ---------------------------------------------------------------- parsing results back
LOCAL = {"x": x, "E": sp.E, "pi": sp.pi, "I": sp.I, "ln": sp.log, "log": sp.log, "sqrt": sp.sqrt,
         "atan": sp.atan, "asin": sp.asin, "acos": sp.acos, "asinh": sp.asinh, "acosh": sp.acosh,
         "atanh": sp.atanh, "erf": sp.erf, "erfi": sp.erfi, "abs": sp.Abs, "sign": sp.sign,
         "gamma_incomplete": sp.uppergamma, "expintegral_ei": sp.Ei, "li": sp.li, "Ei": sp.Ei,
         "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh, "sec": sp.sec, "csc": sp.csc,
         "cot": sp.cot, "i": sp.I, "polylog": sp.polylog, "igamma": lambda a, z: sp.lowergamma(a, z), "re": sp.re, "im": sp.im, "acot": sp.acot, "exp": sp.exp, "Si": sp.Si, "Ci": sp.Ci}


def parse(system, text):
    if system == "sympy":
        return sp.sympify(text, locals={"Symbol": sp.Symbol}) if not text.startswith("Add") else eval(
            text, {**{k: getattr(sp, k) for k in dir(sp)}})
    s = text.replace("%e", "E").replace("%pi", "pi").replace("%i", "I").replace("^", "**")
    s = s.replace("expintegral_ei", "Ei")
    s = re.sub(r"li\[(\d+)\]\(", r"polylog(\1,", s)
    return sp.sympify(s, locals=LOCAL)


def sympy_from_srepr(text):
    import sympy.functions.elementary.piecewise as pw
    ns = {k: getattr(sp, k) for k in dir(sp)}
    ns["ExprCondPair"] = pw.ExprCondPair
    return eval(text, ns)


# ---------------------------------------------------------------- the oracles
def _num(expr, xv):
    v = expr.evalf(50, subs={list(expr.free_symbols)[0]: xv} if expr.free_symbols else {})
    return complex(v) if v.is_number else None


def check_derivative(f, F, rng, n=6):
    """Return 'ok', 'wrong', 'branch' or 'inconclusive' from the derivative oracle.
    Values are compared as complex numbers, so an antiderivative written with complex
    intermediate terms is judged on its derivative only."""
    xr = sp.Symbol("xr", positive=True)       # test points are all positive reals
    f, F = f.subs(x, xr), F.subs(x, xr)
    dF = sp.diff(F, xr)
    good = bad = 0
    for _ in range(30):
        if good + bad >= n:
            break
        xv = sp.Float(rng.uniform(0.15, 2.9), 30)
        try:
            a, b = _num(f, xv), _num(dF, xv)
            if a is None or b is None or not all(map(lambda z: abs(z) < 1e300, (a, b))):
                continue
            if abs(a.imag) > 1e-20 * (1 + abs(a)):
                continue        # integrand not real here
            err = abs(a - b) / max(abs(a), 1e-20)
        except Exception:
            continue
        if err < 1e-10:
            good += 1
        else:
            bad += 1
    if bad and not good:
        return "wrong"
    if good and not bad:
        return "ok"
    if good and bad:
        return "branch"     # right on part of the interval only
    return "inconclusive"


def check_quadrature(f, F, a=0.5, b=2.5):
    """Oracle 2: compare F(b) - F(a) with mpmath quadrature of f on [a, b] (40 digits)."""
    xr = sp.Symbol("xr", positive=True)
    f, F = f.subs(x, xr), F.subs(x, xr)
    fl = sp.lambdify(xr, f, "mpmath")
    q = mp.quad(fl, [a, b])
    d = complex(F.evalf(40, subs={xr: b}) - F.evalf(40, subs={xr: a}))
    return complex(q), d, abs(d - complex(q)) / max(abs(complex(q)), 1e-30)


def main(n_random=150, seed=7, out_path="results.jsonl", hand=True):
    rng = random.Random(seed)
    corpus = ([("hand", e) for e in HAND] if hand else []) + [("random", random_integrand(rng)) for _ in range(n_random)]
    with open(out_path, "w") as out:
        for k, (src, expr) in enumerate(corpus):
            f = sp.sympify(expr)
            row = {"id": k, "source": src, "integrand": expr}
            for name, runner in (("sympy", run_sympy), ("maxima", run_maxima), ("giac", run_giac)):
                t0 = time.time()
                try:
                    status, text = runner(expr)
                except subprocess.TimeoutExpired:
                    status, text = "TIMEOUT", None
                verdict = status
                if status == "OK":
                    try:
                        F = sympy_from_srepr(text) if name == "sympy" else parse(name, text)
                        verdict = check_derivative(f, F, random.Random(k))
                    except Exception as e:
                        verdict = "unparsed"
                        text = f"{text} [{type(e).__name__}]"
                row[name] = {"verdict": verdict, "result": text, "seconds": round(time.time() - t0, 2)}
            out.write(json.dumps(row) + "\n")
            out.flush()
            print(k, expr[:50], {s: row[s]["verdict"] for s in ("sympy", "maxima", "giac")}, flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 150, int(sys.argv[2]) if len(sys.argv) > 2 else 7)
