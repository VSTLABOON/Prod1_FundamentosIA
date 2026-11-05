"""
chatbot/discourse.py
Modulo de segmentacion discursiva y analisis retorico de clausulas.
Permite descomponer enunciados complejos en suboraciones y determinar el rol de cada
fragmento (foco principal, contraste/negacion, concesion previa o contexto comparativo).
Especialmente relevante para clasificar correctamente enunciados donde el usuario
menciona los 3 paradigmas de busqueda en un solo texto.
"""

import re
from typing import List, Tuple

from chatbot.classifier import normalize_text, DOMAIN_PATTERNS
from chatbot.corpus import ALGORITHM_LABELS


NEGATION_AND_EXCLUSION_PATTERNS = [
    r"\ba\s+diferencia\s+de\b",
    r"\ben\s+lugar\s+de\b",
    r"\ben\s+vez\s+de\b",
    r"\blejos\s+de\b",
    r"\bpor\s+encima\s+de\b",
    r"\bantes\s+que\s+(?:la|el|los|las|usar|emplear|busqueda|algoritmo)\b",
    r"\bfrente\s+a\s+(?:la|el|los|las|busqueda|algoritmo)\b",
    r"\ben\s+comparacion\s+con\b",
    r"\bcomparad[oa]s?\s+con\b",
    r"\bsobre\s+(?:la\s+busqueda|el\s+algoritmo|los\s+algoritmos)\b",
    r"^\s*que\s+(?:la\s+|el\s+|los\s+|las\s+|usar\s+|emplear\s+)?(?:busqueda|algoritmo|bfs|dfs|a\*|genetico)",
    r"\bsin\s+(?:usar|emplear|utilizar|aplicar|recurrir|contar)\b",
    r"\b(?:excepto|salvo)\s+(?:la|el|los|las|en)\b",
    r"\bdescartando\b",
    r"\bdescartamos\b",
    r"\bdejando\s+(?:de\s+lado|atras)\b",
    r"\bolvidando\b",
    r"\bno\s+(?:quiero|queremos|usaremos|implementaremos|aplicaremos|emplearemos|elegimos|optamos|busco|prefiero|preferimos|necesito|necesitamos|usamos|uso|utilizamos|empleamos|aplicamos)\b",
    r"\bno\s+(?:usa|utiliza|emplea|aplica|es|son|funciona|funcionan|sirve|sirven)\s+(?:la\s+|el\s+|los\s+|las\s+|con\s+|para\s+)?(?:busqueda|algoritmos?|metodo|bfs|dfs|ucs|dls|iddfs|a\*|voraz|genetic[ao]s?|evolutiv[ao]s?|cieg[ao]s?|heuristic[ao]s?)\b",
    r"\btampoco\b",
    r"(?:^|\s)ni\s+(?:la\s+|el\s+|los\s+|las\s+|usar\s+|emplear\s+|tampoco\s+|con\s+|poblaciones\s+|mutacion\s+|funcion\s+|heuristica\s+|busqueda\s+|algoritmos?\s+|bfs\b|dfs\b|a\*)",
    r"\bcuando\s+la\s+busqueda\b.*\b(?:falla|no\s+basta|es\s+lenta|es\s+intratable|consume|se\s+vuelve)\b",
]

CONCESSIVE_START_PATTERNS = [
    r"^\s*(?:aunque|si\s+bien|pese\s+a\s+que|a\s+pesar\s+de\s+que|mientras\s+que|cuando\s+la|cuando\s+el|primero\s+pense|al\s+principio)\b"
]

CONTEXT_ENUM_PATTERNS = [
    r"^\s*(?:entre\s+la|entre\s+los|entre\s+busqueda|de\s+los\s+tres|de\s+las\s+tres|en\s+clase\s+vimos|existen\s+tres|comparando\s+la|hablando\s+de|tanto\s+la)\b"
]

