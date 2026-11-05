"""
ml_chatbot.py
Modulo de compatibilidad hacia atras para el clasificador de ML for Kids.
Todo el codigo de Python dedicado exclusivamente al chatbot reside en el paquete 'chatbot/'.
Este archivo reexporta todos los componentes publicos para mantener compatibilidad total.
"""

from chatbot import (
    LABELS,
    ALGORITHM_LABELS,
    TRAINING_CORPUS,
    normalize_text,
    extract_mlforkids_key,
    canonicalize_label,
    BLIND_ABSENCE_OF_HEURISTIC_REGEX,
    DOMAIN_PATTERNS,
    COLLOQUIAL_TRICK_PATTERNS,
    NEGATION_AND_EXCLUSION_PATTERNS,
    CONCESSIVE_START_PATTERNS,
    CONTEXT_ENUM_PATTERNS,
    FOCAL_INTENT_PATTERNS,
    LocalMLForKidsClassifier,
    LOCAL_CLASSIFIER,
    check_mlforkids_status,
    query_mlforkids_api,
    split_into_discourse_clauses,
    analyze_clause_discourse_role,
    generate_specific_insight,
    build_verdict_argument,
    classify_message,
)

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
