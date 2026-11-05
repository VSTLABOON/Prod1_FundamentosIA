"""
chatbot/engine.py
Motor orquestador principal del chatbot de Machine Learning for Kids.
Integra la clasificacion Naive Bayes, el despiece logico-discursivo de clausulas
y la generacion de veredictos fundamentados.
"""

from typing import Dict, Any, Optional, List

from chatbot.corpus import LABELS, ALGORITHM_LABELS
from chatbot.classifier import (
    extract_mlforkids_key,
    normalize_text,
    LOCAL_CLASSIFIER,
    query_mlforkids_api
)
from chatbot.discourse import (
    split_into_discourse_clauses,
    analyze_clause_discourse_role
)
from chatbot.argumentation import build_verdict_argument


def classify_message(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Clasifica un enunciado del usuario en una de las 4 etiquetas:
    Heuristica, Ciega, Evolutiva o Desconocido.
    
    Resuelve con exito enunciados complejos donde coexisten las tres categorias
    (multi-mencion) identificando el foco principal y descartando menciones accesorias.
    Si se suministra una API key de Machine Learning for Kids en la nube, combina
    la inferencia remota con el despiece discursivo local.
    """
    clean_text = (text or "").strip()
    effective_key = extract_mlforkids_key(api_key)

    if not clean_text:
        return {
            "label": "Desconocido",
            "source": "Modelo ML for Kids",
            "mlforkids_connected": False,
            "mentioned_algorithms": [],
            "multi_mention_detected": False,
            "all_three_mentioned": False,
            "clause_breakdown": [],
            "argument": {
                "title": "Sin texto de entrada",
                "main_reason": "Escribe una consulta o selecciona un ejemplo para analizarlo.",
                "multi_mention_analysis": None,
                "clues": [],
                "foundation": "",
                "full_text": "Por favor escribe una consulta o descripcion sobre algoritmos de busqueda para clasificarla y argumentar el veredicto."
            },
            "response": "Por favor escribe una consulta o descripcion sobre algoritmos de busqueda para clasificarla y argumentar el veredicto."
        }

    clauses = split_into_discourse_clauses(clean_text)
    all_clauses_norm = [normalize_text(c) for c in clauses]

    clause_breakdown: List[Dict[str, Any]] = []
    weighted_class_mass: Dict[str, float] = {lbl: 0.0 for lbl in LABELS}
    subordinate_classes: set = set()
    affirmative_classes: set = set()
    focal_clauses_texts: List[str] = []
    affirmative_clauses_texts: List[str] = []
    mentioned_set: set = set()
    aggregated_evidences: Dict[str, List[str]] = {lbl: [] for lbl in LABELS}

    for idx, clause_str in enumerate(clauses):
        role, role_weight, role_explanation = analyze_clause_discourse_role(
            clause_str, idx, len(clauses), all_clauses_norm
        )
        c_probs, c_evidences = LOCAL_CLASSIFIER.score_text_fragment(clause_str)
        c_mentions = [lbl for lbl in ALGORITHM_LABELS if len(c_evidences.get(lbl, [])) > 0]

        for m_lbl in c_mentions:
            mentioned_set.add(m_lbl)
            for ev in c_evidences.get(m_lbl, []):
                if ev not in aggregated_evidences[m_lbl]:
                    aggregated_evidences[m_lbl].append(ev)
        for ev_d in c_evidences.get("Desconocido", []):
            if ev_d not in aggregated_evidences["Desconocido"]:
                aggregated_evidences["Desconocido"].append(ev_d)

        if role in ("contraste_o_negacion", "concesion_previa", "contexto_comparativo"):
            for m_lbl in c_mentions:
                subordinate_classes.add(m_lbl)
        elif role in ("foco_principal", "afirmacion"):
            for m_lbl in c_mentions:
                affirmative_classes.add(m_lbl)
            affirmative_clauses_texts.append(clause_str)
            if role == "foco_principal":
                focal_clauses_texts.append(clause_str)

        if c_mentions and c_probs["Desconocido"] < 0.55:
            clause_top_label = max(c_mentions, key=lambda l: c_probs[l])
        else:
            clause_top_label = max(LABELS, key=lambda l: c_probs[l])

        clause_breakdown.append({
            "fragment": clause_str,
            "detected_label": clause_top_label,
            "mentioned_labels": c_mentions,
            "discourse_role": role,
            "role_explanation": role_explanation,
            "evidences": c_evidences.get(clause_top_label, []),
            "all_evidences": c_evidences
        })

        for lbl in LABELS:
            weighted_class_mass[lbl] += c_probs[lbl] * role_weight

    mentioned_algorithms = [lbl for lbl in ALGORITHM_LABELS if lbl in mentioned_set]
    multi_mention_detected = len(mentioned_algorithms) >= 2

    if affirmative_classes and subordinate_classes:
        for sub_lbl in subordinate_classes:
            if sub_lbl not in affirmative_classes:
                weighted_class_mass[sub_lbl] *= 0.10

    total_mass = sum(weighted_class_mass.values()) or 1.0
    discourse_probs = {lbl: (weighted_class_mass[lbl] / total_mass) for lbl in LABELS}

    if mentioned_algorithms and discourse_probs["Desconocido"] < 0.60 and not aggregated_evidences["Desconocido"]:
        algo_sum = sum(discourse_probs[l] for l in ALGORITHM_LABELS)
        if algo_sum > 0.25:
            discourse_probs["Desconocido"] *= 0.18
            norm_factor = sum(discourse_probs.values()) or 1.0
            discourse_probs = {lbl: discourse_probs[lbl] / norm_factor for lbl in LABELS}

    mlk_connected = False
    mlk_source_label = "Modelo ML for Kids Integrado (Sin cuenta)"
    final_probs = dict(discourse_probs)

    if effective_key and effective_key != "__BROWSER_LOCALSTORAGE__":
        active_texts = focal_clauses_texts if focal_clauses_texts else affirmative_clauses_texts
        query_target = " ".join(active_texts) if (multi_mention_detected and active_texts) else clean_text

        mlk_result = query_mlforkids_api(effective_key, query_target)
        if mlk_result:
            mlk_connected = True
            mlk_source_label = "Modelo ML for Kids (Nube)"
            top_pred = max(mlk_result, key=lambda x: x["confidence"])

            if top_pred["confidence"] < 45.0 and not mentioned_algorithms:
                final_probs = {"Heuristica": 0.0, "Ciega": 0.0, "Evolutiva": 0.0, "Desconocido": 1.0}
            else:
                api_probs = {lbl: 0.01 for lbl in LABELS}
                for item in mlk_result:
                    lbl = item["class_name"]
                    if lbl in api_probs:
                        api_probs[lbl] = max(api_probs[lbl], item["confidence"] / 100.0)

                if affirmative_classes and subordinate_classes:
                    for sub_lbl in subordinate_classes:
                        if sub_lbl not in affirmative_classes:
                            api_probs[sub_lbl] *= 0.08

                api_sum = sum(api_probs.values()) or 1.0
                api_probs = {lbl: api_probs[lbl] / api_sum for lbl in LABELS}

                alpha = 0.80
                for lbl in LABELS:
                    final_probs[lbl] = (alpha * api_probs[lbl]) + ((1.0 - alpha) * discourse_probs[lbl])
                f_sum = sum(final_probs.values()) or 1.0
                final_probs = {lbl: final_probs[lbl] / f_sum for lbl in LABELS}

    winning_label = max(LABELS, key=lambda l: final_probs[l])

    argument_obj = build_verdict_argument(
        user_text=clean_text,
        winning_label=winning_label,
        mentioned_algorithms=mentioned_algorithms,
        clause_breakdown=clause_breakdown,
        evidences=aggregated_evidences
    )

    return {
        "label": winning_label,
        "source": mlk_source_label,
        "mlforkids_connected": mlk_connected,
        "mentioned_algorithms": mentioned_algorithms,
        "multi_mention_detected": multi_mention_detected,
        "all_three_mentioned": len(mentioned_algorithms) == 3,
        "clause_breakdown": clause_breakdown,
        "evidences": aggregated_evidences,
        "argument": argument_obj,
        "response": argument_obj["full_text"]
    }
