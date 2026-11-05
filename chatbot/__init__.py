"""
Paquete chatbot: Motor clasificador con Machine Learning for Kids (ML for Kids).
Especializado en cuatro etiquetas: Heuristica, Ciega, Evolutiva y Desconocido.
Capaz de desambiguar enunciados donde se mencionan los 3 paradigmas simultaneamente
y generar argumentos justificados con rigor conceptual y discursivo.
"""

from chatbot.corpus import (
    LABELS,
    ALGORITHM_LABELS,
    TRAINING_CORPUS
)
from chatbot.classifier import (
    normalize_text,
    extract_mlforkids_key,
    canonicalize_label,
    BLIND_ABSENCE_OF_HEURISTIC_REGEX,
    DOMAIN_PATTERNS,
    COLLOQUIAL_TRICK_PATTERNS,
    LocalMLForKidsClassifier,
    LOCAL_CLASSIFIER,
    check_mlforkids_status,
    query_mlforkids_api
)
from chatbot.discourse import (
    NEGATION_AND_EXCLUSION_PATTERNS,
    CONCESSIVE_START_PATTERNS,
    CONTEXT_ENUM_PATTERNS,
    FOCAL_INTENT_PATTERNS,
    split_into_discourse_clauses,
    analyze_clause_discourse_role
)
from chatbot.argumentation import (
    generate_specific_insight,
    build_verdict_argument
)
from chatbot.engine import classify_message

__all__ = [
    "LABELS",
    "ALGORITHM_LABELS",
    "TRAINING_CORPUS",
    "normalize_text",
    "extract_mlforkids_key",
    "canonicalize_label",
    "BLIND_ABSENCE_OF_HEURISTIC_REGEX",
    "DOMAIN_PATTERNS",
    "COLLOQUIAL_TRICK_PATTERNS",
    "NEGATION_AND_EXCLUSION_PATTERNS",
    "CONCESSIVE_START_PATTERNS",
    "CONTEXT_ENUM_PATTERNS",
    "FOCAL_INTENT_PATTERNS",
    "LocalMLForKidsClassifier",
    "LOCAL_CLASSIFIER",
    "check_mlforkids_status",
    "query_mlforkids_api",
    "split_into_discourse_clauses",
    "analyze_clause_discourse_role",
    "generate_specific_insight",
    "build_verdict_argument",
    "classify_message",
]
