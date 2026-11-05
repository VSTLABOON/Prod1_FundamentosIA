"""
chatbot/cli.py
Interfaz de linea de comandos (CLI) y suite de pruebas para el clasificador de ML for Kids.
Permite realizar pruebas interactivas en terminal y evaluar la precision sobre los
420 enunciados oficiales del corpus.

Uso:
    python -m chatbot.cli              # Modo interactivo
    python -m chatbot.cli --test       # Evalua el corpus completo de 420 enunciados
    python -m chatbot.cli "texto..."   # Clasifica directamente un enunciado
"""

import sys
import argparse
from typing import Dict

from chatbot.corpus import TRAINING_CORPUS, LABELS
from chatbot.engine import classify_message


def run_benchmark() -> bool:
    print("=" * 70)
    print("EVALUACION DEL CORPUS OFICIAL (420 EJEMPLOS / 4 ETIQUETAS)")
    print("=" * 70)

    total = 0
    correct = 0
    per_class_total: Dict[str, int] = {lbl: 0 for lbl in LABELS}
    per_class_correct: Dict[str, int] = {lbl: 0 for lbl in LABELS}
    errors = []

    for expected_label, examples in TRAINING_CORPUS.items():
        for ex in examples:
            total += 1
            per_class_total[expected_label] += 1
            result = classify_message(ex)
            pred = result["label"]
            if pred == expected_label:
                correct += 1
                per_class_correct[expected_label] += 1
            else:
                errors.append({
                    "text": ex,
                    "expected": expected_label,
                    "predicted": pred,
                    "reason": result["argument"]["main_reason"]
                })

    for lbl in LABELS:
        c_tot = per_class_total[lbl]
        c_cor = per_class_correct[lbl]
        pct = (c_cor / c_tot * 100.0) if c_tot else 0.0
        print(f"  - {lbl.ljust(12)}: {c_cor:3d}/{c_tot:3d} ({pct:6.2f}%)")

    overall_pct = (correct / total * 100.0) if total else 0.0
    print("-" * 70)
    print(f"Precision Total: {correct}/{total} ({overall_pct:.2f}%)")
    print("=" * 70)

    if errors:
        print(f"\nDiscrepancias detectadas ({len(errors)}):")
        for err in errors[:10]:
            print(f"  * Texto: {err['text']}")
            print(f"    Esperado: {err['expected']} | Predicho: {err['predicted']}")
        return False
    else:
        print("\nPrueba completada con 100% de precision sobre el corpus.")
        return True


def interactive_mode() -> None:
    print("=" * 70)
    print("CHATBOT ML FOR KIDS - MODO INTERACTIVO (LINEA DE COMANDOS)")
    print("Etiquetas soportadas: Heuristica, Ciega, Evolutiva, Desconocido")
    print("Escribe 'salir' o presiona Ctrl+C para terminar.")
    print("=" * 70)

    while True:
        try:
            user_input = input("\nTu consulta > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("salir", "exit", "quit"):
                print("Hasta luego.")
                break

            result = classify_message(user_input)
            print("-" * 70)
            print(f"Veredicto:    {result['label']}")
            print(f"Fuente:       {result['source']}")
            if result["mentioned_algorithms"]:
                print(f"Menciones:    {', '.join(result['mentioned_algorithms'])} (Multi-mencion: {result['multi_mention_detected']})")
            print("\nFundamentacion:")
            print(result["response"])
            print("-" * 70)
        except (KeyboardInterrupt, EOFError):
            print("\nSesion finalizada.")
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI del Chatbot ML for Kids")
    parser.add_argument("query", nargs="?", help="Texto a clasificar (opcional)")
    parser.add_argument("--test", action="store_true", help="Evaluar los 420 ejemplos del corpus")
    args = parser.parse_args()

    if args.test:
        success = run_benchmark()
        sys.exit(0 if success else 1)
    elif args.query:
        res = classify_message(args.query)
        print(f"Etiqueta: {res['label']}")
        print(f"Fuente:   {res['source']}")
        print(f"\nArgumento:\n{res['response']}")
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
