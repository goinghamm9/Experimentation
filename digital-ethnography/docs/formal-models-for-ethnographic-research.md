# Formal Models for Ethnographic Research

*Organized around Arthur Stinchcombe's* Constructing Social Theories *(1968), with the ethnographic canon mapped to its formal counterparts.*

Three layers, and they need different math:

- **Theory construction** (§0) — what kind of causal claim you are making, and what would discriminate it from its rivals. Stinchcombe's layer. Determines which of the models below is even applicable.
- **Research process** (§1–§3, §6) — how many informants, whose voices, when to stop, how much to trust a coder.
- **Cultural system and causal inference** (§4–§9) — what structure is recovered: shared knowledge, salience, semantic space, configurational causes, decision rules.

Notation: `N` informants, `M` items, `K` latent themes, `n` interviews completed.

---

## Contents

| § | Section | Core question |
|---|---|---|
| 0 | The Stinchcombe Layer | What kind of causal claim is this? |
| 1 | Sampling and Saturation | How much fieldwork, and when do I stop? |
| 2 | Shared Knowledge and Competence | Who knows what, and is there one culture? |
| 3 | Reliability of Coding | Can the coding be trusted, and where do I spend? |
| 4 | Structure from Elicitation | Does the domain have structure? |
| 5 | Behavior, Time, and Sequence | What do people actually do, in what order? |
| 6 | Networks, Structure, and Access | Who did I reach, and what is the social structure? |
| 7 | Case-Based Causal Inference | What caused the outcome, across few cases? |
| 8 | Triangulation, Observer, Decisions | Is the corroboration real? |
| 9 | The Iterative Process Itself | Is the coding scheme converging? |
| 10 | GT Under Pre-Specification | How does this survive contact with instrumented systems? |
| 11 | Risk, Tails, and Fragility | What is the exposure, and what am I not seeing? |
| 12 | Pattern Recognition and Drift | What breaks when this is automated? |
| 13 | Insight → Quant → Decision | What is any of this worth? |
| 14 | Blockmodeling and Community Structure | What is the role system, and what are the nodes? |
| 15 | Linguistic Anthropology | What does the talk itself encode? |
| 16 | The Anthropological Tradition | What does the discipline proper contribute? |
| 17 | The Case for Qualitative Research | Why is any of this necessary? |
| 18 | Commercial Landscape | Does this already exist, and what sells? |

---

## 0. The Stinchcombe Layer: What the Math Is For

Stinchcombe was not an ethnographer, and *Constructing Social Theories* is not a fieldwork manual. Its relevance is that it specifies what turns observation into theory — and it does so in a way that is directly formalizable. His later *The Logic of Social Research* (2005) makes the ethnographic case explicitly: each method has a distinctive comparative advantage, and ethnography's is the direct observation of **mechanism in context**, which is precisely the ingredient the other methods have to assume.

### 0.1 A theory is a generator of many implications

Stinchcombe's central discipline: a theory worth having produces a large number of *independent* observable consequences, and you should be able to name at least three plausible explanations for any correlation you care about before you start.

Formally, maintain a model set `{T₁, T₂, T₃, …}` with priors `P(T_k)`. Field evidence updates them:

```
P(T_k | e) ∝ P(e | T_k) · P(T_k)
```

If a theory survives `m` genuinely independent tests, each of size `α`, the probability a false version survives all of them is roughly `α^m` — evidentiary strength grows exponentially in the number of independent implications, and not at all in repeated confirmation of the same one. This is the same correlation problem as §8.1: `m` confirmations correlated at `ρ` are worth

```
m_eff = m / (1 + (m − 1)·ρ)
```

Ten interviews confirming the same implication are one test, not ten.

### 0.2 Crucial observation as maximal discrimination

Stinchcombe's "crucial experiment" logic gives fieldwork a selection rule. For a candidate observation `a` (this informant, that site, those records), with predictive distributions `p₁(y|a)` and `p₂(y|a)` under rival theories:

```
a* = argmax_a  [ D_KL(p₁ ‖ p₂) + D_KL(p₂ ‖ p₁) ]
```

Choose the observation the theories disagree about most. An observation both theories predict identically has zero evidential value regardless of how vivid it is. This is the theory-side complement to the value-of-information rule in §1.4, and it is what makes "theoretical sampling" a computation rather than an instinct.

### 0.3 Three causal structures, three formalisms

Stinchcombe's taxonomy matters operationally: each type of explanation requires a *different* kind of evidence, and ethnography is decisive for one of them and useless for another.

**(a) Demographic / rate explanations.** Aggregate change produced by composition rather than by any change in individuals:

```
dN_k/dt = Σ_j q_jk·N_j − Σ_j q_kj·N_k + b_k − d_k
```

Decompose an observed shift in a community-level proportion:

```
Δp̄ = Σ_g w_g·Δp_g   +   Σ_g p_g·Δw_g
      within-group change    composition change
```

**Fieldwork corollary:** before explaining a change in practice by a change in belief, rule out change in *who is present* — migration, cohort replacement, differential exit. The second term is the one ethnographers systematically forget, and it is the source of most spurious "the culture is shifting" claims.

**(b) Functional explanations.** Legitimate only as a closed causal loop with an observable selection mechanism. Stinchcombe's requirements — homeostatic variable `H`, structure `S`, tension, and a selection process `σ` — as a control system:

```
dH/dt = g(S, T)          structure maintains the homeostatic variable
dS/dt = σ(H* − H)        deviation feeds back onto the structure
```

The explanation holds only if the loop is stabilizing: linearized, `(∂g/∂S)·(∂σ/∂H) < 0`, with the Jacobian's eigenvalues having negative real parts. Where selection operates by differential retention of practices:

```
dx_i/dt = x_i·( f_i(x) − f̄(x) )
```

**Fieldwork corollary — and this is ethnography's strongest claim to necessity:** `σ` must be *exhibited*, not assumed. Sanctioning, exit, ridicule, reward, imitation — someone has to be seen doing it. A functional claim without an observed `σ` is teleology dressed as explanation. Quantitative work can rarely see `σ`; participant observation can.

**(c) Historicist explanations.** The phenomenon persists by self-reproduction, and the causes of origin differ from the causes of persistence:

```
P(X_{t+1} = x | X_t = x) → 1
```

Polya-urn dynamics (self-reinforcement) converge almost surely to a limit that depends on early draws — but the limit does not encode them:

```
I(X₀ ; X_∞)  →  small
```

**Fieldwork corollary:** origins are *not identifiable from the present state*. No amount of additional time in the field recovers them. A historicist claim requires archives, or cases caught at different stages of the same process. Recognizing that you are making a historicist claim tells you to stop interviewing and go to the records.

### 0.4 Concepts, indicators, and the theory of measurement

Stinchcombe's rule is that a concept earns its place by entering a causal statement, and that every indicator carries a theory of why it indicates. Formally this is the measurement model — §2.3 (IRT), §3 (reliability), §4 (elicitation). Coding schemes constructed without an explicit indicator theory produce §3.2's worst case: high coder-by-person variance that no amount of additional fieldwork can fix.

---

## 1. Sampling and Saturation

*Glaser & Strauss (theoretical sampling, saturation); Becker (quasi-statistics).*

### 1.1 Theme detection (binomial) — Becker's quasi-statistics

Becker's 1958 argument that participant observers should state the frequency and distribution of what they report, in numbers where possible. A theme held by proportion `p` is expressed by any given informant with probability `p`:

```
P(detect) = 1 − (1 − p)^n          n ≥ ln(α) / ln(1 − p)
```

To be 95% sure of catching anything held by ≥30% of the population: `n ≥ 8.4` → 9 interviews.

- **Breaks when:** informants are not exchangeable (usually). Stratify, then apply per stratum.
- **Also breaks when:** the theme is rare and consequential, or `p` is non-stationary. This is a thin-tailed formula; see §11.3 for the rule of three and the correct reply to "we never observed it."

### 1.2 The discovery curve

```
E[D_n] = Σ_k [1 − (1 − p_k)^n]
E[D_{n+1}] − E[D_n] = Σ_k p_k·(1 − p_k)^n
```