FOCAL_INTENT_PATTERNS = [
    r"\b(?:necesito|necesitamos|quiero|queremos|busco|prefiero|preferimos|optamos\s+por|elegimos|elegi|decidi|usaremos|usamos|utilizamos|empleamos|implementaremos|aplicaremos|emplearemos|seleccionamos)\b",
    r"\b(?:explicame|dime|cual\s+es|como\s+funciona|que\s+algoritmo|cual\s+de\s+ellos|cual\s+de\s+las|cual\s+mantiene|cual\s+usa|cual\s+utiliza|cual\s+no\s+utiliza|cual\s+no\s+usa|cual\s+explora|me\s+interesa|hablame\s+de)\b",
    r"\b(?:por\s+lo\s+tanto|en\s+consecuencia|por\s+eso|asi\s+que|por\s+consiguiente|por\s+ende|finalmente|al\s+final|en\s+este\s+caso|para\s+este\s+problema|el\s+algoritmo\s+principal|la\s+solucion\s+es)\b",
    r"\b(?:unicamente|solamente|exclusivamente|se\s+resuelve\s+con|trata\s+de|es\s+mejor|es\s+mas\s+[a-z]+|resulta\s+mejor)\b",
    r"^\s*(?:pero|sin\s+embargo|no\s+obstante|en\s+cambio|mas\s+bien|sino\s+que|sino|por\s+el\s+contrario)\b",
]


def split_into_discourse_clauses(text: str) -> List[str]:
    """
    Segmenta un texto en clausulas logico-discursivas respetando conectores de
    contraste, oraciones adversativas y puntuacion fuerte.
    """
    working = text.strip()
    if not working:
        return []

    working = re.sub(
        r"\b((?:es\s+|son\s+|resulta\s+)?(?:mejor(?:es)?|mas\s+[a-záéíóúñ]+|preferible|superior(?:es)?))\s+"
        r"(que\s+(?:la|el|los|las|usar|emplear|busqueda|algoritmo|bfs|dfs|a\*))",
        r"\1 ||| \2",
        working,
        flags=re.IGNORECASE
    )

    pattern = (
        r"(?:\s*\|\|\|\s*)|"
        r"(?:[.;:?!]+)|"
        r"(?:,\s*(?=(?:pero|sin embargo|no obstante|en cambio|por el contrario|mas bien|sino|"
        r"mientras que|aunque|si bien|por lo tanto|por eso|asi que|en consecuencia|por consiguiente|"
        r"finalmente|al final|yo |nosotros |aqui |en este |prefiero|preferimos|necesito|necesitamos|quiero|queremos|"
        r"usamos|utilizamos|empleamos|aplicamos|implementaremos|optamos|elegimos|donde|cual|como|explicame|dime)\b))|"
        r"(?:\s+(?=(?:pero|sin embargo|no obstante|en cambio|por el contrario|mas bien|sino\s+que|sino\s+la|sino\s+el|sino\s+busqueda|"
        r"mientras que|aunque|si bien|por lo tanto|por eso|asi que|en consecuencia|por consiguiente|"
        r"a diferencia de|en lugar de|en vez de|lejos de|por encima de|antes que la|antes que el|antes que usar|"
        r"frente a la|frente al|en comparacion con|comparado con|comparada con|sobre la busqueda|excepto la|salvo la|"
        r"descartando|dejando de lado|sin usar|sin emplear|sin utilizar|sin recurrir|"
        r"ni tampoco|ni usar|ni emplear|ni la busqueda|ni el algoritmo|ni los algoritmos|ni poblaciones)\b))"
    )
    raw_parts = re.split(pattern, working, flags=re.IGNORECASE)
    clauses: List[str] = []

    contrast_start_re = re.compile(
        r"^\s*(?:a\s+diferencia\s+de|en\s+lugar\s+de|en\s+vez\s+de|aunque|si\s+bien|pese\s+a\s+que|"
        r"a\s+pesar\s+de\s+que|mientras\s+que|descartando|dejando\s+de\s+lado|sin\s+usar|sin\s+emplear|"
        r"no\s+quiero|no\s+queremos|no\s+necesito)\b",
        flags=re.IGNORECASE
    )
    focal_transition_re = re.compile(
        r"\s+(?=(?:yo\s+|nosotros\s+|aqui\s+|en\s+este\s+caso\s+|este\s+metodo\s+|este\s+algoritmo\s+)?"
        r"(?:usamos|utilizamos|empleamos|aplicamos|implementaremos|elegimos|optamos|prefiero|preferimos|"
        r"necesito|necesitamos|quiero|queremos|busco|buscamos|seleccionamos|me\s+interesa|explicame|dime)\b)",
        flags=re.IGNORECASE
    )

    for part in raw_parts:
        if not part or not part.strip():
            continue
        cleaned = part.strip(" ,")
        if not cleaned:
            continue

        sub_norm = normalize_text(cleaned)
        if contrast_start_re.search(sub_norm):
            sub_splits = focal_transition_re.split(cleaned, maxsplit=1)
            if len(sub_splits) == 2 and sub_splits[0].strip() and sub_splits[1].strip():
                clauses.append(sub_splits[0].strip(" ,"))
                clauses.append(sub_splits[1].strip(" ,"))
                continue

        is_enum_intro = any(re.search(p, sub_norm) for p in CONTEXT_ENUM_PATTERNS)
        algo_hits = sum(
            1 for lbl in ALGORITHM_LABELS
            if any(re.search(pat, sub_norm) for pat, _, _ in DOMAIN_PATTERNS[lbl])
        )
        if algo_hits >= 2 and "," in cleaned and not is_enum_intro:
            comma_parts = [p.strip() for p in cleaned.split(",") if p.strip()]
            if len(comma_parts) > 1:
                clauses.extend(comma_parts)
                continue
        clauses.append(cleaned)

    return clauses if clauses else [text.strip()]


