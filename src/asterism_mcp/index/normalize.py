"""Symbol normalisation shared by indexing and querying, so `τ_E`, `tau_E` and `tauE` meet in FTS."""

from __future__ import annotations

import re
import unicodedata

GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon", "ζ": "zeta", "η": "eta",
    "θ": "theta", "ι": "iota", "κ": "kappa", "λ": "lambda", "μ": "mu", "ν": "nu", "ξ": "xi", "π": "pi",
    "ρ": "rho", "σ": "sigma", "ς": "sigma", "τ": "tau", "υ": "upsilon", "φ": "phi", "ϕ": "phi", "χ": "chi",
    "ψ": "psi", "ω": "omega", "Γ": "Gamma", "Δ": "Delta", "Θ": "Theta", "Λ": "Lambda", "Ξ": "Xi",
    "Π": "Pi", "Σ": "Sigma", "Φ": "Phi", "Ψ": "Psi", "Ω": "Omega",
}
_SCRIPT_JOIN = re.compile(r"(?<=\w)[_^](?=[\w−-])")
_SPACES = re.compile(r"\s+")


def normalise(text: str) -> str:
    """NFKC, Greek letters spelled out, sub/superscript markers fused (`T_e` → `Te`, `λ_q` → `lambdaq`)."""
    text = unicodedata.normalize("NFKC", text)
    text = "".join(GREEK.get(ch, ch) for ch in text)
    text = _SCRIPT_JOIN.sub("", text)
    return _SPACES.sub(" ", text).strip()


_FTS_TOKEN = re.compile(r"[\w]+", re.UNICODE)


def fts_query(user_query: str) -> str:
    """Turn free text into a safe FTS5 query: normalised tokens, implicit AND, quoted phrases kept."""
    phrases = re.findall(r'"([^"]+)"', user_query)
    rest = re.sub(r'"[^"]+"', " ", user_query)
    parts = [f'"{" ".join(_FTS_TOKEN.findall(normalise(p)))}"' for p in phrases if p.strip()]
    parts += [f'"{tok}"' for tok in _FTS_TOKEN.findall(normalise(rest))]
    return " ".join(parts)


STOPWORDS = frozenset(["a", "an", "and", "are", "as", "at", "be", "by", "does", "did", "do", "for", "from", "has", "have", "how", "in", "into", "is", "it", "its", "of", "on", "or", "that", "the", "their", "there", "these", "this", "to", "was", "were", "what", "when", "where", "which", "who", "why", "with", "within", "without", "than", "then", "over", "under", "between", "about", "any", "can", "could", "should", "would", "may", "might", "much", "many", "most", "more", "less", "per", "vs", "versus"])


def fts_query_any(user_query: str) -> str:
    """Any-term FTS5 query (OR of the non-stopword tokens), used when the all-terms query finds too little."""
    toks = [t for t in _FTS_TOKEN.findall(normalise(user_query)) if t.casefold() not in STOPWORDS]
    return " OR ".join(f'"{t}"' for t in dict.fromkeys(toks))