Concave and monotonically decreasing — saturation is asymptotic, never reached. Empirically `D_n ≈ α·n^β` with `β < 1` (Heaps' law); fit `β` from your own accumulation data to project remaining yield.

### 1.3 Saturation as a species-richness problem

Themes as species, interviews as effort. With `f₁` themes seen exactly once, `f₂` seen twice, `D` seen so far:

```
Good–Turing unseen mass:   P₀ ≈ f₁ / n
Chao1 richness:            K̂ = D + f₁²/(2·f₂)
bias-corrected:            K̂ = D + f₁(f₁−1) / (2(f₂+1))
```

- **Buys you:** saturation as an auditable number. "We stopped at `f₁/n = 0.04` with Chao1 projecting 3 unobserved themes" is a claim; "no new themes emerged" is an assertion.
- **Breaks when:** coding granularity drifts mid-study — splitting a code inflates `f₁` and fakes non-saturation.

### 1.4 Three different sampling objectives (do not mix them)

The canon contains three incompatible sampling rules, each optimal for a different goal. Stating which one you are running resolves most methodological arguments before they start.

| Rule | Source | Objective |
|---|---|---|
| Representative sampling | survey tradition | minimize `Var(θ̂)` |
| Theoretical sampling | Glaser & Strauss | maximize `E[new categories]` = §1.2 marginal yield |
| Extended case selection | Burawoy | maximize expected surprise under the incumbent theory, `E[ −log p_{T₀}(y \| c) ]` |

And the stopping rule, in value-of-information form:

```
EVSI(a) = E_{y~p(y|a)}[ max_d U(d,y) ] − max_d E[U(d)] − c(a)
```

Stop when `EVSI(a) ≤ 0` for every available `a`. Combined with §0.2, this usually says a *new site* beats six more interviews at the current one — a new site moves the model-set posterior; a redundant informant does not.

---

## 2. Shared Knowledge and Competence

*Romney, Weller & Batchelder; D'Andrade; Dressler.*

### 2.1 Cultural Consensus Theory — General Condorcet Model

Recovers the "right answers" with no answer key, by exploiting the fact that competent informants agree with each other more. Latent key `Z_m ∈ {0,1}`, competence `D_i ∈ [0,1]`, guessing bias `g`:

```
P(X_im = 1) = D_i·Z_m + (1 − D_i)·g
```

With `g = 1/2`, two informants match on an item with probability `(1 + D_i·D_j)/2`, so the guessing-corrected agreement matrix is **rank one**:

```
M*_ij = 2·M_ij − 1 = D_i · D_j
```

**Test for a single culture:** eigendecompose the corrected agreement matrix. `λ₁/λ₂ ≥ 3` supports one shared domain; competences are the first-eigenvector loadings. Large `λ₂` means subcultures — fit a mixture rather than averaging across a fracture line.

**Recovering the key** — exact Bayesian aggregation is competence-weighted voting:

```
logit P(Z_m = 1) = logit(prior) + Σ_i (2·x_im − 1)·ln[ (1 + D_i) / (1 − D_i) ]
```

Five informants at `D ≈ 0.8` beat fifty at `D ≈ 0.2`. This is the formal warrant for the ethnographer's key-informant instinct.

### 2.2 Cultural consonance (Dressler)

```
C_i = ⟨b_i , z⟩ / ‖z‖₁
```

Fit between an individual's behavior vector and the consensus prototype — the bridge from an ethnographic construct to a regression covariate predicting health, stress, status.

### 2.3 Competence as latent trait (2PL IRT)

```
P(x_im = 1 | θ_i) = 1 / (1 + exp(−a_m(θ_i − b_m)))
```

Separates item difficulty `b_m` and discrimination `a_m` from informant ability `θ_i`. Identifies which *items* diagnose cultural expertise — often the study's most interesting finding.

---

## 3. Reliability of Coding

*Krippendorff; Cronbach's generalizability theory.*

```
Cohen's κ = (p_o − p_e) / (1 − p_e)
Krippendorff's α = 1 − D_o / D_e
```

Use `α`: any number of coders, missing data, any measurement level via a chosen difference function `δ`.

**Generalizability theory** — the model that tells you where to spend. Decomposing over persons `p`, items `i`, coders `c`:

```
X_pic = μ + ν_p + ν_i + ν_c + ν_pi + ν_pc + ν_ic + ν_pic,e
σ²_δ = σ²_pi/n_i + σ²_pc/n_c + σ²_pic/(n_i·n_c)
ρ²  = σ²_p / (σ²_p + σ²_δ)
```

Compare `σ²_pc` against `σ²_pi`. If coder-by-person variance dominates, more informants will not help — the instrument is the problem, which sends you back to §0.4.

---

## 4. Recovering Structure from Elicitation

*Bernard, Weller, Romney (systematic data collection); Bourdieu (correspondence analysis).*

### 4.1 Free-list salience

```
Smith's S_j = (1/N)·Σ_i (L_i − R_ij + 1) / L_i        (0 if unlisted)
Sutrop's S  = F / (N · mP)
```

### 4.2 Pile sorts, fields, and geometry

Co-occurrence gives proximities `δ_ij`; non-metric MDS minimizes Kruskal stress-1:

```
σ₁ = sqrt( Σ_{i<j}(d_ij − d̂_ij)² / Σ_{i<j} d_ij² )
```

Stress below ~0.10 in two dimensions is a usable cognitive map. Note that Bourdieu's *field* is not a metaphor but a method: *Distinction* is built on multiple correspondence analysis, the SVD of a chi-square-standardized indicator matrix. If you are claiming a field with positions and oppositions, MCA is the formal statement of that claim and it is testable.

### 4.3 Topic models over field text

```
LDA:  θ_d ~ Dir(α)   z_dn ~ Cat(θ_d)   w_dn ~ Cat(φ_{z_dn})   φ_k ~ Dir(β)
STM:  θ_d ~ LogisticNormal(X_d·Γ , Σ)          covariates on topic prevalence
PMI:  PMI(a,b) = log[ p(a,b) / (p(a)·p(b)) ]   semantic network edges
```

Use STM: it lets site, role, tenure, and gender enter prevalence directly. Treat divergence between machine topics and hand codes as a finding to explain, not an error to correct.

---

## 5. Behavior, Time, and Sequence

*Malinowski (the texture of everyday life); Gross & Johnson (spot sampling); Goffman (frames); Turner (social drama); Abbott (sequence); Sacks (turn-taking).*

### 5.1 Random spot / scan sampling

Malinowski's charting of daily life, made estimable. For an activity occupying true time proportion `π`, with `K` randomized instantaneous observations:

```
π̂ = k/K       Var(π̂) = π(1 − π)/K       K ≥ z²·π(1 − π)/d²
```

At `π = 0.2`, `d = 0.05`: `K ≈ 246` observations per person. This number decides whether a time-allocation claim is real.

### 5.2 Latent regimes (Goffman's frames, formalized)

Frame shifts are unobserved state changes governing observed behavior — a hidden Markov model:

```
P(O, S | λ) = π_{s₁}·b_{s₁}(o₁) · Π_t a_{s_{t−1}s_t}·b_{s_t}(o_t)
```

Estimating `a` and `b` turns "they switched register" into a decodable state path with a likelihood.

### 5.3 Turner's social drama as a semi-Markov process

The four-phase model — breach → crisis → redress → reintegration *or* schism — is a state machine with two absorbing outcomes. Add phase-duration distributions and it makes predictions: e.g., hazard of schism as a function of redress duration.

```
states {normal, breach, crisis, redress} → {reintegration, schism}
```

Estimate transition hazards across repeated dramas within a community. This converts a descriptive typology into something falsifiable.

### 5.4 Abbott's sequence analysis

Distance between two trajectories (careers, rituals, life courses) via optimal matching — Levenshtein edit distance with substitution costs `s(a,b)` and indel cost `c` — then cluster the distance matrix to recover typical trajectories.

```
d(A,B) = min over edit paths of Σ costs
```

- **Critical caveat:** results are driven by the cost matrix. Derive substitution costs from observed transition rates, `s(a,b) = 2 − p(a|b) − p(b|a)`, rather than setting them by hand.

### 5.5 Sequential organization of talk (Sacks)

Adjacency-pair structure as sequential dependence in turn types:

```
λ(b|a) = p(b|a) / p(b)
```

Values far from 1 identify the sequentially organized pairs conversation analysis works from, and give a base rate against which "this response was notable" can be tested.

---

## 6. Networks, Structure, and Access

*Gluckman and the Manchester School; Harrison White; Heckathorn; Duneier.*

### 6.1 Who you actually reached

Chain referral is a random walk on the social graph; a simple random walk's stationary distribution is proportional to degree, so raw snowball samples over-represent the well-connected — Duneier's objection to the "inconvenience sample," with a correction:

```
P̂_A = ( Σ_{i∈A} 1/d_i ) / ( Σ_{i∈S} 1/d_i )
```

Assumptions: reciprocal ties, sampling with replacement, accurate self-reported degree, and enough chain length to mix. Mixing is governed by the second eigenvalue `λ₂`; under strong homophily `λ₂ → 1` and the sample never leaves the first cluster no matter how large it gets.

### 6.2 Structure as blockmodel (White)

Structural equivalence: actors are equivalent when their tie profiles match. Measure by correlating rows/columns of the adjacency matrix; CONCOR iterates the correlation to convergence; the blockmodel is a partition plus an image matrix of block densities, assessed by fit against observed density.

```
i ≈ j  ⟺  corr( A_i· , A_j· ) ≈ 1     (structural)
regular equivalence: equivalent actors relate equivalently to equivalent others
```

This is the formal content of "social structure" as Manchester-school ethnography used the term — role systems rather than individual attributes.

---

## 7. Case-Based Causal Inference

*Ragin (QCA); Mackie (INUS); Mitchell and Yin (analytic inference); Burawoy (extended case); Van Evera and Bayesian process tracing.*

This is the section that connects §0's causal structures to actual fieldwork, and the one most often missing from ethnographic method texts.

### 7.1 Fuzzy-set QCA

Set membership `x_i, y_i ∈ [0,1]`. Sufficiency of `X` for `Y`:

```
Consistency:  Cons(X ⇒ Y) = Σ_i min(x_i, y_i) / Σ_i x_i
Coverage:     Cov(X ⇒ Y)  = Σ_i min(x_i, y_i) / Σ_i y_i
Necessity:    Cons(X ⇐ Y) = Σ_i min(x_i, y_i) / Σ_i y_i
```

Conventional benchmark: consistency ≥ 0.80 for a sufficiency claim; coverage measures empirical importance. With `k` conditions the truth table has `2^k` rows; sparse cases leave logical remainders; Boolean minimization (Quine–McCluskey) reduces surviving rows to prime implicants.

This delivers **conjunctural causation** (conditions matter in combination), **equifinality** (several distinct paths to the same outcome), and **asymmetry** (the causes of absence differ from the causes of presence) — all three of which are what ethnographers usually mean by causal claims and none of which survive a regression's net-effects framing.

**Mackie's INUS condition** is the underlying logic: a cause is typically an *insufficient but necessary part of an unnecessary but sufficient* configuration. That is the precise formal statement of "it mattered, in that context, together with those other things."

- **Honest caveat:** QCA results are sensitive to calibration thresholds and consistency cutoffs, and this fragility is a live methodological dispute. Report sensitivity across plausible calibrations or the result is not credible.

### 7.2 Bayesian process tracing

For a single case, evidence updates the odds directly:

```
posterior odds = prior odds × P(e | H) / P(e | ¬H)
```

Van Evera's test types are just regions of that likelihood ratio:

| Test | `P(e\|H)` | `P(e\|¬H)` | Consequence |
|---|---|---|---|
| Hoop | high | high | failing kills `H`; passing is weak |
| Smoking gun | moderate | very low | passing strongly confirms; failing is weak |
| Doubly decisive | high | very low | decisive either way |
| Straw in the wind | moderate | moderate | weak both ways |

Design fieldwork to look for smoking guns and hoops, not for confirmations — this is §0.2 applied at the level of a single observation.

### 7.3 What a case licenses (Mitchell, Yin)

Case-based fieldwork updates a distribution over *mechanisms*, not over *population parameters*:

```
strong:  P(M₁ | e) / P(M₂ | e)     — likelihood ratios can be extreme at n = 1
weak:    P(θ | e)                  — prevalence, nearly uninformative at n = 1
```

Analytic (not enumerative) generalization. A single case can annihilate a mechanism that predicts something that demonstrably did not happen, while saying essentially nothing about how common anything is. Claiming the second from the first is the standard overreach.

### 7.4 Burawoy's extended case method

Reconstruct existing theory by hunting anomalies. Case selection maximizes expected surprisal under the incumbent theory:

```
c* = argmax_c  E[ −log p_{T₀}(y | c) ]
```

Then build `T₁ ⊇ T₀` that accommodates the anomaly while preserving `T₀`'s prior successes — a constrained model-revision problem, and the exact opposite objective from representative sampling (§1.4). Note the tension with grounded theory: Burawoy starts from theory and seeks its failure; Glaser & Strauss suspend theory and seek emergence. These are different objective functions and a study should declare which it is optimizing.

---

## 8. Triangulation, the Observer, and Decision Models

### 8.1 Triangulation as evidence fusion

```
log[ P(H|e)/P(¬H|e) ] = log[ P(H)/P(¬H) ] + Σ_k log LR_k
```

Independence is load-bearing and usually false. Model a shared bias `b` — same faction, same gatekeeper, same framing: `e_k = H + b + ε_k`, sources correlated at `ρ`:

```
n_eff = k / (1 + (k − 1)·ρ)
```

At `ρ = 0.6`, five informants from one network are worth about 1.7 independent observations. The formal statement of why three interviews inside one clique are not triangulation — and, per §0.1, why three confirmations of one implication are not three tests. Under fat tails `n` is deflated a second time and independently; see §11.2.

### 8.2 Observer reactivity and habituation

The researcher's presence as a decaying treatment effect — the formal residue of the reflexivity literature (Charmaz, Burawoy):

```
Y_it = Y*_i + γ·exp(−λ·t) + ε_it
```

Fit `γ` (reactivity magnitude) and `1/λ` (habituation time constant) by regressing behavior on time-in-field. An empirical basis for discarding early observations rather than an arbitrary one.

### 8.3 Ethnographic decision models (Gladwin)

Deterministic decision trees induced from fieldwork and validated on held-out cases (benchmark: ≥85–90% predictive accuracy). Probabilistic generalization via random utility:

```
U_ij = V(x_ij ; β) + ε_ij     →     P(i picks j) = exp(V_ij) / Σ_k exp(V_ik)
```

Econometrics estimates `β`; only fieldwork can specify `x` and the choice set — which attributes people actually weigh, and which alternatives they actually consider.

---

## 9. The Iterative Process Itself

### 9.1 Constant comparison as fixed-point iteration

```
C_{t+1} = F(C_t , data_t)          terminate when ‖C_{t+1} − C_t‖ < ε
```

Saturation is the claim that `F` is a contraction with a stable fixed point. Stating it this way exposes the failure mode: if each new site materially rewrites the scheme, `F` is not contracting, and more fieldwork will not converge. That is a finding about the domain's heterogeneity — and, under §0.3(c), often a sign you are looking at a historicist process and need archives instead.

### 9.2 Becker's four stages, mapped

| Stage | Formal counterpart |
|---|---|
| 1. Selection and definition of problems, concepts, indices | §0.4, §4 |
| 2. Check on frequency and distribution (quasi-statistics) | §1.1, §1.3, §3 |
| 3. Incorporation into a model of the social system | §0.3, §6.2, §7.1 |
| 4. Final analysis and presentation of evidence | §8.1, transparency of `n_eff` |

---

## 10. Grounded Theory Under Pre-Specification: The Digital Ecosystem, 2026 and Beyond

Grounded theory says do not specify in advance. Quantitative work cannot proceed without specifying in advance. Instrumented digital systems make the advance specification *irreversible*. This section resolves the contradiction and states what follows for strategy.

### 10.1 The reconciliation: GT sets the support, pre-specification fixes the measure

They operate on different objects and only appear to conflict.

```
Grounded theory  →  constructs the hypothesis/measurement space  Θ, and σ(E)
Pre-specification →  fixes a measure over Θ and freezes the analysis map
```

You cannot estimate a parameter for a construct absent from `Θ`. The cost of an inadequate `Θ` is an irreducible misspecification floor:

```
bias_floor = min_{θ ∈ Θ} KL( p* ‖ p_θ )
```

No sample size reduces it. This is **Type III error** (Kimball, 1957): the precise answer to the wrong question. Pre-registration is a defense against Type I inflation and is entirely silent on Type III. Grounded theory is the Type III control. Stated that way, the two methods are complements with disjoint jobs, and the "emergence vs. forcing" argument is about sequencing, not about truth.

### 10.2 The forking-paths tax, and why discovery must be quarantined

If exploration and confirmation run on the same data with `m` implicit analytic paths:

```
α_eff ≈ 1 − (1 − α)^m
```

Split-sample discipline: allocate fraction `γ` of data to discovery, `1 − γ` to confirmation, and choose `γ` to maximize

```
P(correct construct discovered | γ·n)  ×  Power(confirm | (1 − γ)·n)
```

The first factor is §1.2's saturating discovery curve; the second is roughly monotone in `n`. Because discovery saturates and power does not, the optimum usually assigns a *small* fraction to discovery — but the cost of `γ = 0` is unbounded, since you then confirm the wrong construct with perfect rigor and full statistical propriety.

### 10.3 Abduction as the formal engine (Timmermans & Tavory)

Neither pure induction (Glaser) nor pure deduction. Using §0.1's model set, the trigger to expand is explicit:

```
if  max_k P(e | T_k) < τ   →   admit T_{k+1}
```

The generative analogue of open coding is a Chinese restaurant process: each new observation joins an existing category or opens a new one.

```
P(new category | n observed) = α / (α + n)
E[categories after n] ≈ α·ln(1 + n/α)
```

The concentration parameter `α` *is* the analyst's willingness to open a new code, now an explicit, tunable, reportable quantity rather than a temperament. Note that the expected-category curve is the same logarithmic shape as §1.2 — the two literatures have been describing the same object.

### 10.4 In digital systems, the schema is the question

The governing constraint, stated exactly:

```
A question Q is answerable from telemetry  ⟺  Q is measurable with respect to σ(E),
the sigma-algebra generated by the instrumented event set E.
```

Instrumentation freezes `σ(E)`. Un-logged dimensions cannot be backfilled — the information was never created. So **event taxonomy design is advance question framing performed under irreversibility**, which is the hardest version of the problem in §10.1 and the one most often handed to whoever is closest to the code.

Two consequences:

- The pre-instrumentation qualitative pass is not research overhead, it is schema insurance. The asymmetry is weeks of discovery against quarters of unanswerable questions.
- Instrument the dimensions that *discriminate rival explanations* (§0.2), not the events that are cheapest to emit. Most event schemas are optimized for ease of logging, which is orthogonal to evidential value.

### 10.5 Taxonomy drift as a monitored quantity

Run Good–Turing (§1.3) continuously over incoming unstructured streams — support tickets, call transcripts, session notes, reviews, churn reasons:

```
alert when  f₁ / n  exceeds τ and is rising
```

A rising singleton rate means reality has outgrown the codebook. Most organizations rebuild taxonomies on a calendar; this makes it event-driven, and it is the single most deployable idea in this document.

### 10.6 LLM judges are coders, and the whole of §2–§3 applies

The dominant measurement problem in generative systems is scoring outputs against rubrics that do not pre-exist. A rubric is a coding scheme; a judge is a coder. Therefore:

- **Krippendorff's α** across judges and humans, with `δ` matched to the scale (§3).
- **Generalizability theory** decomposing variance over prompts × items × judges (§3). This answers "add judges or add test cases?" — which is otherwise decided by vibes.
- **Cultural Consensus Theory** when there is no gold label (§2.1). The corrected agreement matrix should be rank one. `λ₁/λ₂ < 3` means the judges are applying two different rubrics — a finding about rubric ambiguity, not noise to average away. Competence weights then aggregate them correctly.
- **`n_eff` (§8.1).** Judges sharing a base model or a prompt lineage are correlated sources. Three judges from one model family are worth roughly one judge, and ensembling them produces confidence rather than evidence.

Grounded theory's role here is upstream and unavoidable: someone has to construct the rubric's categories from actual failure modes before anything can be scored. The rubric is a codebook, and it saturates or it doesn't (§1.3).

### 10.7 What follows strategically

Stated as consequences of the structure above, not as forecasts.

1. **The durable asset is the construct library, not the model or the dashboard.** Models turn over on a roughly annual cycle; validated definitions, their calibration data, and the `σ(E)` they presuppose do not. Whoever owns the ontology determines what can be asked downstream.
2. **Data minimization raises the return on knowing what to log.** As collection becomes more constrained by regulation and by cost, "log everything and decide later" stops being available — which increases, not decreases, the value of the discovery pass that precedes instrumentation.
3. **Signal proliferation is not evidence accumulation.** More tools reading the same clickstream are correlated sources; the honest count is `n_eff`, and it is close to 1.
4. **Contestable counter, stated fairly:** the construct-library moat weakens if general models become reliably able to induce serviceable taxonomies zero-shot from raw streams. The defensible version of the claim is narrower — the moat is in *validated, calibrated* constructs with known reliability properties and an audit trail, not in the category list itself, which is increasingly cheap to generate and always was cheap to guess.

---

## 11. Risk, Tails, and Fragility

Stripped of the rhetoric, Taleb's transferable contribution is four things: a **regime triage** that must run before any estimator is chosen, a **second deflation of effective sample size**, a formal account of **survivorship**, and — most useful here — a way to measure **fragility without knowing any probabilities**. Ethnography's epistemic situation (small `n`, a bounded observation window, a sample conditioned on survival) is precisely where each of these bites hardest.

### 11.1 Tail regime triage — the second triage, alongside §0.3

```
P(X > x) ~ L(x)·x^(−α)          moments of order ≥ α do not exist
α ≤ 2 → infinite variance;  α ≤ 1 → infinite mean
```

**Thin-tailed ethnographic quantities** — time-allocation proportions, agreement rates, list lengths, code frequencies. The machinery in §1–§5 applies as written.

**Fat-tailed ones** — conflict and violence intensity, wealth and landholding, network degree, organizational survival, migration and rumor cascades, attention, institutional collapse. Here the earlier machinery misleads, and the size of the error is not small.

Estimate the tail index by Hill or by fitting a Generalized Pareto to exceedances over a threshold `u`:

```
Hill:  α̂ = [ (1/k)·Σ_{i=1}^{k} ln( X_(i) / X_(k+1) ) ]^(−1)
GPD:   P(X > u+y | X > u) = (1 + ξ·y/β)^(−1/ξ)        ξ > 0 → heavy tail
```

Run this triage where you run §0.3's. Getting the causal structure right and the tail regime wrong still produces a confidently incorrect study.

### 11.2 Effective sample size, deflated twice

§8.1 deflates `n` for correlation. Tail thickness deflates it again, independently:

```
correlation:  n_eff = n / (1 + (n − 1)·ρ)
tail:         n_eff = n^( 2(α − 1)/α )          for 1 < α ≤ 2
```

At `α = 1.5`, one hundred observations carry the precision of about twenty-two. At `α = 1.2`, about five. As `α → 1`, no achievable `n` helps — the sample mean does not converge to anything useful, and reporting one is an error rather than an approximation.

**Correction this forces on §1:** the discovery curve and Chao1 assume a well-behaved abundance distribution. If theme prevalence is itself fat-tailed — a few themes ubiquitous, a long tail of rare consequential ones — saturation estimates are optimistic and the singleton rate `f₁/n` decays more slowly than the estimator implies.

### 11.3 The bounded window, and the correct reply to "we never saw it"

Fieldwork observes an interval. Under a power-law tail the expected worst case observed grows with looking time:

```
E[ max of n draws ] ~ n^(1/α)
```

At `α = 1.5`, doubling time in the field raises the expected worst-observed event by ~1.59×. The severity of the worst thing you witnessed is therefore substantially a fact about your fieldwork schedule, not about the community.

For non-observation, the rule of three: with zero occurrences in `n` independent observations, the 95% upper bound is

```
p ≤ 3 / n
```

Thirty interviews with no report of a practice leaves its prevalence plausibly as high as 10%. **This corrects §1.1**, whose detection formula assumes `p` is known and stationary — for rare, consequential, regime-dependent events neither holds, and the required `n` is far larger than that formula returns.

### 11.4 Silent evidence: the survivor-conditioned sample

Ethnography nearly always samples on survival — the community still there, the firm still trading, the practice still practiced, the informant still present and still willing. With survival probability `s(x)`:

```
p_obs(x) = p(x)·s(x) / ∫ p(u)·s(u) du
```

and the bias in any statistic has a clean closed form:

```
E_obs[g(X)] − E[g(X)] = Cov( g(X), s(X) ) / E[s(X)]
```

Anything positively correlated with survival is overestimated, by exactly that covariance. The immediate consequence for functional explanation (§0.3b): **adaptive-looking practices look more adaptive than they are**, because the cases where they failed are structurally absent from the field site. A homeostatic loop inferred only from survivors is close to unfalsifiable.

Remedy: sample the graveyard — defunct organizations, abandoned practices, out-migrants, refusals, closed sites. Either estimate `s(x)` or bound the covariance. This is also the honest reading of §6.1: non-response and attrition are `s(x)`, not nuisance.

### 11.5 Ergodicity: time average versus ensemble average

With multiplicative dynamics and an absorbing barrier, the average across people and the average over time for one person are different quantities:

```
ensemble:  E[X_T]
time:      g = E[ ln(X_{t+1}/X_t) ]        with  g ≤ ln(1 + E[r])   (Jensen)
survival:  P(survive T) = Π_t (1 − p_t) → 0   for any constant p > 0
```

**This is the most valuable single import for qualitative work on risk.** Behavior that reads as irrationally cautious under expected-value reasoning — livelihood diversification at a yield cost, levelling and redistributive institutions, fictive-kinship insurance, refusal of profitable but variance-increasing options, subsistence-first cropping — is *optimal* under time-average maximization with a ruin barrier. It replaces the deficit account ("they misunderstand probability") with a model in which the observed behavior is correct and the analyst's benchmark was wrong.

This is also where Taleb converges with an older ethnographic literature that got there first: Scott's moral economy and safety-first peasant, and the economic anthropology of risk-buffering. The formalism above is what that literature was describing.

**Modifies §8.3:** substitute geometric growth under a barrier for expected utility in the decision model, and Gladwin-style trees begin predicting choices that EV specifications systematically miss.

### 11.6 Fragility without probabilities — the best fit for qualitative work

The key move: concavity to a stressor is measurable even when the distribution is unknown.

```
fragile:      ∂²V/∂σ² < 0            antifragile:  ∂²V/∂σ² > 0
Jensen:       E[V(X)] < V(E[X])      for concave V
```

Detection by second difference — a pure stress test requiring no probabilities at all:

```
H(Δ) = V(x + Δ) + V(x − Δ) − 2·V(x)
H < 0 → fragile        H > 0 → antifragile        H ≈ 0 → robust
```

`V` is any outcome the community actually cares about — household food security, an institution's legitimacy, a workshop's throughput, a household's standing. `Δ` is a stressor you can pose counterfactually. **The asymmetry between the two answers is the measurement, and both answers are elicitable in an interview.** "What happens if the rains come two weeks late? What if they come two weeks early?" — if the harm from late exceeds the benefit from early, `H < 0` and the household is fragile to rainfall timing, with no frequency data required.

That property is why this is the strongest item in the section for ethnography specifically. It also states formally why average-case planning fails: for concave systems, point-estimate reasoning systematically overestimates outcomes.

### 11.7 Ruin, irreversibility, and where cost–benefit is inadmissible

```
reversible + local        → expected-value reasoning admissible
irreversible + systemic   → absorbing barrier; no EV tradeoff admissible
```

Because `Π(1 − p_t) → 0`, any recurring exposure with a nonzero ruin probability is eventually fatal regardless of favorable expected value. Note that §10.4's schema irreversibility is a small instance of the same structure — an absorbing decision, where the right posture is precautionary rather than optimizing.

### 11.8 What this framework does not give you

Stated plainly, because the material above is easy to over-apply.

- **Fat-tailedness is a domain claim, not a universal.** Many ethnographic quantities are genuinely thin-tailed and §1–§5 is correct for them. Reflexive Extremistan reasoning produces unfalsifiable caution, which is its own failure mode.
- **Tail exponents are badly estimated at small `n`.** The Hill estimator has substantial bias and variance, and is sensitive to threshold choice. There is real irony here: the framework argues you cannot learn tails from data, and its central parameter is learned from data. Carry `α` as a sensitivity range, never a point estimate.
- **The precautionary principle needs "systemic and irreversible" to have content.** Almost any action can be rhetorically framed as having a fat-tailed downside. That qualifier is where the entire argument lives, and it is more often asserted than demonstrated.
- **The strong non-ergodicity claim is contested.** That absorbing barriers change optimal policy is not seriously disputed and is enough for everything in §11.5; the further claim that this overturns expected-utility theory is a live argument, not a settled result.
- **Most of the surrounding apparatus adds no mathematics.** The transferable core is exactly five items: tail regime, effective `n`, survivorship, convexity, absorbing barriers.

---

## 12. Pattern Recognition, Drift, and the Agentic Instrument

An automated system searches a vastly larger hypothesis space, vastly faster, than the fieldworker this document was written for. Everything in §0–§11 is an apparatus for not fooling yourself; at machine speed that apparatus stops being quality control and becomes the primary architecture. This section supplies the pattern-recognition layer and the two pieces of Eric Weinstein's work that carry transferable formal content.

### 12.1 The governing constraint is the base rate

For any engine scanning for a low-prevalence signal:

```
PPV = (sens·π) / ( sens·π + (1 − spec)·(1 − π) )
```

At prevalence `π = 0.001` with sensitivity 0.95 and specificity 0.99, precision is **8.7%** — more than nine in ten flags are wrong, with an excellent-sounding classifier. Specificity, not sensitivity, is the binding constraint, and it has to be extraordinary before rare-signal detection is worth anything.

Two design consequences, both non-negotiable:

- **Raise `π` by pre-stratification rather than chasing specificity.** Scanning everything is the worst case of this formula. Scoping to a defensible subpopulation is worth more than any model improvement.
- **The output is a ranked queue, never a finding.** An engine at 8.7% precision is a triage instrument for human judgment. Anything that presents its output as a conclusion is misreporting its own error rate by an order of magnitude.

### 12.2 Signal versus noise in agreement matrices — Marchenko–Pastur

§2.1's `λ₁/λ₂ ≥ 3` is a rule of thumb. Random matrix theory replaces it with a theorem. For a `p × n` data matrix with noise variance `σ²` and aspect ratio `q = p/n`, the noise eigenvalues fall inside

```
λ± = σ²·(1 ± √q)²
```

Eigenvalues above `λ₊` are signal; everything in the bulk is sampling noise regardless of how suggestive it looks. This gives an honest count of how many consensus dimensions you actually have, applies unchanged to LLM-judge agreement matrices (§10.6), and rules out the standard failure of reading structure into the second and third eigenvectors of a small sample.

### 12.3 Apophenia scales with the search

Under the null, the largest of `m` sample correlations on `n` observations is approximately

```
max|r| ≈ √( 2·ln m / n )
```

With 200 variables, `m ≈ 20,000` pairs; at `n = 500` the expected largest spurious correlation is about 0.20 — publishable-looking, and entirely noise. An agent enumerating hypotheses drives `m` up by orders of magnitude, so §10.2's `α_eff ≈ 1 − (1 − α)^m` goes to 1.

**Requirement:** the agent must account for its own search space. Hypotheses considered must be counted and reported, and the discovery/confirmation split (§10.2) must be enforced by the architecture rather than by discipline. An agentic system that does not log `m` cannot state what any of its findings mean.

### 12.4 Distribution-free calibration

Given §11's world — unknown distribution, possibly fat tails, no reliable parametric form — the correct uncertainty layer is conformal prediction, which needs only exchangeability:

```
P( Y ∈ C(X) ) ≥ 1 − α
```

with weighted or adaptive variants under covariate shift. This degrades gracefully instead of failing confidently, which is the specific failure mode of a calibrated-on-Gaussian anomaly detector operating in Extremistan.

### 12.5 Change detection: taxonomy drift, done properly

§10.5's threshold on the singleton rate is a first approximation. Replace it with a detector that has a stated false-alarm rate:

```
CUSUM:   S_t = max(0, S_{t−1} + (x_t − k)),   alarm when S_t > h
Bayesian online changepoint:   posterior over run length P(r_t | x_{1:t})
```

Tune the average run length to false alarm rather than eyeballing `τ`. The monitored statistic is `f₁/n` (§1.3); the alarm means the codebook has stopped describing the world.

### 12.6 Structure without committing to a metric

Where §4.2 forces a choice of dimensionality, persistent homology does not:

```
filtration over scale → persistence diagram → bottleneck distance
```

Features that persist across a wide range of scales are structure; short bars are noise. Useful for embedding clouds and pile-sort data where the MDS dimensionality choice is doing more work than the data supports.

### 12.7 The gauge problem: comparing across a drifting frame (Malaney–Weinstein)

This is the transferable core of Weinstein's formal work, and it is directly load-bearing here.

The economic index-number problem: when preferences and baskets change, a price index compares quantities that live in different frames. Comparison requires a **connection** — a rule for parallel-transporting a measurement from one frame to another — and the choice of connection is a gauge choice. The Malaney–Weinstein program seeks a gauge-invariant formulation.

The ethnographic and telemetry version is exact. A code, construct, or event definition measured at time `t` lives in a fiber over `t`. Comparing `t₀` to `t₁` is not subtraction; it is transport:

```
X̃(t₁) = P·exp( ∫_γ A ) · X(t₀)
```

And the diagnostic falls straight out. Path dependence is curvature:

```
F = dA + A ∧ A ≠ 0    ⟺   the comparison depends on the route taken
```

**The holonomy test, which you can actually run:** re-baseline a construct through two different chains of intermediate schema versions — `v1 → v2 → v3 → v1` — and compare the result to the identity. Nonzero holonomy means your longitudinal series is an artifact of the migration path, not a fact about the world. Most analytics teams migrate event schemas repeatedly and never check this, then read trend lines across the seams.

This makes §10.4 sharper: **schema migrations are gauge transformations.** Un-versioned redefinition of a metric is not a data-quality problem, it is a frame change with no connection specified, and the resulting time series has no invariant meaning.

- **Honest status:** gauge-theoretic index numbers are a minority research program, not established practice in economics. The loop diagnostic above stands on its own regardless of whether the larger program succeeds — path-dependence of a re-baselined comparison is directly measurable and either present or not.

### 12.8 Embedded growth obligations as fragility

Weinstein's EGO concept — institutions structurally committed to a growth rate they can no longer deliver — is not a model as stated, but it formalizes cleanly into §11.6. Where `V` is institutional viability and `g` is the growth rate:

```
H(Δ) = V(g + Δ) + V(g − Δ) − 2·V(g) < 0
```

Pyramid-shaped commitments — pension ladders, tenure tracks, promotion pipelines, headcount-indexed org design, franchise expansion — are concave in growth shortfall: the harm from missing is larger than the benefit from exceeding. This is elicitable in an interview with no probabilities, per §11.6: ask what happens if intake falls 20%, then what happens if it rises 20%, and compare the two answers.

### 12.9 What does not transfer

Stated plainly, because borrowing the vocabulary without the content would be decoration. Geometric Unity is a speculative unification program, not peer-reviewed and not accepted in physics; nothing in it bears on measurement of social phenomena, and invoking it here would add nothing but register. Kayfabe and DISC are essayistic institutional critique — Kayfabe is a genuinely interesting Goffman-adjacent claim about staged institutional conflict (§5.2) and is worth reading as a framing device, but it is a metaphor, not a model. The gauge-index work (§12.7) and EGO-as-concavity (§12.8) are the two items that carry real formal weight, and they are enough.

### 12.10 The instrument, assembled — and its failure mode

The pipeline the preceding sections imply:

```
collection → open coding (§10.3 CRP) → reliability (§3, §10.6)
   → consensus and dimensionality (§2.1, §12.2)
   → causal structure triage (§0.3) and configurational inference (§7)
   → tail and ruin assessment (§11) → drift monitoring (§12.5, §12.7)
```

Six controls that have to be architectural rather than procedural, because at machine speed nobody can enforce them by hand:

1. **Search-space accounting** (§12.3) — log `m`, report `α_eff`, enforce the discovery/confirmation split.
2. **Base-rate honesty** (§12.1) — ranked queue, stated PPV, never a finding.
3. **Effective sample size on both axes** (§8.1, §11.2) — correlation and tails, reported alongside every estimate.
4. **Holonomy check on every schema migration** (§12.7) — no un-versioned redefinition.
5. **Survivorship correction** (§11.4) — the engine only sees who is still in the stream; `Cov(g,s)/E[s]` is the bias, and it is usually large.
6. **Conformal intervals** (§12.4) rather than point estimates.

**The scope question, which changes the architecture more than any of the above.** "HUMINT" names a specific threat model: collection from human sources who are not participating voluntarily. That version and the consenting-source version are different systems, not different settings.

With consenting sources — customer and user research, employee ethnography, partner interviews, voice-of-customer streams, panels — everything in this document is directly the product, the sources can be re-contacted to resolve ambiguity (which is what makes §7.2's hoop tests possible at all), and `s(x)` in §11.4 is estimable because you know who declined.

Without consent, three things break at once. Legally, you inherit wiretap and two-party-consent law, GDPR and state privacy regimes, and the FTC's unfair-surveillance line — for an agency this is category-of-business risk, not a compliance checkbox. Methodologically, you lose the ability to re-contact, which removes the disconfirming tests that make any of §7 work, leaving only confirmation. And per §12.1, at realistic prevalence the engine is wrong more than nine times in ten — which is tolerable for a product-insight queue and not tolerable when the false positives are assertions about identifiable people.

The consenting-source version is the one where this apparatus is a genuine advantage rather than a liability, and it is also the larger market. Build that one.

---

## 13. From Insight to Decision: The Qual → Quant → Action Pipeline

**Honest assessment of §0–§12:** it is strong on the *validity of the qualitative layer* and weak on *what you do with it*. Everything above establishes that a finding is real. Almost none of it establishes that the finding is worth anything, converts it into a quantitative instrument, or attaches it to a decision. This section closes that gap and carries the more recent methods (roughly 2016–2026) that the earlier sections do not reach.

### 13.1 The actionability filter

An insight has value only if it changes an action.

```
VOI = E_y[ U( d*(y) ) ] − U( d*_prior )
VOI = 0  whenever  argmax_d  is unchanged by the finding
```

Applied honestly and *before* the study rather than after, this eliminates most proposed research. "Users find onboarding confusing" has zero decision value if onboarding was being rebuilt regardless. The discipline is to name the decision, the alternatives, and the threshold at which the decision flips — then ask whether the study can plausibly move the estimate across that threshold.

### 13.2 Qual → causal DAG → adjustment set

**The strongest available claim that ethnography creates quantitative value.** Identification is not a statistical property; it is a claim about structure that data cannot supply. Pearl's back-door criterion: a set `Z` is admissible for estimating the effect of `X` on `Y` if no member of `Z` is a descendant of `X` and `Z` blocks every back-door path.

```
P(Y | do(X)) = Σ_z P(Y | X, z)·P(z)
```

What fieldwork uniquely supplies:

- **Unmeasured confounders.** You learn that purchasing decisions route through a relationship not represented in any system of record. That variable's absence is now a stated limitation instead of a silent bias.
- **Colliders.** Conditioning on a common effect *creates* spurious association. Fieldwork is how you discover that a standard "control variable" is downstream of both treatment and outcome. This is a case where adding a control makes the estimate worse, and no amount of data reveals it.
- **Mediators**, which must not be conditioned on when the total effect is the estimand.
- **Instrument validity.** The exclusion restriction is untestable by construction and must be argued substantively. Ethnography is that argument.

Getting the adjustment set wrong invalidates the entire downstream quantitative study, silently. This connects §0.3's causal-structure taxonomy directly to identification.

### 13.3 Qual → prior

Structured elicitation converts fieldwork into a probability distribution: SHELF, trial-roulette elicitation, and Cooke's classical model, which weights experts by measured calibration on seed questions with known answers — which is §2.1's competence weighting under another name.

```
posterior ∝ likelihood × prior_from_fieldwork
```

This matters most where it is least acknowledged: in small-`n` quantitative work (rare disease, B2B, industrial, early-stage product), the prior does most of the work and is usually improvised. A fieldwork-derived, documented prior is the defensible version of what is already happening.

### 13.4 Qual → instrument → measurement invariance

The instrument-development pipeline: concept elicitation → item pool → cognitive debriefing → pilot → factor structure → invariance testing.

```
configural  →  metric (equal loadings)  →  scalar (equal intercepts)  →  strict (equal residuals)
ΔCFI < 0.01 as the practical threshold; alignment optimization when groups are many
```

**Correction to §12.7, stated plainly:** measurement invariance testing is the established, tooled, thirty-year-old version of the gauge and holonomy argument. If scalar invariance fails, comparing means across groups or across time is uninterpretable — the same claim as nonzero holonomy, with software and reviewer familiarity behind it. Reach for the invariance machinery first. The gauge formulation earns its place only where there is no group structure to test against, such as schema migration in telemetry.

### 13.5 Qual → quantified priority

Free-list salience (§4.1) yields the item set; best-worst scaling or a discrete choice experiment converts it into ratio-scaled priorities with explicit tradeoffs.

```
BWS:  P(best=i, worst=j) = exp(v_i − v_j) / Σ_{k≠l} exp(v_k − v_l)
DCE:  MNL or mixed logit;  WTP = −β_attribute / β_price
```

This is the commercial workhorse §8.3 gestured at without naming. It is the standard mechanism by which an ethnographically elicited attribute becomes a number a decision-maker can trade against cost.

### 13.6 Qual → segmentation by mechanism

Latent class analysis on qualitatively derived indicators, rather than clustering on demographics:

```
P(y_i) = Σ_c π_c · Π_m P(y_im | c)
```

Classes are defined by the mechanism fieldwork identified; you then profile them against covariates already present in your systems, which is what makes the segmentation operational rather than decorative.

### 13.7 Qual → heterogeneity hypotheses → causal ML

Ethnography generates *for whom and why*; causal machine learning estimates it.

```
CATE:   τ(x) = E[ Y(1) − Y(0) | X = x ]        causal forests, X-learner
policy: π* = argmax_π E[ Y(π(X)) ]             policy trees
```

The qualitative contribution is the candidate moderator set. Without it, these methods search an enormous covariate space and, per §12.3, reliably discover heterogeneity that is not there.

### 13.8 Enriching existing data at scale: PPI and DSL

**The direct answer to "enrich existing data easily."** You have a large corpus — tickets, transcripts, reviews, CRM notes, call logs — and you want a construct from it as a variable in a downstream model. Labeling it with an LLM and proceeding naively biases every downstream estimate, because the model's errors are systematic rather than random.

Prediction-Powered Inference and Design-based Supervised Learning solve this. The mechanism:

```
imputation estimate:  θ̃ = argmin_θ (1/N) Σ_i ℓ_θ( x_i , ŷ_i )        — biased
rectifier:            r_θ = E[ ∇ℓ_θ(x, y) − ∇ℓ_θ(x, ŷ) ]              — estimated on the gold set
PPI estimate:         θ̃ corrected by r̂_θ                              — consistent, valid CIs
```

Practically: hand-label a small **probability sample**, measure the model's systematic error on it, and correct the corpus-scale estimate by that measured error. Implementations exist (`ppi_py`, `postpi`, `pspa`). Reported gains are real — on the order of 20% standard-error reduction from augmenting a hundred human annotations with tens of thousands of model judgments.

The stance worth internalizing: **do not try to build an unbiased judge; accept that the judge is biased and correct for it statistically.** That is an orthogonal and far more tractable engineering problem.

The join with everything above: the ethnographic codebook (§1–§3) becomes the annotation scheme, and PPI/DSL makes it a statistically valid variable at corpus scale. Two requirements are non-negotiable — the gold set must be a probability sample, not a convenience sample, and the coding scheme must be the validated one.

- **Honest caveat:** consistency is established under theoretical assumptions, but finite-sample behavior at the sample sizes applied researchers actually work with is still being benchmarked, and results are mixed. Treat the correction as necessary, not as a guarantee.

### 13.9 Recent developments in saturation and sample-size logic

The doc's §1.3 machinery is one tradition. Three others from the last decade belong beside it:

- **Code saturation versus meaning saturation.** These are different quantities reached at different points — codes stabilize early, the understanding of what a code *means* stabilizes considerably later. Chao1 and Good–Turing measure code saturation only, and stopping there is the standard mistake.
- **Information power.** Sample adequacy as a function of aim specificity, sample specificity, established theory, dialogue quality, and analysis strategy. A defensible non-numeric alternative where the richness assumptions behind Chao1 do not hold.
- **Prospective stopping criteria.** A declared base size, run length, and new-information threshold, specified in advance. This is the pre-registerable version and the one that belongs in a protocol or a regulatory submission.

### 13.10 A counter-position that deserves stating

Braun and Clarke's reflexive thematic analysis explicitly rejects inter-rater reliability and codebook logic for a class of research, on the grounds that coding is interpretation rather than measurement — so agreement demonstrates shared training, not truth. This is not a technical error to be corrected; it is a coherent and different epistemological commitment.

Sections §3 and §10.6 apply where codes are treated as measurements: instrument development, regulatory artifacts, machine-assisted scale-up, anything where an external party must audit the process. They do not apply to reflexive TA, and importing them there produces the appearance of rigor over work that never claimed that kind of rigor and is not improved by it.

### 13.11 The assembled pipeline

```
fieldwork
  → validated codebook (§1–§3)
  → causal DAG and adjustment set (§13.2)
  → elicited prior (§13.3)
  → instrument + invariance testing (§13.4)
  → quantified priorities (§13.5)
  → mechanism-based segments (§13.6)
  → heterogeneity and policy (§13.7)
  → corpus-scale enrichment via PPI/DSL (§13.8)
  → decision (§13.1)
```

Every arrow is a place where value is created or destroyed. The two that destroy the most: an unvalidated codebook scaled naively across a corpus (§13.8), and a finding with no decision attached to it (§13.1).

---

## 14. Blockmodeling and the Structure of Communities

§6.2 introduced blockmodeling in a paragraph. It deserves more, because it is the most developed formal apparatus anthropology and sociology have for the thing ethnographers most often claim to have found: **social structure**.

### 14.1 Positions are not communities

The most common error in applied network analysis. Two different questions, two different methods:

```
cohesion  →  who is densely connected to whom      → community detection, modularity
position  →  who occupies the same role            → blockmodeling, equivalence
```

Two village moneylenders who never interact are in the *same position* and different *communities*. Modularity-based community detection will never group them; a blockmodel will. If the ethnographic claim is about roles — brokers, patrons, gatekeepers, intermediaries — community detection is the wrong instrument and will return a confidently wrong answer.

### 14.2 The equivalence ladder

```
structural:  corr( A_i· , A_j· ) ≈ 1      same ties to the same others
automorphic: ∃ permutation preserving the graph mapping i → j
regular:     equivalent actors relate equivalently to equivalent others
```

Structural equivalence is too strict for most ethnographic purposes — it requires the *same* alters, so two chiefs in two villages are never equivalent. **Regular equivalence** is the one that captures role systems, and it is what "chief," "broker," or "patron" actually means as a structural claim.

The multiple-networks move matters most: White, Boorman and Breiger's contribution was blockmodeling several relations *simultaneously*. This is where ethnography is indispensable — you cannot get the relevant relation set from a survey. Which ties matter (credit, kinship, ritual sponsorship, labor exchange, referral, escalation) is a fieldwork finding, and a blockmodel over the wrong tie set is precise nonsense.

### 14.3 Stochastic and generalized blockmodels

Deterministic partitioning has been superseded for most purposes:

```
SBM:            P(A_ij = 1) = ω_{z_i z_j}
degree-corrected:  P(A_ij = 1) ∝ θ_i·θ_j·ω_{z_i z_j}
mixed-membership:  each actor holds a distribution over roles
```

The degree correction matters enormously in real ethnographic networks, where a few actors are connected to nearly everyone: without it, the model recovers a high-degree block and a low-degree block and calls that structure. Mixed-membership is usually the right ontology — people occupy multiple roles at once, which the deterministic partition denies by construction.

Choose the number of blocks by integrated classification likelihood or a marginal likelihood criterion, not by inspection. And apply §12.2 first: if the eigenvalue structure is inside the Marchenko–Pastur bulk, there is no block structure to find.

Generalized blockmodeling (Doreian, Batagelj and Ferligoj) lets you *pre-specify* the block types you expect — complete, null, regular, row-dominant — and fit directly. That is the format for a confirmatory ethnographic hypothesis about structure: state the image matrix you expect from fieldwork, then test it.

### 14.4 Milofsky: the node-set problem

Carl Milofsky's work on community-based organizations, voluntary associations, and small nonprofits — from the Yale Program on Nonprofit Organizations forward — makes a claim that is methodologically prior to everything in §14.1–14.3, and it is regularly missed.

**A community is constituted by its associations, not by its residents.** Studying a community by sampling individuals and aggregating produces a description of a population, not of a community. The structure lives in the relations among organizations — the fire company, the congregation, the school board, the mutual aid society — and in the overlapping memberships that bind them. His framing of community organizations through networks, markets, culture and contracts treats these as competing coordination logics rather than as one undifferentiated "tie."

The formal consequence is sharp and general:

```
the blockmodel over persons and the blockmodel over associations
are different objects and answer different questions
```

**Choice of node set is a §10.1 support decision, not a data-collection detail.** Get it wrong and no amount of network mathematics recovers the structure, because the structure was never represented. This is the network-analytic form of the bias floor: `min KL(p* ‖ p_θ)` over a model class that cannot express the object.

Two further connections:

- **Survivorship is acute here (§11.4).** Small voluntary associations form and dissolve constantly and invisibly. A network of the associations still operating is conditioned on `s(x)` in the strongest way, and the "adaptive practices" of surviving organizations look far more adaptive than they are.
- **Community resilience** — the capacity to reorganize after a destructive event — is the field-level version of §11.6. Flexible, overlapping, redundant organizational structures are convex to shock; efficient, specialized, single-threaded ones are concave. That is measurable by the second-difference test without any probability estimate.

Milofsky's more recent interest in joining ethnographic community research to mapped administrative records (electronic health records, organizational registries) is, in substance, the §13.8 enrichment pipeline pursued in the field rather than in a product.

---

## 15. Linguistic Anthropology

The document has conversation analysis (§5.5) but not linguistic anthropology, which is a distinct tradition and supplies the most rigorous qualitative-to-quantitative pipeline in the human sciences.

### 15.1 Hymes: the ethnography of speaking

Communicative competence — knowing not just what is grammatical but what is sayable, by whom, to whom, when — against a purely grammatical notion of competence. The SPEAKING mnemonic (setting, participants, ends, act sequence, key, instrumentalities, norms, genre) is, read formally, **a specified feature space for speech events**: a coding frame with dimensions derived from cross-cultural comparison rather than invented per study.

This is a ready-made `Θ` (§10.1) for any study of communication, and it is more defensible than a codebook improvised from the first ten transcripts.

### 15.2 Silverstein: indexical order

Meaning that is not referential but *pointing* — a form indexes a social identity, stance, or context. The formal content is a hierarchy:

```
n-th order:      form co-occurs with a social category (observable distribution)
n+1-th order:    the co-occurrence is itself noticed, evaluated, and used
```

Each promotion up the ladder is a measurable change in distribution plus a change in metapragmatic commentary. This is precisely a §12.5 change-detection problem on a sociolinguistic variable, and it explains a phenomenon the doc's drift machinery would otherwise treat as noise: **the meaning of an indicator changes because people notice the indicator.** That is Hacking's looping effect (§17.2) with a mechanism attached.

### 15.3 Labov: the exemplar of the whole pipeline

Variationist sociolinguistics did, in the 1960s, exactly what §13 describes.

- Ethnographic observation identifies a variable that carries social meaning.
- The variable is operationalized with explicit envelope-of-variation rules.
- Rapid anonymous observation collects data at scale under a designed protocol.
- Variable rule analysis — logistic regression on linguistic and social conditioning factors — quantifies it.

```
logit P(variant) = β₀ + Σ_k β_k·(linguistic factors) + Σ_j γ_j·(social factors)
```

Also formal and directly useful: **narrative structure** as a grammar — abstract, orientation, complicating action, evaluation, result, coda — with *evaluation* as the load-bearing element, the part that says why the story is worth telling. Coding narratives against this schema turns free-form accounts into structured objects, and evaluation clauses are where the informant's own theory of significance is located. That is the highest-value region of any transcript and most coding schemes ignore it.

### 15.4 Levinson: relativity made testable

Spatial frames of reference — relative, intrinsic, absolute — vary across languages, and the variation predicts non-linguistic performance on spatial recall and inference tasks. This is the rigorous descendant of Sapir–Whorf: an ethnographic observation converted into a falsifiable experimental prediction with an effect that either appears or does not.

It is the best available demonstration that fieldwork-derived hypotheses can carry experimental weight, and the model for §13.7's move from mechanism to testable heterogeneity.

### 15.5 Ochs: transcription is theory

The choice of what to transcribe — prosody, overlap, pause length, gaze, gesture, code-switching — is analytic, not clerical. **A transcript is a `σ(E)`.** What is not transcribed cannot be analyzed later, and the omission is invisible in the resulting data.

This is the same theorem as §10.4, discovered in linguistic anthropology first and with more attention to what is lost. It also means that transcription conventions are the measurement instrument, and should be specified and reported with the same seriousness as a coding scheme.

### 15.6 Goodwin: professional vision, and what α actually measures

Expert perception is socially organized — practitioners are trained to see the relevant object, and that training is what produces agreement. The uncomfortable implication for §3: **Krippendorff's α measures shared professional vision, not correspondence to truth.** Two coders trained together will agree; that agreement is evidence about the training, not about the world.

This is the strongest technical statement of Braun and Clarke's objection (§13.10), and it is why high α on a scheme with no external validation is not reassurance. It also predicts the LLM-judge result in §10.6: judges from one model family share a training and will agree with each other for reasons that have nothing to do with being right.

### 15.7 Componential analysis and the lineage of §4

Ethnoscience — Goodenough, Frake, Conklin — sought the native category system through formal semantic analysis: kin terms, ethnobotanical taxonomies, disease classifications, decomposed into distinctive features. Free lists, pile sorts, triad tests and consensus analysis (§2, §4) are the direct descendants, and cultural consensus theory is what the program became once it acquired a measurement model. Worth knowing because the critiques of ethnoscience — that formal elicitation produces neat taxonomies that no one actually uses — apply unchanged to any modern system that mistakes an elicited structure for a practiced one.

---

## 16. The Anthropological Tradition Proper

Distinct from the applied and commercial ethnography §18 describes. The tradition contributes four things the applied version usually discards.

### 16.1 Boas: categories must be derived, not imposed

Historical particularism and the insistence that a culture be understood in its own terms rather than placed on a universal ladder. Stripped to its methodological core this is the §10.1 argument, stated eighty years earlier: **imposing an external `Θ` guarantees a misspecification floor no sample size will close.** The four-field commitment — cultural, linguistic, archaeological, biological — is a triangulation design with genuinely independent error structures, which is rarer and more valuable than §8.1's usual correlated sources.

### 16.2 Mary Douglas: grid/group, and the missing half of §11

Taleb (§11) supplies the mathematics of risk. Douglas supplies the theory of why groups facing identical risk perceive it differently, and it is formalizable as a two-dimensional typology:

```
grid  = degree to which life is regulated by externally imposed rules
group = degree of incorporation into a bounded social unit

high grid / high group → hierarchist    risks to social order salient
low grid  / low group  → individualist  risk as opportunity
low grid  / high group → egalitarian    risks from the system, to the collective
high grid / low group  → fatalist       risk as unmanageable
```

The predictive content: **which** hazards a group amplifies is a function of its position in this space, not of the hazard's expected loss. This has been operationalized into measurement scales in the cultural cognition literature and it predicts risk-perception variance that expected-utility models cannot.

For anyone building risk assessment on ethnographic data, this is the necessary complement: §11 tells you what the exposure is, §16.2 tells you how the exposure will be seen, and the gap between those two is where every risk-communication failure lives.

### 16.3 Evans-Pritchard: self-sealing systems

The Azande material is the canonical demonstration that a belief system can absorb every disconfirmation through secondary elaboration and remain internally coherent. Formally, an unlimited supply of auxiliary hypotheses:

```
every observation becomes a straw in the wind (§7.2)
LR → 1 for all e,  so no evidence updates anything
```

The diagnostic value is general. If your candidate theory can accommodate any observation, its likelihood ratio is 1 everywhere and it is not a theory in the §0.1 sense. This applies to indigenous belief systems and to organizational strategy narratives with equal force — and the second is what you will encounter in commercial fieldwork.

### 16.4 Lévi-Strauss, Mauss, Marcus, Tsing

- **Lévi-Strauss** — myth variants as elements related by transformation rather than as independent texts. The formal residue: analyze the *transformation group*, not the individual case. Connects to §4.2's geometry and to §5.4's sequence distances.
- **Mauss** — the gift as a total social fact: one act carrying economic, legal, religious and aesthetic content simultaneously. This is the argument for multiplex networks (§14.2) — collapsing relations to a single tie type destroys the phenomenon.
- **Marcus: multi-sited ethnography** — follow the thing, the metaphor, the conflict, the person. This is the design for studying distributed systems (supply chains, platforms, standards bodies), and formally it is §0.2 applied to site selection: choose the next site to maximize discrimination between rival accounts of the system.
- **Tsing** — friction and the study of global supply chains as ethnographic objects. The contemporary demonstration that the tradition's methods work on distributed commercial systems, which is where most current applied demand sits.

### 16.5 Writing Culture: the challenge that has to be answered

Clifford and Marcus, and Strathern's related critique: ethnographic authority is constructed rhetorically; the monograph is a genre with conventions that produce the effect of objectivity; the analyst's categories are not neutral and often import the wrong ontology wholesale.

This is not answerable by adding statistics. Every estimator in this document takes the coding scheme as given, and the critique is precisely about where the scheme comes from and whose categories it encodes. The honest response has three parts: state the categories and their provenance explicitly rather than letting them operate invisibly; report where the analysis is sensitive to them; and accept that this is mitigation rather than refutation. A study that is transparent about its constructs is better than one that is not, and neither is category-neutral.

---

## 17. The Case for Qualitative Research

Everything above depends on this being right, so it should be stated rather than assumed.

### 17.1 Five arguments that hold

1. **Construct validity precedes measurement.** All measurement presupposes categories; the categories come from somewhere. Getting them wrong imposes `min_θ KL(p* ‖ p_θ)`, which no sample size reduces (§10.1). Qualitative work is the discipline of getting them right, and there is no substitute because the error is invisible from inside the data.
2. **Identification requires structure the data cannot supply.** The adjustment set is not estimable (§13.2). Which variable is a confounder and which is a collider is a claim about the world, argued substantively or not at all.
3. **Mechanisms must be observed, not inferred.** Stinchcombe's functional explanation requires exhibiting the selection process `σ` (§0.3b). Participant observation can watch someone sanction, exit, reward, or imitate. Regression cannot.
4. **You cannot pre-register a question you do not have.** Search over hypothesis space needs a generator, and the generator is fieldwork (§10.3).
5. **Meaning constitutes the variable.** Identical observable behaviors are different acts. Coding them together is misspecification, and the only way to know is to ask. This is Weber's *Verstehen* and Winch's argument that social phenomena are constituted by rules — the deepest version of the case and the one least amenable to formalization.

### 17.2 The ontological argument

Social kinds are interactive kinds: they change when classified. People learn the category, recognize themselves in it, and behave differently — Hacking's looping effect, Giddens's double hermeneutic, Silverstein's indexical promotion (§15.2) as the mechanism.

```
natural kind:      classification does not alter the object
interactive kind:  p(x) after classification ≠ p(x) before
```

This is a real disanalogy with natural science and it has a hard consequence: **the instrument alters the object, permanently and cumulatively.** It is deeper than §8.2's reactivity, which decays. A segmentation scheme that ships into a product becomes part of how users understand themselves. That is not measurement error; it is the measurement changing what is measured, and only continued qualitative contact detects it.

### 17.3 Foundational versus incremental insight, formalized

The distinction the term "foundational" is reaching for:

```
incremental:   updates the measure     P(θ) → P(θ | e)      on a fixed Θ
foundational:  changes the support     Θ → Θ ∪ {new dimension}
```

**An insight is foundational if and only if no amount of data on the existing `Θ` could have produced it.** That is a crisp test and it has a sharp corollary: foundational insight cannot come from analytics. Analytics operates on `σ(E)` (§10.4), and `σ(E)` is fixed at instrumentation. Every question answerable from the warehouse is by construction a question someone already thought to represent. The dashboard can only refine the measure; only contact with the un-instrumented world can extend the support.

This is the entire argument for continued qualitative investment inside a mature data organization, and it is why the more instrumented a company becomes, the more it needs fieldwork rather than less.

### 17.4 The honest limits

Qualitative work cannot establish prevalence, cannot estimate an effect size, cannot support a counterfactual, and does not generalize enumeratively (§7.3). It is analyst-dependent in ways that §3 mitigates and does not eliminate. Its samples are conditioned on survival and access (§11.4, §6.1). And per §16.5, its categories are not neutral.

The case is not that it is better than quantitative work. It is that it does a **different, prior, and non-substitutable** job: it produces the `Θ`, the `σ(E)`, the causal graph, and the meaning of the variables — all of which the quantitative machinery consumes and none of which it can generate. Run alone it produces vivid, unfalsifiable stories. Run downstream of nothing, quantitative work produces precise answers to unexamined questions. The failure modes are symmetric, and only one order of operations avoids both.

---

## 18. Commercial Landscape and Positioning

Included because the strategic question is inseparable from the methodological one: the reason this apparatus is not already a product is not that nobody thought of it.

### 18.1 What already exists

- **AI-moderated collection** — Listen Labs, Conveo, Outset, Strella, UserCall, Voicepanel. Funded, fast-moving, enterprise-deployed.
- **Analysis and repository** — Dovetail (category leader for UX and product), Enterpret, Thematic, Chattermill, Marvin, Condens.
- **Legacy CAQDAS** — NVivo, ATLAS.ti, MAXQDA, Dedoose, Quirkos, all adding AI features to manual-first workflows.
- **VoC and CX** — Qualtrics XM Discover, Medallia, InMoment.
- **Mobile and in-context ethnography** — dscout, Indeemo, Streetbees, Voxpopme, Discuss.io, Remesh.
- **Human intelligence as a service, already monetized at scale** — AlphaSense/Tegus, GLG, Third Bridge, Guidepoint. The expert-network model is a multi-billion-dollar category and is the closest existing analog to "ethnographic intelligence as a service."
- **Ethnographic consultancies** — ReD Associates, Stripe Partners, Gemic, plus the qual arms of Ipsos and Kantar. Twenty-plus years old.
- **The rigor layer** — free web calculators, open-source packages (`irr`, `krippendorffsalpha`, `iNEXT`, `ppi_py`), and arXiv benchmark papers. **Not productized anywhere.**

The category is crowded. The rigor layer is not. Those are different claims, and the gap between them is the entire thesis.

### 18.2 Why the rigor layer has not been productized

Insight markets buy confidence, not calibration. "Your precision at this base rate is 8.7%, here is a queue rather than a finding" is a strictly worse-sounding pitch than "five insights in twenty-four hours." Every honest uncertainty number surfaced is a reason for the buyer to choose the vendor who does not surface it. This is adverse selection, it is structural, and it is why methodological rigor has never won a horizontal insight market. Anyone planning to sell this broadly and quickly should expect that outcome.

### 18.3 Where rigor is actually priced

Where being wrong is attributable and expensive:

1. **Regulated instrument development (COA/PRO).** Saturation documentation is a required regulatory deliverable, and the governing guidance explicitly declines to specify a rule for how much is enough. A mandated artifact with no standard method is the sharpest available wedge for this apparatus, and capture–recapture approaches to it already have academic traction without a product behind them.
2. **AI evaluation governance.** EU AI Act conformity assessment and NIST AI RMF turn §10.6 into a compliance artifact rather than a feature.
3. **Litigation, regulatory remediation, and accessibility.** Methodology is attacked directly by opposing counsel, so rigor is the product.
4. **Public-sector evaluation**, where procurement requires documented method.

### 18.4 Sell or open-source

The mathematics is not defensible intellectual property. It is published, and pieces are already open source. Therefore:

- **Open-source the method library.** It is the only route to becoming *the format*, and format ownership is the actual moat — the §10.7 construct-library argument applied to standards.
- **Monetize the attestation**, not the algorithm: hosted provenance, audit trail, regulatory-grade report generation, expert review and sign-off. In regulated markets the signed artifact is the product.
- **The disruption target is not the AI qual platforms.** Their moat is UX and integrations, which an open method library does not touch. The exposed incumbents are the consultancies whose margin depends on methodological opacity, and the accuracy claims of the AI vendors — publishing a reliability benchmark that scores commercial auto-coding against α costs almost nothing and establishes the standard.

### 18.5 The constraint that governs

Horizontal and fast is the failure mode. A horizontal product has no construct library and therefore no moat, and it is a capital profile that a services business funding an internal product cannot support. The version that fits: a **services offer with the method library as leverage and credibility**, sold into one regulated vertical, priced as a deliverable rather than a seat.

---

## Credit Map

| Figure | Contribution | Formal counterpart | § |
|---|---|---|---|
| Stinchcombe | causal-structure taxonomy; many implications | KL discrimination; feedback loops; path dependence | 0 |
| Malinowski | participant observation; everyday texture | spot sampling estimation | 5.1 |
| Radcliffe-Brown / Gluckman | structure; situational analysis | blockmodels; extended case | 6.2, 7.4 |
| Glaser & Strauss | theoretical sampling; saturation | discovery curve; Chao1 | 1.2–1.4 |
| Becker | quasi-statistics; staged analysis | binomial detection; α; G-theory | 1.1, 3, 9.2 |
| Geertz | thick description; interpretation | **none, by design** | closing |
| Goffman | frames; dramaturgy | HMM latent regimes | 5.2 |
| Turner | social drama | semi-Markov phase model | 5.3 |
| Romney / Weller / Batchelder | cultural consensus | General Condorcet Model | 2.1 |
| D'Andrade | cognitive anthropology | schema as latent structure | 2 |
| Dressler | cultural consonance | prototype fit as covariate | 2.2 |
| Bernard / Gross / Johnson | systematic data collection | free lists; spot sampling | 4.1, 5.1 |
| Bourdieu | field; habitus | multiple correspondence analysis | 4.2 |
| Harrison White | structural equivalence | blockmodeling; CONCOR | 6.2 |
| Abbott | temporality; narrative | optimal matching | 5.4 |
| Sacks | sequential organization of talk | turn-transition dependence | 5.5 |
| Ragin | configurational comparison | fs/QCA consistency, coverage | 7.1 |
| Mackie | causal complexity | INUS conditions | 7.1 |
| Mitchell / Yin | analytic vs enumerative inference | Bayesian mechanism inference | 7.3 |
| Van Evera | process-tracing tests | likelihood-ratio regions | 7.2 |
| Burawoy | extended case method | maximal-surprisal case selection | 7.4 |
| Duneier | sampling critique | inverse-degree weighting | 6.1 |
| Heckathorn | hidden populations | RDS estimator | 6.1 |
| Krippendorff | content-analysis reliability | α | 3 |
| Gladwin | decision-tree modeling | discrete choice | 8.3 |
| Charmaz | reflexivity | reactivity decay model | 8.2 |
| Timmermans & Tavory | abductive analysis | model-set expansion; CRP | 10.3 |
| Kimball | Type III error | misspecification floor | 10.1 |
| Gelman & Loken | garden of forking paths | `α_eff`; split-sample | 10.2 |
| Taleb | tail regimes; fragility; ruin | `n_eff` deflation; second-difference test | 11 |
| Mandelbrot | scaling and heavy tails | power-law tail index | 11.1 |
| Peters | ergodicity economics | time vs ensemble average | 11.5 |
| Scott | moral economy; safety-first | ruin-barrier optimization | 11.5 |
| Malaney & Weinstein | gauge-theoretic index numbers | connection, curvature, holonomy test | 12.7 |
| Weinstein | embedded growth obligations | concavity in growth shortfall | 12.8 |
| Marchenko & Pastur | noise spectrum of random matrices | signal threshold `λ₊` | 12.2 |
| Vovk / Shafer | conformal prediction | distribution-free coverage | 12.4 |
| Page / Adams & MacKay | change detection | CUSUM; run-length posterior | 12.5 |
| Pearl | identification; back-door criterion | adjustment set from fieldwork | 13.2 |
| Cooke / O'Hagan (SHELF) | structured expert elicitation | calibration-weighted priors | 13.3 |
| Meredith / Asparouhov & Muthén | measurement invariance; alignment | configural → scalar testing | 13.4 |
| Louviere | best-worst scaling | ratio-scaled priority | 13.5 |
| Wager & Athey / Künzel | heterogeneous effects; policy learning | CATE; policy trees | 13.7 |
| Angelopoulos et al. | prediction-powered inference | rectifier correction | 13.8 |
| Egami, Imai et al. | design-based supervised learning | debiased LLM annotations | 13.8 |
| Hennink & Kaiser | code vs. meaning saturation | two stopping points | 13.9 |
| Malterud et al. | information power | non-numeric adequacy | 13.9 |
| Braun & Clarke | reflexive thematic analysis | **rejects** §3's framing | 13.10 |
| Milofsky | community as associations | node-set as support decision | 14.4 |
| Doreian, Batagelj & Ferligoj | generalized blockmodeling | pre-specified image matrix | 14.3 |
| Holland / Karrer & Newman | stochastic blockmodels | degree-corrected SBM | 14.3 |
| Hymes | ethnography of speaking | SPEAKING as feature space | 15.1 |
| Gumperz | contextualization cues | sequential inference in talk | 15.1 |
| Silverstein | indexical order | n-th → n+1-th order promotion | 15.2 |
| Labov | variationist sociolinguistics | variable rule; narrative grammar | 15.3 |
| Levinson | frames of reference | relativity made falsifiable | 15.4 |
| Ochs | transcription as theory | the transcript is a `σ(E)` | 15.5 |
| C. Goodwin | professional vision | what α actually measures | 15.6 |
| Goodenough / Frake / Conklin | componential analysis | lineage of §2 and §4 | 15.7 |
| Boas | historical particularism | derived vs. imposed `Θ` | 16.1 |
| Mary Douglas | grid/group cultural theory | risk perception typology | 16.2 |
| Evans-Pritchard | self-sealing systems | LR → 1 everywhere | 16.3 |
| Lévi-Strauss | structural transformation | analyze the transformation group | 16.4 |
| Mauss | total social facts | multiplex necessity | 16.4 |
| G. Marcus | multi-sited ethnography | site selection for discrimination | 16.4 |
| Tsing | friction; supply chains | distributed systems as field sites | 16.4 |
| Clifford & Marcus / Strathern | Writing Culture critique | provenance of the scheme | 16.5 |
| Hacking / Giddens | interactive kinds; double hermeneutic | classification alters the object | 17.2 |
| Weber / Winch | Verstehen; constitutive rules | meaning constitutes the variable | 17.1 |

---

## Assembling These into One Design

| Study decision | Model |
|---|---|
| What kind of claim am I making | §0.3 causal-structure triage — **do this first** |
| Is this claim even answerable by fieldwork | §0.3(c): historicist → go to archives |
| Which observation next | §0.2 KL discrimination + §1.4 EVSI |
| Which sampling rule am I running | §1.4 — declare it |
| How many informants per stratum | §1.1 detection floor |
| When to stop | §1.3 Good–Turing singleton rate |
| Does this group share a culture | §2.1 eigenvalue ratio |
| Whose account to weight | §2.1 competence weights |
| Coders or informants for the next dollar | §3 variance components |
| Does the domain have structure | §4.1–4.2 salience, MDS stress, MCA |
| Is a time-allocation claim real | §5.1 observation count |
| Did recruitment reach the population | §6.1 inverse-degree weighting |
| What caused the outcome across sites | §7.1 consistency and coverage |
| What does this one case license | §7.3 mechanism vs. prevalence |
| Is the corroboration real | §8.1 `n_eff` |
| Am I protected against the wrong question | §10.1 Type III, not pre-registration |
| How much data goes to discovery | §10.2 split-sample allocation |
| What must the event schema capture | §10.4 `σ(E)` and §0.2 discrimination |
| Has the taxonomy gone stale | §10.5 singleton-rate monitor |
| Do my LLM judges share one rubric | §10.6 eigenvalue ratio, `n_eff` |
| Which tail regime am I in | §11.1 triage — **do this alongside §0.3** |
| What is my real sample size | §11.2 correlation **and** tail deflation |
| We never observed it — so what | §11.3 rule of three, `p ≤ 3/n` |
| Who is missing from the field site | §11.4 `Cov(g, s)/E[s]` — sample the graveyard |
| Why is this behavior "irrational" | §11.5 time average under a ruin barrier |
| How exposed is this household or institution | §11.6 second-difference stress test |
| Is cost–benefit even admissible here | §11.7 reversible vs. absorbing |
| Is this detector worth deploying | §12.1 PPV at the real base rate |
| Is that eigenvalue real | §12.2 Marchenko–Pastur edge |
| How many hypotheses did we search | §12.3 log `m`, report `α_eff` |
| Is this trend line comparable across versions | §12.7 holonomy test |
| What is this institution fragile to | §12.8 concavity in growth shortfall |
| Is this finding worth having at all | §13.1 VOI — ask before the study |
| What must the downstream model adjust for | §13.2 back-door adjustment set |
| How do I turn this into an instrument | §13.4 elicitation → invariance |
| How do I rank what matters | §13.5 BWS / discrete choice |
| How do I label a whole corpus validly | §13.8 PPI / DSL with a gold probability sample |
| Have I actually saturated | §13.9 code vs. meaning saturation |
| Roles or cohesive groups | §14.1 — blockmodel vs. community detection |
| What are the nodes, actually | §14.4 node-set is a support decision |
| Which relations get modeled | §14.2 multiplex tie set from fieldwork |
| What does the talk encode | §15.1–15.3 SPEAKING, indexicality, evaluation clauses |
| What does high α actually prove | §15.6 shared training, not truth |
| Why do they see this risk differently | §16.2 grid/group position |
| Is this theory falsifiable at all | §16.3 LR → 1 test |
| Is this insight foundational | §17.3 does it extend `Θ` or update `P(θ)` |

---

## Where the Formalism Stops

Stinchcombe's own limit is instructive: he could formalize the *structure* of an explanation but not the act of proposing one, and his advice on that was essentially to read widely and think of more candidates. Nothing above generates a theory. Every model here takes as given the coding scheme, the item set, the state space, the candidate mechanisms — and those are the ethnographer's contribution, produced by interpretation.

Geertz appears in the credit map with no formal counterpart, and that is not an oversight. Deciding what a wink *means*, which framing to adopt, what the relevant categories even are — that is upstream of all of this and not reducible to it. The apparatus is for making claims auditable, for stopping honestly, for knowing when corroboration is illusory, and for refusing to make historicist claims from present-tense data. It is not for making interpretation sound settled. A Chao1 estimate computed over a badly specified code list is a confident number about nothing.

**Primary sources:** Stinchcombe, *Constructing Social Theories* (1968) and *The Logic of Social Research* (2005); Glaser & Strauss, *The Discovery of Grounded Theory* (1967); Becker, "Problems of Inference and Proof in Participant Observation" (1958) and *Tricks of the Trade*; Geertz, *The Interpretation of Cultures*; Turner, *Schism and Continuity* and *Dramas, Fields, and Metaphors*; Romney, Weller & Batchelder (1986); Weller & Romney, *Systematic Data Collection*; Bernard, *Research Methods in Anthropology*; Bourdieu, *Distinction*; White, Boorman & Breiger (1976); Abbott, *Time Matters*; Ragin, *The Comparative Method* and *Fuzzy-Set Social Science*; Mackie, *The Cement of the Universe*; Mitchell, "Case and Situation Analysis" (1983); Burawoy, "The Extended Case Method" (1998); Van Evera, *Guide to Methods for Students of Political Science*; Heckathorn (1997, 2002); Krippendorff, *Content Analysis*; Gladwin, *Ethnographic Decision Tree Modeling*.
