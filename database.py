"""
database.py
Modulo de gestion de base de datos SQLite para el Glosario de Inteligencia Artificial.

Proporciona funciones para inicializar el esquema de datos, realizar consultas filtradas,
busquedas de texto completo, actualizacion de favoritos y generacion de preguntas
para el modulo interactivo de evaluacion.
"""

import sqlite3
import os
import random
from typing import List, Dict, Any, Optional

# Ruta absoluta o relativa del archivo de base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glossary.db")


def get_db_connection() -> sqlite3.Connection:
    """
    Establece y retorna una conexion a la base de datos SQLite.
    Configura row_factory para obtener resultados accesibles como diccionarios.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Crea la tabla de conceptos si no existe en la base de datos.
    Define las columnas necesarias para almacenar la definicion, contexto,
    formula tecnica y ruta del archivo de imagen.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            title_en TEXT NOT NULL,
            category TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            short_desc TEXT NOT NULL,
            full_definition TEXT NOT NULL,
            real_world_example TEXT NOT NULL,
            technical_detail TEXT NOT NULL,
            historical_milestone TEXT NOT NULL,
            image_name TEXT NOT NULL,
            tags TEXT NOT NULL,
            is_favorite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Indice para acelerar busquedas por categoria y slug
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepts_category ON concepts(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepts_slug ON concepts(slug)")

    conn.commit()
    conn.close()


def count_concepts() -> int:
    """
    Retorna la cantidad total de conceptos registrados en la base de datos.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM concepts")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_all_concepts(
    category: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    favorites_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Recupera la lista de conceptos aplicando filtros opcionales de categoria,
    termino de busqueda en titulo/descripcion, etiqueta o favoritos.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM concepts WHERE 1=1"
    params: List[Any] = []

    if category and category.strip() and category != "all":
        query += " AND category = ?"
        params.append(category.strip())

    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query += " AND (title LIKE ? OR title_en LIKE ? OR short_desc LIKE ? OR tags LIKE ?)"
        params.extend([search_term, search_term, search_term, search_term])

    if tag and tag.strip():
        tag_term = f"%{tag.strip()}%"
        query += " AND tags LIKE ?"
        params.append(tag_term)

    if favorites_only:
        query += " AND is_favorite = 1"

    query += " ORDER BY id ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_concept_by_id(concept_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene el detalle completo de un concepto a partir de su identificador primario.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM concepts WHERE id = ?", (concept_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_concept_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un concepto utilizando su identificador legible (slug).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM concepts WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def toggle_favorite(concept_id: int) -> Optional[bool]:
    """
    Alterna el estado de favorito de un concepto (0 o 1).
    Retorna el nuevo estado booleano o None si el concepto no existe.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT is_favorite FROM concepts WHERE id = ?", (concept_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    current_state = row["is_favorite"]
    new_state = 0 if current_state == 1 else 1

    cursor.execute("UPDATE concepts SET is_favorite = ? WHERE id = ?", (new_state, concept_id))
    conn.commit()
    conn.close()

    return bool(new_state)


def get_categories() -> List[str]:
    """
    Retorna la lista ordenada de categorias unicas presentes en la base de datos.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM concepts ORDER BY category ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row["category"] for row in rows]


def get_quiz_questions(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Genera una serie de preguntas de seleccion multiple a partir de los conceptos en la BD.
    Cada pregunta toma la definicion corta de un concepto como enunciado y 4 opciones
    de titulos de conceptos (1 correcta y 3 distractores aleatorios).
    """
    concepts = get_all_concepts()
    if len(concepts) < 4:
        return []

    selected = random.sample(concepts, min(limit, len(concepts)))
    questions = []

    for index, target in enumerate(selected, start=1):
        # Seleccionar 3 distractores distintos al concepto objetivo
        distractors = [c for c in concepts if c["id"] != target["id"]]
        sampled_distractors = random.sample(distractors, 3)

        options = [
            {"id": target["id"], "text": target["title"], "is_correct": True}
        ]
        for dist in sampled_distractors:
            options.append({
                "id": dist["id"],
                "text": dist["title"],
                "is_correct": False
            })

        random.shuffle(options)

        questions.append({
            "number": index,
            "concept_id": target["id"],
            "prompt": target["short_desc"],
            "category": target["category"],
            "difficulty": target["difficulty"],
            "options": options,
            "explanation": f"{target['title']}: {target['real_world_example']}"
        })

    return questions
