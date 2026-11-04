"""
app.py
Servidor principal del Glosario de Inteligencia Artificial (Flask).

Gestiona la entrega de paginas web, la API RESTful para el filtrado reactivo
de conceptos, la generacion de cuestionarios interactivos y la comprobacion
automatica de estado de archivos multimedia para despliegue en la nube.
"""

import os
from flask import Flask, render_template, jsonify, request
import database as db
import seed_db
import ml_chatbot

app = Flask(__name__, static_folder="static", template_folder="templates")

# Configuracion de clave secreta para entornos de produccion y sesiones
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "glosario-ia-clave-secreta-produccion")


def ensure_database_ready() -> None:
    """
    Verifica que la base de datos este inicializada y poblada con los 20 conceptos.
    Si la base de datos no existe o esta incompleta, ejecuta la siembra automaticamente.
    Esto permite el despliegue directo en plataformas en la nube (Render, Railway, Heroku)
    sin necesidad de ejecutar scripts manuales posteriores al despliegue.
    """
    try:
        db.init_db()
        total = db.count_concepts()
        if total < 20:
            print(f"[INICIALIZACION] Se detectaron {total} conceptos. Ejecutando siembra inicial...")
            seed_db.seed()
        else:
            print(f"[INICIALIZACION] Base de datos verificada. Total de conceptos: {total}")
    except Exception as error:
        print(f"[ERROR INICIALIZACION] Ocurrio un fallo al preparar la base de datos: {error}")


# Ejecutar comprobacion automatica al cargar el modulo
ensure_database_ready()


def enrich_concept_with_media_status(concept: dict) -> dict:
    """
    Verifica si el archivo de imagen fisica existe en la carpeta static/images/.
    Retorna el diccionario enriquecido con el indicador 'has_custom_image' y la URL.
    """
    image_name = concept.get("image_name", "")
    images_dir = os.path.join(app.static_folder, "images")
    image_path = os.path.join(images_dir, image_name)

    has_image = bool(image_name and os.path.isfile(image_path))
    concept_copy = dict(concept)
    concept_copy["has_custom_image"] = has_image
    concept_copy["image_url"] = f"/static/images/{image_name}" if image_name else ""
    return concept_copy


@app.route("/")
def index():
    """
    Ruta principal. Renderiza la maqueta visual con el listado inicial
    de conceptos y las categorias disponibles para el filtrado interactivo.
    """
    categories = db.get_categories()
    raw_concepts = db.get_all_concepts()
    concepts = [enrich_concept_with_media_status(c) for c in raw_concepts]
    return render_template(
        "index.html",
        concepts=concepts,
        categories=categories,
        total_count=len(concepts)
    )


@app.route("/api/concepts", methods=["GET"])
def api_get_concepts():
    """
    Endpoint REST para consultar la lista de conceptos.
    Parametros de consulta opcionales:
      - category: Filtro por categoria tematica
      - q o search: Termino de busqueda en texto
      - tag: Filtro por etiqueta
      - favorites: 'true' para filtrar unicamente marcados como favoritos
    """
    category = request.args.get("category")
    search = request.args.get("q") or request.args.get("search")
    tag = request.args.get("tag")
    favorites_param = request.args.get("favorites", "").lower()
    favorites_only = favorites_param in ["true", "1", "yes"]

    raw_concepts = db.get_all_concepts(
        category=category,
        search=search,
        tag=tag,
        favorites_only=favorites_only
    )
    enriched = [enrich_concept_with_media_status(c) for c in raw_concepts]

    return jsonify({
        "status": "success",
        "count": len(enriched),
        "data": enriched
    })


@app.route("/api/concepts/<int:concept_id>", methods=["GET"])
def api_get_concept_detail(concept_id: int):
    """
    Endpoint REST para obtener la ficha tecnica completa de un concepto especifico.
    """
    concept = db.get_concept_by_id(concept_id)
    if not concept:
        return jsonify({"status": "error", "message": "Concepto no encontrado"}), 404

    return jsonify({
        "status": "success",
        "data": enrich_concept_with_media_status(concept)
    })