def analyze_clause_discourse_role(
    clause: str,
    index: int,
    total_clauses: int,
    all_clauses_norm: List[str]
) -> Tuple[str, float, str]:
    """
    Determina la intencion discursiva y el peso asignado a un fragmento:
    - foco_principal (peso ~2.5): afirmacion central o interrogante
    - afirmacion (peso ~1.0): descripcion directa sin conectores contrastantes
    - concesion_previa (peso ~0.22): premisa superada por 'pero / por eso'
    - contexto_comparativo (peso ~0.18): enumeracion previa o introductoria
    - contraste_o_negacion (peso ~0.06 - 0.12): exclusion deliberada ('en lugar de', 'sin usar', 'no quiero')
    """
    norm = normalize_text(clause)

    is_interrogative_start = bool(
        re.search(r"^\s*[¿?]?\s*(?:cual|cuales|que\s+algoritmo|que\s+busqueda|que\s+metodo|como\s+funciona|por\s+que)\b", norm)
    )
    if is_interrogative_start and total_clauses > 1:
        return (
            "foco_principal",
            2.50,
            "contiene la pregunta central que define lo que realmente deseas saber"
        )

    for pat in NEGATION_AND_EXCLUSION_PATTERNS:
        if re.search(pat, norm):
            return (
                "contraste_o_negacion",
                0.06,
                "se menciona unicamente para descartarlo, negarlo o contrastarlo"
            )

    for pat in CONCESSIVE_START_PATTERNS:
        if re.search(pat, norm):
            return (
                "contraste_o_negacion",
                0.12,
                "se plantea como una condicion concesiva o secundaria ('aunque / mientras que')"
            )

    if index > 0:
        prev_norm = all_clauses_norm[index - 1]
        has_own_focal = any(re.search(p, norm) for p in FOCAL_INTENT_PATTERNS)
        if (norm.startswith("y ") or norm.startswith("o ")) and not has_own_focal:
            if any(re.search(p, prev_norm) for p in CONCESSIVE_START_PATTERNS + NEGATION_AND_EXCLUSION_PATTERNS):
                return (
                    "contraste_o_negacion",
                    0.10,
                    "forma parte del mismo bloque de descarte o contraste inicial"
                )

    if total_clauses > 1:
        for pat in CONTEXT_ENUM_PATTERNS:
            if re.search(pat, norm):
                return (
                    "contexto_comparativo",
                    0.18,
                    "solo enumera las opciones posibles antes de lanzar la pregunta principal"
                )

    if index < total_clauses - 1:
        for later_norm in all_clauses_norm[index + 1:]:
            starts_override = re.search(
                r"^\s*(?:pero|sin\s+embargo|no\s+obstante|en\s+cambio|mas\s+bien|sino|por\s+el\s+contrario|"
                r"por\s+lo\s+tanto|por\s+eso|asi\s+que|en\s+consecuencia|por\s+consiguiente|finalmente|al\s+final)\b",
                later_norm
            )
            later_is_negated = any(re.search(p, later_norm) for p in NEGATION_AND_EXCLUSION_PATTERNS)
            if starts_override and not later_is_negated:
                return (
                    "concesion_previa",
                    0.22,
                    "es una premisa previa que queda superada por la decision final tras el conector ('pero / por eso / finalmente')"
                )

    has_question = "?" in clause or "¿" in clause or re.search(r"\b(?:cual|como|que|donde|por\s+que)\b", norm)
    for pat in FOCAL_INTENT_PATTERNS:
        if re.search(pat, norm):
            return (
                "foco_principal",
                2.50,
                "expresa directamente el requerimiento o eleccion principal"
            )

    if has_question and total_clauses > 1:
        return (
            "foco_principal",
            2.35,
            "formula la interrogante principal de tu mensaje"
        )

    return (
        "afirmacion",
        1.0,
        "describe directamente el funcionamiento del algoritmo buscado"
    )
