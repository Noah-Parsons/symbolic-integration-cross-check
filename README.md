# P09 — Symbolic integration cross-check

**Field:** Software verification  
**Size:** Medium (one project season)  
**Time:** 6-8 weeks

## Question
How often do SymPy, Maxima and Giac return wrong antiderivatives or definite integrals, and do they disagree?

## Why it matters
Symbolic results feel trustworthy. Checking by differentiating back and by numeric quadrature gives two independent oracles.

## Builds on
MechanicsDSL's dependence on SymPy

## Method
1. Build an integrand corpus (textbook tables + random generation)
2. Verify antiderivatives by symbolic differentiation and by mpmath quadrature at random points
3. Classify errors: branch cuts, dropped conditions, outright wrong

## Deliverable
Report + corpus; issues for confirmed bugs.

## Risks
Branch-cut 'errors' are often conventions, so define correctness first.

## Before you start: novelty check
Search Google Scholar / arXiv / GitHub for: _computer algebra integration bugs testing; Rubi test suite_. If the question is already answered, narrow it or pick another project.

## Possible outlet
ISSAC poster; ACM Communications in Computer Algebra

## Log
_(dates, decisions, results)_