@app.route("/api/concepts/<int:concept_id>/favorite", methods=["POST"])
def api_toggle_favorite(concept_id: int):
    """
    Endpoint REST para alternar el estado de favorito de un concepto.
    """
    new_state = db.toggle_favorite(concept_id)
    if new_state is None:
        return jsonify({"status": "error", "message": "Concepto no encontrado"}), 404

    return jsonify({
        "status": "success",
        "concept_id": concept_id,
        "is_favorite": new_state
    })


@app.route("/api/categories", methods=["GET"])
def api_get_categories():
    """
    Endpoint REST para obtener el catalogo de categorias existentes.
    """
    categories = db.get_categories()
    return jsonify({
        "status": "success",
        "data": categories
    })


@app.route("/api/quiz", methods=["GET"])
def api_get_quiz():
    """
    Endpoint REST para generar un cuestionario aleatorio de seleccion multiple.
    Acepta el parametro 'limit' para fijar el numero de preguntas (defecto: 5).
    """
    limit = request.args.get("limit", default=5, type=int)
    questions = db.get_quiz_questions(limit=max(1, min(limit, 15)))
    return jsonify({
        "status": "success",
        "count": len(questions),
        "data": questions
    })


@app.route("/api/chatbot/classify", methods=["POST"])
def api_chatbot_classify():
    """
    Endpoint REST para clasificar un mensaje mediante el modelo de ML for Kids
    entrenado con las 4 etiquetas: Heuristica, Ciega, Evolutiva y Desconocido.
    Incluye desambiguacion discursiva cuando se mencionan multiples algoritmos
    en un mismo texto.
    """
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    api_key = payload.get("api_key", "")

    result = ml_chatbot.classify_message(text=text, api_key=api_key)
    return jsonify({
        "status": "success",
        "data": result
    })


@app.route("/api/chatbot/verify-key", methods=["POST"])
def api_chatbot_verify_key():
    """
    Endpoint REST para verificar y normalizar una API Key o URL de un proyecto
    entrenado en Machine Learning for Kids (machinelearningforkids.co.uk).
    """
    payload = request.get_json(silent=True) or {}
    raw_key = payload.get("api_key", "")
    status_info = ml_chatbot.check_mlforkids_status(raw_key)
    return jsonify({
        "status": "success",
        "data": status_info
    })


@app.route("/api/chatbot/training-data", methods=["GET"])
def api_chatbot_training_data():
    """
    Endpoint REST que devuelve el corpus de entrenamiento de las 4 etiquetas
    (Heuristica, Ciega, Evolutiva, Desconocido) para consulta o carga en ML for Kids.
    """
    return jsonify({
        "status": "success",
        "labels": list(ml_chatbot.LABELS),
        "corpus": ml_chatbot.TRAINING_CORPUS
    })


@app.route("/api/chatbot/train", methods=["POST"])
def api_chatbot_train():
    """
    Endpoint REST para agregar un nuevo ejemplo de entrenamiento a una de las
    4 cubetas (Heuristica, Ciega, Evolutiva, Desconocido) y reentrenar en vivo
    el modelo local, igual que en el modo sin cuenta de ML for Kids.
    """
    payload = request.get_json(silent=True) or {}
    label = payload.get("label", "")
    text = payload.get("text", "")
    added = ml_chatbot.LOCAL_CLASSIFIER.add_example(label, text)
    if not added:
        return jsonify({
            "status": "error",
            "message": "Por favor ingresa un texto valido y selecciona una de las 4 etiquetas."
        }), 400

    canon = ml_chatbot.canonicalize_label(label)
    return jsonify({
        "status": "success",
        "label": canon,
        "total_in_bucket": len(ml_chatbot.TRAINING_CORPUS.get(canon, [])),
        "message": f"Ejemplo agregado a la cubeta '{canon}' y modelo reentrenado exitosamente."
    })


if __name__ == "__main__":
    # Deteccion de puerto dinamico para despliegues en la nube (Render, Railway, Heroku)
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    print(f"[SERVIDOR] Iniciando Glosario de IA en http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
