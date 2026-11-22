# Symbolic Integration Cross-Check

Noah Parsons, as of 21 November 2026

## Question

How often do computer algebra systems return a wrong antiderivative, as opposed to giving up? When a system answers, the answer is usually trusted. This study tests each answer with independent checks.

## Systems

- SymPy 1.14.0
- Maxima 5.46.0 (the Ubuntu 24.04 package)
- Giac 1.9.0

## Method (`crosscheck.py`)

**Integrands.** There are 700 in all, run in two batches:
- 50 hand-picked classic integrands;
- 650 random compositions of elementary functions (seeds stored in the results).

Each system has 20 seconds per integrand.

**Checks.** Every answer is tested two ways.
1. **Derivative oracle.** The returned antiderivative is differentiated and compared with the integrand at random points, in 40-digit arithmetic. An answer is marked **wrong** when the two differ at every point. A constant of integration can't do that.
2. **Quadrature oracle,** for anything flagged. F(b) − F(a) is compared with mpmath quadrature of the integrand on several intervals. Each flagged result was also re-evaluated **inside the system that produced it** (Maxima's own `float`, Giac's own `evalf`). That rules out errors from translating its output into SymPy.

Answers returned unevaluated, timing out or not parseable are recorded as such, not as errors. SymPy answers in hypergeometric or piecewise form that the first parser could not read were re-parsed and checked separately (`sympy_unparsed_recheck.json`).

## Results

| | Answered and correct | Wrong | Gave up (unevaluated) | Timed out |
|---|---|---|---|---|
| SymPy | 444 (+2 discontinuous, see below) | **0** | 192 | 60 |
| Maxima | 485 | **4** | 209 | 2 |
| Giac | 496 | **1** | 198 | 0 |

Each row covers all 700 integrands, once a few unparseable answers are counted: 2 for SymPy and 5 for Giac, two of which are Giac's own error messages.

### Maxima 5.46.0: ∫ sin(xⁿ) dx and ∫ cos(xⁿ) dx are wrong for every odd n

Maxima answers these in terms of `gamma_incomplete` with imaginary arguments. For even n the result is right. For odd n, the definite integral it gives, evaluated by Maxima itself, is wrong. On [0.3, 1.1]:

| Integrand | Maxima's F(1.1) − F(0.3) | Quadrature |
|---|---|---|
| cos(x³) | 0.0280 | 0.6715 |
| cos(x⁴) | 0.6808 | 0.6808 |
| cos(x⁵) | −0.0084 | 0.6842 |
| cos(x⁶) | 0.6841 | 0.6841 |
| cos(x⁷) | −0.0124 | 0.6817 |
| sin(x³) | 0.3715 | 0.3231 |
| sin(x⁴) | 0.2802 | 0.2802 |
| sin(x⁵) | 0.2250 | 0.2509 |
| sin(x⁶) | 0.2296 | 0.2296 |
| sin(x⁷) | 0.1584 | 0.2130 |

For cos(x³), a correct antiderivative in the same functions is −(x/6)[(ix³)^(−1/3) Γ(1/3, ix³) + (−ix³)^(−1/3) Γ(1/3, −ix³)]. It matches quadrature to 16 digits. SymPy's answer (a hypergeometric function) is also correct.

The fourth Maxima error, x² exp(x^(5/2)), is a branch problem. Maxima's answer, −(2/5) Γ(6/5, −x^(5/2)), is right only if the fifth root of a negative number is taken to be real. Maxima itself evaluates it on the principal branch and returns a complex number (−0.304 − 0.221i on [0.2, 0.9]) for a real integral of 0.375.

### Giac 1.9.0: one sign error on the same integrand

For x² exp(x^(5/2)), Giac returns (2/5)·igamma(6/5, −x^(5/2)). Its own `evalf` gives −0.375 on [0.2, 0.9], where the true value is +0.375. This is the same branch issue as Maxima's, landing on the opposite sign.

### SymPy: no wrong answers

The only flags are ∫ 1/(2 + cos x) and ∫ 1/(sin x + cos x + 2). SymPy's antiderivatives are correct between the jumps of tan(x/2) but discontinuous across them, a well-known and documented behaviour of SymPy.

## Before reporting

- **The Maxima odd-exponent error** is the clear finding. Check it on the current Maxima release, since 5.46.0 is from 2022, and search Maxima's bug tracker before filing. Related `gamma_incomplete` integration problems were discussed on the Maxima mailing list in 2012.
- **The Giac sign error** should likewise be checked on a current Giac.

## Files

| File | Contents |
|---|---|
| `crosscheck.py` | Corpus, the three systems, both oracles |
| `results.jsonl`, `verified.json` | Batch 1 (50 hand-picked and 150 random), re-verified |
| `results2.jsonl` | Batch 2 (500 random) |
| `sympy_unparsed_recheck.json` | Re-check of SymPy's hypergeometric and piecewise answers |
| `reverify.py` | Re-runs the oracle on stored results without calling the systems |
