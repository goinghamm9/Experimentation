"""The rigor layer — estimators, not vibes.

Implements the measurement apparatus from *Formal Models for Ethnographic
Research* (see `docs/formal-models-for-ethnographic-research.md`). Pure Python,
no dependencies, fully offline — these are deterministic computations and must
never be delegated to a model's judgement.

    saturation   §1.2–1.3   when to stop, as an auditable number
    reliability  §3, §8.1   coder agreement, and the effective n that qualifies it
    consensus    §2.1, §12.2 Cultural Consensus Theory + Marchenko–Pastur noise edge
    honesty      §11.3, §12.1, §12.3  base rates, rule of three, search-space accounting

The limit is stated in the corpus and repeated here because it is easy to forget
once the numbers look authoritative: every estimator takes the coding scheme as
given. *A Chao1 estimate computed over a badly specified code list is a confident
number about nothing.*
"""

from .consensus import ConsensusReport, competence_weighted_answer, marchenko_pastur_edge
from .consensus import assess as assess_consensus
from .honesty import (
    SearchLedger,
    alpha_eff,
    detection_floor,
    max_spurious_correlation,
    ppv,
    rule_of_three,
)
from .reliability import (
    ReliabilityReport,
    cohens_kappa,
    fleiss_kappa,
    krippendorff_alpha,
    n_eff_correlation,
    n_eff_tail,
)
from .reliability import assess as assess_reliability
from .saturation import SaturationReport, chao1, chao1_bias_corrected, good_turing_unseen, heaps_beta
from .saturation import assess as assess_saturation

__all__ = [
    "assess_saturation", "SaturationReport", "chao1", "chao1_bias_corrected",
    "good_turing_unseen", "heaps_beta",
    "assess_reliability", "ReliabilityReport", "krippendorff_alpha",
    "cohens_kappa", "fleiss_kappa", "n_eff_correlation", "n_eff_tail",
    "assess_consensus", "ConsensusReport", "marchenko_pastur_edge",
    "competence_weighted_answer",
    "ppv", "rule_of_three", "detection_floor", "alpha_eff",
    "max_spurious_correlation", "SearchLedger",
]
