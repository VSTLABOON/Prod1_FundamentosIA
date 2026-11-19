"""
arm_storage.py
Persistencia SQL (SQLite), Memoria de Rutas (CBR) y Mini-RAG local
para el Brazo Robotico Autonomo 3D dentro de glossary.db.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from typing import Any, Dict, List, Optional

import database as db


MAX_RUNS_STORED = 300
MAX_CACHE_STORED = 40

STOPWORDS_ES = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "a", "en", "con", "por", "para", "sobre", "y", "o", "que", "cual", "cuales",
    "como", "cuanto", "cuantos", "cuanta", "cuantas", "fue", "fueron", "es", "son",
    "ha", "han", "mas", "menos", "se", "su", "sus", "este", "esta", "esto", "hay",
    "hubo", "me", "te", "lo", "le", "les", "si", "no", "muy", "vez", "veces",
}


def normalize_text(text: str) -> str:
    """Normaliza tildes y minusculas para busqueda TF-IDF consistente."""
    decomposed = unicodedata.normalize("NFKD", str(text or ""))
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return stripped.lower()


def tokenize(text: str) -> List[str]:
    """Tokeniza un texto conservando referencias tecnicas (astar, dfs, bfs, ucs)."""
    norm = normalize_text(text).replace("a*", "astar")
    tokens = re.findall(r"[a-z0-9_]+", norm)
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS_ES]


def init_arm_tables() -> None:
    """Crea las tablas arm_runs y arm_route_cache en glossary.db si no existen."""
    conn = db.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS arm_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                task_id TEXT NOT NULL,
                task_name TEXT NOT NULL,
                algorithm_id TEXT NOT NULL,
                algorithm_name TEXT NOT NULL,
                found INTEGER NOT NULL,
                is_optimal INTEGER NOT NULL,
                completed_stages INTEGER NOT NULL,
                total_stages INTEGER NOT NULL,
                nodes_expanded INTEGER NOT NULL,
                energy REAL NOT NULL,
                steps INTEGER NOT NULL,
                cycle_seconds REAL NOT NULL,
                had_unexpected INTEGER NOT NULL,
                from_cache INTEGER NOT NULL DEFAULT 0,
                within_budget INTEGER NOT NULL DEFAULT 1,
                cargo_id TEXT NOT NULL DEFAULT 'battery_module',
                cargo_name TEXT NOT NULL DEFAULT 'Modulo Bateria EV',
                weight_kg REAL NOT NULL DEFAULT 18.0,
                delivered INTEGER NOT NULL DEFAULT 0,
                payload_energy_tax REAL NOT NULL DEFAULT 0.0,
                transport_distance_m REAL NOT NULL DEFAULT 0.0,
                reason TEXT NOT NULL,
                scene_json TEXT NOT NULL,
                summary_doc TEXT NOT NULL
            )
            """
        )
        # Migracion segura si arm_runs ya existia en disco sin las nuevas columnas
        cursor.execute("PRAGMA table_info(arm_runs)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        migrations = [
            ("within_budget", "ALTER TABLE arm_runs ADD COLUMN within_budget INTEGER NOT NULL DEFAULT 1"),
            ("cargo_id", "ALTER TABLE arm_runs ADD COLUMN cargo_id TEXT NOT NULL DEFAULT 'battery_module'"),
            ("cargo_name", "ALTER TABLE arm_runs ADD COLUMN cargo_name TEXT NOT NULL DEFAULT 'Modulo Bateria EV'"),
            ("weight_kg", "ALTER TABLE arm_runs ADD COLUMN weight_kg REAL NOT NULL DEFAULT 18.0"),
            ("delivered", "ALTER TABLE arm_runs ADD COLUMN delivered INTEGER NOT NULL DEFAULT 0"),
            ("payload_energy_tax", "ALTER TABLE arm_runs ADD COLUMN payload_energy_tax REAL NOT NULL DEFAULT 0.0"),
            ("transport_distance_m", "ALTER TABLE arm_runs ADD COLUMN transport_distance_m REAL NOT NULL DEFAULT 0.0"),
        ]
        for col_name, ddl in migrations:
            if col_name not in existing_cols:
                cursor.execute(ddl)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_arm_runs_algo ON arm_runs(algorithm_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_arm_runs_found ON arm_runs(found)")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS arm_cargo_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                run_id INTEGER NOT NULL,
                task_id TEXT NOT NULL,
                task_name TEXT NOT NULL,
                algorithm_id TEXT NOT NULL,
                algorithm_name TEXT NOT NULL,
                cargo_id TEXT NOT NULL,
                cargo_name TEXT NOT NULL,
                weight_kg REAL NOT NULL,
                origin_station TEXT NOT NULL,
                destination_station TEXT NOT NULL,
                picked_up INTEGER NOT NULL DEFAULT 0,
                delivered INTEGER NOT NULL DEFAULT 0,
                delivery_status TEXT NOT NULL,
                transport_distance_m REAL NOT NULL DEFAULT 0.0,
                base_energy REAL NOT NULL DEFAULT 0.0,
                payload_energy_tax REAL NOT NULL DEFAULT 0.0,
                total_loaded_energy REAL NOT NULL DEFAULT 0.0,
                cycle_seconds REAL NOT NULL DEFAULT 0.0,
                had_unexpected INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_arm_cargo_status ON arm_cargo_ledger(delivered, cargo_id)")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS arm_route_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scene_hash TEXT NOT NULL,
                algorithm_id TEXT NOT NULL,
                task_name TEXT NOT NULL,
                energy REAL NOT NULL,
                steps INTEGER NOT NULL,
                cycle_seconds REAL NOT NULL,
                hit_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result_json TEXT NOT NULL,
                UNIQUE(scene_hash, algorithm_id)
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_arm_cache_lookup ON arm_route_cache(scene_hash, algorithm_id)")
        conn.commit()
    finally:
        conn.close()


def compute_scene_hash(
    start_deg: Any,
    waypoints: Any,
    obstacles: Any,
    cargo_id: str = "battery_module",
) -> str:
    """Calcula una huella canonica SHA-256 de la postura inicial, objetivos, obstaculos y carga."""
    canonical = {
        "cargo_id": str(cargo_id or "battery_module").strip().lower(),
        "start_deg": [round(float(start_deg[0]), 1), round(float(start_deg[1]), 1)],
        "waypoints": [
            {
                "action": str(w.get("action", "weld")),
                "x": round(float(w["x"]), 1),
                "y": round(float(w["y"]), 1),
            }
            for w in (waypoints or [])
        ],
        "obstacles": sorted(
            [
                {
                    "kind": str(o.get("kind", "car_body")),
                    "x": round(float(o["x"]), 1),
                    "y": round(float(o["y"]), 1),
                    "w": round(float(o["w"]), 1),
                    "h": round(float(o["h"]), 1),
                }
                for o in (obstacles or [])
            ],
            key=lambda item: (item["kind"], item["x"], item["y"], item["w"], item["h"]),
        ),
    }
    raw = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def lookup_cached_sequence(scene_hash: str, algorithm_id: str) -> Optional[Dict[str, Any]]:
    """Busca una ruta previamente resuelta en arm_route_cache."""
    init_arm_tables()
    conn = db.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, hit_count, result_json
            FROM arm_route_cache
            WHERE scene_hash = ? AND algorithm_id = ?
            """,
            (scene_hash, algorithm_id),
        )
        row = cursor.fetchone()
        if not row:
            return None

        cursor.execute(
            """
            UPDATE arm_route_cache
            SET hit_count = hit_count + 1, last_used_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (row["id"],),
        )
        conn.commit()

        try:
            cached = json.loads(row["result_json"])
        except (ValueError, TypeError):
            return None

        # Validar compatibilidad de entradas antiguas de cache (deben incluir telemetria de carga)
        if not isinstance(cached, dict) or "cargo" not in cached or "within_budget" not in cached:
            return None

        cached["from_cache"] = True
        cached["cache_hits"] = int(row["hit_count"]) + 1
        cached["execution_time_ms"] = 0.8
        return cached
    finally:
        conn.close()


def save_cached_sequence(
    scene_hash: str,
    algorithm_id: str,
    task_name: str,
    result: Dict[str, Any],
) -> None:
    """Almacena una solucion exitosa en arm_route_cache con poda LRU a MAX_CACHE_STORED."""
    if not result.get("found"):
        return
    init_arm_tables()
    payload = dict(result)
    payload.pop("from_cache", None)
    payload_str = json.dumps(payload, ensure_ascii=False)

    conn = db.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO arm_route_cache (
                scene_hash, algorithm_id, task_name, energy, steps, cycle_seconds, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(scene_hash, algorithm_id) DO UPDATE SET
                task_name = excluded.task_name,
                energy = excluded.energy,
                steps = excluded.steps,
                cycle_seconds = excluded.cycle_seconds,
                result_json = excluded.result_json,
                last_used_at = CURRENT_TIMESTAMP
            """,
            (
                scene_hash,
                algorithm_id,
                str(task_name or "Tarea"),
                float(result.get("energy", 0.0)),
                int(result.get("steps", 0)),
                float(result.get("cycle_seconds", 0.0)),
                payload_str,
            ),
        )
        # Mantener un tope sano de entradas en cache para Render
        cursor.execute(
            """
            DELETE FROM arm_route_cache
            WHERE id NOT IN (
                SELECT id FROM arm_route_cache
                ORDER BY last_used_at DESC, id DESC
                LIMIT ?
            )
            """,
            (MAX_CACHE_STORED,),
        )
        conn.commit()
    finally:
        conn.close()


def _build_summary_doc(record: Dict[str, Any]) -> str:
    """Genera texto indexable para el recuperador TF-IDF del Mini-RAG."""
    estado = (
        "exito optimo completado"
        if record["found"] and record["is_optimal"]
        else ("completado rodeo no optimo" if record["found"] else "fallo detenido error bloqueo")
    )
    sla = "dentro presupuesto esperado" if record["within_budget"] else "fuera expectativas excedio presupuesto 900"
    imprevisto = "con obstaculo imprevisto emergencia" if record["had_unexpected"] else "sin imprevistos normal"
    memoria = "recuperado memoria cache sql" if record["from_cache"] else "calculado desde cero"
    entrega = (
        f"carga entregada pieza transportada {record['cargo_name']} {record['weight_kg']} kg"
        if record["delivered"]
        else f"carga no entregada transporte abortado {record['cargo_name']} {record['weight_kg']} kg"
    )
    algo_alias = "astar a*" if record["algorithm_id"] == "astar" else record["algorithm_id"]
    reason_part = f"Motivo: {record['reason']}." if record["reason"] else ""
    return (
        f"Tarea {record['task_name']} ({record['task_id']}). "
        f"Estrategia {record['algorithm_name']} ({algo_alias}). "
        f"Resultado {estado}. {sla}. {entrega}. "
        f"Distancia con carga {record['transport_distance_m']} metros. "
        f"Sobrecarga por peso {record['payload_energy_tax']}. "
        f"Etapas {record['completed_stages']} de {record['total_stages']}. "
        f"Posturas probadas {record['nodes_expanded']}. Energia {record['energy']}. "
        f"Tiempo ciclo {record['cycle_seconds']} segundos. {imprevisto}. {memoria}. {reason_part}"
    ).strip()


def log_arm_run(
    task_id: str,
    task_name: str,
    result: Dict[str, Any],
    scene_payload: Dict[str, Any],
    had_unexpected: bool = False,
) -> int:
    """Guarda una ejecucion real en arm_runs y registra el movimiento de carga en arm_cargo_ledger."""
    init_arm_tables()
    algo = result.get("algorithm", {})
    cargo = result.get("cargo") or {}
    cargo_id = str(cargo.get("cargo_id") or scene_payload.get("cargo_id") or "battery_module")
    cargo_name = str(cargo.get("cargo_name") or "Modulo Bateria EV")
    weight_kg = float(cargo.get("weight_kg", 18.0))
    picked_up = 1 if cargo.get("picked_up", result.get("found")) else 0
    delivered = 1 if cargo.get("delivered", result.get("found")) else 0
    delivery_status = str(cargo.get("delivery_status") or ("entregado" if delivered else "sin_recoger"))
    origin_station = str(cargo.get("origin_station") or "Estacion origen")
    destination_station = str(cargo.get("destination_station") or "Estacion destino")
    transport_distance_m = float(cargo.get("transport_distance_m", 0.0))
    base_energy = float(result.get("energy", 0.0))
    payload_energy_tax = float(cargo.get("payload_energy_tax", result.get("payload_energy_tax", 0.0)))
    total_loaded_energy = float(cargo.get("total_loaded_energy", round(base_energy + payload_energy_tax, 1)))

    record = {
        "task_id": str(task_id or "custom"),
        "task_name": str(task_name or "Tarea en planta"),
        "algorithm_id": str(algo.get("id", "astar")),
        "algorithm_name": str(algo.get("name", "A*")),
        "found": 1 if result.get("found") else 0,
        "is_optimal": 1 if result.get("is_optimal") else 0,
        "completed_stages": int(result.get("completed_stages", 0)),
        "total_stages": int(result.get("total_stages", 1)),
        "nodes_expanded": int(result.get("nodes_expanded", 0)),
        "energy": base_energy,
        "steps": int(result.get("steps", 0)),
        "cycle_seconds": float(result.get("cycle_seconds", 0.0)),
        "had_unexpected": 1 if had_unexpected else 0,
        "from_cache": 1 if result.get("from_cache") else 0,
        "within_budget": 1 if result.get("within_budget", True) else 0,
        "cargo_id": cargo_id,
        "cargo_name": cargo_name,
        "weight_kg": weight_kg,
        "delivered": delivered,
        "payload_energy_tax": payload_energy_tax,
        "transport_distance_m": transport_distance_m,
        "reason": str(result.get("reason", "")),
    }
    summary_doc = _build_summary_doc(record)
    scene_str = json.dumps(scene_payload or {}, ensure_ascii=False)

    conn = db.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO arm_runs (
                task_id, task_name, algorithm_id, algorithm_name,
                found, is_optimal, completed_stages, total_stages,
                nodes_expanded, energy, steps, cycle_seconds,
                had_unexpected, from_cache, within_budget,
                cargo_id, cargo_name, weight_kg, delivered, payload_energy_tax, transport_distance_m,
                reason, scene_json, summary_doc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["task_id"],
                record["task_name"],
                record["algorithm_id"],
                record["algorithm_name"],
                record["found"],
                record["is_optimal"],
                record["completed_stages"],
                record["total_stages"],
                record["nodes_expanded"],
                record["energy"],
                record["steps"],
                record["cycle_seconds"],
                record["had_unexpected"],
                record["from_cache"],
                record["within_budget"],
                record["cargo_id"],
                record["cargo_name"],
                record["weight_kg"],
                record["delivered"],
                record["payload_energy_tax"],
                record["transport_distance_m"],
                record["reason"],
                scene_str,
                summary_doc,
            ),
        )
        run_id = int(cursor.lastrowid)

        cursor.execute(
            """
            INSERT INTO arm_cargo_ledger (
                run_id, task_id, task_name, algorithm_id, algorithm_name,
                cargo_id, cargo_name, weight_kg, origin_station, destination_station,
                picked_up, delivered, delivery_status, transport_distance_m,
                base_energy, payload_energy_tax, total_loaded_energy,
                cycle_seconds, had_unexpected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                record["task_id"],
                record["task_name"],
                record["algorithm_id"],
                record["algorithm_name"],
                cargo_id,
                cargo_name,
                weight_kg,
                origin_station,
                destination_station,
                picked_up,
                delivered,
                delivery_status,
                transport_distance_m,
                base_energy,
                payload_energy_tax,
                total_loaded_energy,
                record["cycle_seconds"],
                record["had_unexpected"],
            ),
        )

        cursor.execute(
            """
            DELETE FROM arm_runs
            WHERE id NOT IN (
                SELECT id FROM arm_runs ORDER BY id DESC LIMIT ?
            )
            """,
            (MAX_RUNS_STORED,),
        )
        cursor.execute(
            """
            DELETE FROM arm_cargo_ledger
            WHERE id NOT IN (
                SELECT id FROM arm_cargo_ledger ORDER BY id DESC LIMIT ?
            )
            """,
            (MAX_RUNS_STORED,),
        )
        conn.commit()
        return run_id
    finally:
        conn.close()


def _compute_paired_astar_savings(cursor: Any) -> Optional[float]:
    """
    Calcula el ahorro porcentual de energia de A* frente a otras estrategias
    comparando corridas exitosas dentro de la misma tarea (task_id).
    """
    cursor.execute(
        """
        SELECT task_id,
               AVG(CASE WHEN algorithm_id = 'astar' THEN energy END) AS astar_e,
               AVG(CASE WHEN algorithm_id != 'astar' THEN energy END) AS other_e
        FROM arm_runs
        WHERE found = 1
        GROUP BY task_id
        HAVING astar_e IS NOT NULL AND other_e IS NOT NULL AND other_e > 0
        """
    )
    paired_rows = cursor.fetchall()
    if paired_rows:
        savings = [((r["other_e"] - r["astar_e"]) / r["other_e"]) * 100.0 for r in paired_rows]
        return round(sum(savings) / len(savings), 1)
    return None


def get_arm_history(filter_mode: str = "all", limit: int = 50) -> Dict[str, Any]:
    """Consulta la bitacora SQLite, la memoria de rutas y las metricas acumuladas."""
    init_arm_tables()
    conn = db.get_db_connection()
    try:
        cursor = conn.cursor()

        where_clause = ""
        if filter_mode == "failed":
            where_clause = "WHERE found = 0"
        elif filter_mode == "unexpected":
            where_clause = "WHERE had_unexpected = 1"

        cursor.execute(
            f"""
            SELECT id, created_at, task_id, task_name, algorithm_id, algorithm_name,
                   found, is_optimal, completed_stages, total_stages,
                   nodes_expanded, energy, steps, cycle_seconds,
                   had_unexpected, from_cache, within_budget,
                   cargo_id, cargo_name, weight_kg, delivered, payload_energy_tax, transport_distance_m,
                   reason, scene_json
            FROM arm_runs
            {where_clause}
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, min(limit, 100)),),
        )
        runs = []
        for row in cursor.fetchall():
            item = dict(row)
            item["found"] = bool(item["found"])
            item["is_optimal"] = bool(item["is_optimal"])
            item["had_unexpected"] = bool(item["had_unexpected"])
            item["from_cache"] = bool(item["from_cache"])
            item["within_budget"] = bool(item["within_budget"])
            item["delivered"] = bool(item.get("delivered", item["found"]))
            try:
                item["scene"] = json.loads(item.pop("scene_json"))
            except (ValueError, TypeError):
                item["scene"] = {}
            runs.append(item)

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_runs,
                SUM(CASE WHEN found = 0 THEN 1 ELSE 0 END) AS total_failures,
                SUM(CASE WHEN from_cache = 1 THEN 1 ELSE 0 END) AS total_from_cache
            FROM arm_runs
            """
        )
        stats_row = dict(cursor.fetchone() or {})
        savings_pct = _compute_paired_astar_savings(cursor)

        cursor.execute(
            """
            SELECT id, scene_hash, algorithm_id, task_name, energy, steps, cycle_seconds, hit_count, last_used_at
            FROM arm_route_cache
            ORDER BY last_used_at DESC, id DESC
            LIMIT 30
            """
        )
        cache_entries = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) FROM arm_route_cache")
        cache_count = int(cursor.fetchone()[0])

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_transfers,
                SUM(CASE WHEN delivered = 1 THEN 1 ELSE 0 END) AS total_deliveries,
                SUM(CASE WHEN delivered = 0 THEN 1 ELSE 0 END) AS aborted_transports,
                ROUND(SUM(CASE WHEN delivered = 1 THEN weight_kg ELSE 0 END), 1) AS total_kg_delivered,
                ROUND(SUM(CASE WHEN delivered = 1 THEN transport_distance_m ELSE 0 END), 2) AS total_distance_m,
                ROUND(SUM(CASE WHEN delivered = 1 THEN payload_energy_tax ELSE 0 END), 1) AS total_payload_tax
            FROM arm_cargo_ledger
            """
        )
        cargo_stats = dict(cursor.fetchone() or {})

        cursor.execute(
            """
            SELECT id, created_at, run_id, task_id, task_name, algorithm_id, algorithm_name,
                   cargo_id, cargo_name, weight_kg, origin_station, destination_station,
                   picked_up, delivered, delivery_status, transport_distance_m,
                   base_energy, payload_energy_tax, total_loaded_energy, cycle_seconds, had_unexpected
            FROM arm_cargo_ledger
            ORDER BY id DESC
            LIMIT 40
            """
        )
        cargo_ledger = []
        for row in cursor.fetchall():
            c_item = dict(row)
            c_item["picked_up"] = bool(c_item["picked_up"])
            c_item["delivered"] = bool(c_item["delivered"])
            c_item["had_unexpected"] = bool(c_item["had_unexpected"])
            cargo_ledger.append(c_item)

        return {
            "kpis": {
                "total_runs": int(stats_row.get("total_runs") or 0),
                "total_failures": int(stats_row.get("total_failures") or 0),
                "total_from_cache": int(stats_row.get("total_from_cache") or 0),
                "cache_count": cache_count,
                "astar_energy_savings_pct": savings_pct,
                "total_deliveries": int(cargo_stats.get("total_deliveries") or 0),
                "total_kg_delivered": float(cargo_stats.get("total_kg_delivered") or 0.0),
                "total_distance_m": float(cargo_stats.get("total_distance_m") or 0.0),
                "aborted_transports": int(cargo_stats.get("aborted_transports") or 0),
                "total_payload_tax": float(cargo_stats.get("total_payload_tax") or 0.0),
            },
            "runs": runs,
            "cargo_ledger": cargo_ledger,
            "cache_entries": cache_entries,
        }
    finally:
        conn.close()


def clear_arm_storage(scope: str = "runs") -> Dict[str, int]:
    """Limpia los registros SQL solicitados ('runs', 'cargo', 'cache' o 'all')."""
    clean_scope = (scope or "runs").strip().lower()
    if clean_scope not in ("runs", "cargo", "cache", "all"):
        raise ValueError(f"Scope invalido: '{scope}'. Usa 'runs', 'cargo', 'cache' o 'all'.")

    init_arm_tables()
    conn = db.get_db_connection()
    try:
        cursor = conn.cursor()
        deleted_runs = 0
        deleted_cargo = 0
        deleted_cache = 0

        if clean_scope in ("runs", "all"):
            cursor.execute("SELECT COUNT(*) FROM arm_runs")
            deleted_runs = int(cursor.fetchone()[0])
            cursor.execute("DELETE FROM arm_runs")

        if clean_scope in ("runs", "cargo", "all"):
            cursor.execute("SELECT COUNT(*) FROM arm_cargo_ledger")
            deleted_cargo = int(cursor.fetchone()[0])
            cursor.execute("DELETE FROM arm_cargo_ledger")

        if clean_scope in ("cache", "all"):
            cursor.execute("SELECT COUNT(*) FROM arm_route_cache")
            deleted_cache = int(cursor.fetchone()[0])
            cursor.execute("DELETE FROM arm_route_cache")

        conn.commit()
        return {"deleted_runs": deleted_runs, "deleted_cargo": deleted_cargo, "deleted_cache": deleted_cache}
    finally:
        conn.close()


def _retrieve_relevant_runs(question: str, all_rows: List[Dict[str, Any]], top_k: int = 4) -> List[Dict[str, Any]]:
    """Recupera los registros SQL mas relevantes combinando TF-IDF + intencion."""
    if not all_rows:
        return []

    q_tokens = tokenize(question)
    q_norm = normalize_text(question)
    docs_tokens = [tokenize(r["summary_doc"]) for r in all_rows]
    num_docs = len(docs_tokens)

    df: Counter[str] = Counter()
    for toks in docs_tokens:
        df.update(set(toks))

    def tfidf(tokens: List[str]) -> Dict[str, float]:
        tf = Counter(tokens)
        total = max(1, len(tokens))
        return {
            t: (cnt / total) * (math.log((num_docs + 1) / (df.get(t, 0) + 1)) + 1.0)
            for t, cnt in tf.items()
        }

    q_vec = tfidf(q_tokens)
    q_mag = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0

    want_fail = any(w in q_norm for w in ("fallo", "falla", "error", "detuvo", "pierde", "bloque"))
    want_unexp = any(w in q_norm for w in ("imprevisto", "emergencia", "inesperado", "caja", "carrito"))
    want_opt = any(w in q_norm for w in ("mejor", "optima", "optimo", "energia", "eficiente", "ahorro", "rapido"))
    want_mem = any(w in q_norm for w in ("memoria", "cache", "recuerda", "recordo"))

    scored: List[Dict[str, Any]] = []
    max_id = max(r["id"] for r in all_rows)
    for row, d_toks in zip(all_rows, docs_tokens):
        d_vec = tfidf(d_toks)
        d_mag = math.sqrt(sum(v * v for v in d_vec.values())) or 1.0
        cosine = sum(q_vec[t] * d_vec.get(t, 0.0) for t in q_vec) / (q_mag * d_mag)

        boost = 0.0
        if want_fail and row["found"] == 0:
            boost += 0.35
        if want_unexp and row["had_unexpected"] == 1:
            boost += 0.30
        if want_opt and row["found"] == 1 and row["is_optimal"] == 1:
            boost += 0.22
        if want_mem and row["from_cache"] == 1:
            boost += 0.30

        recency = 0.02 * (row["id"] / max(1, max_id))
        item = dict(row)
        item["rag_score"] = round(cosine + boost + recency, 4)
        scored.append(item)

    scored.sort(key=lambda r: r["rag_score"], reverse=True)
    return scored[:top_k]


def query_arm_rag(question: str) -> Dict[str, Any]:
    """Ejecuta el pipeline Mini-RAG local (Retrieval SQL + Synthesis) sobre arm_runs."""
    init_arm_tables()
    clean_q = str(question or "").strip()
    if not clean_q:
        return {
            "question": "",
            "answer": "Escribe una pregunta sobre las corridas guardadas para consultar el historial SQL.",
            "total_indexed": 0,
            "sources": [],
        }

    conn = db.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, created_at, task_id, task_name, algorithm_id, algorithm_name,
                   found, is_optimal, completed_stages, total_stages,
                   nodes_expanded, energy, steps, cycle_seconds,
                   had_unexpected, from_cache, within_budget,
                   cargo_id, cargo_name, weight_kg, delivered, payload_energy_tax, transport_distance_m,
                   reason, summary_doc
            FROM arm_runs
            ORDER BY id DESC
            LIMIT 200
            """
        )
        all_rows = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

    if not all_rows:
        return {
            "question": clean_q,
            "answer": "Aun no hay corridas guardadas en SQLite. Ejecuta algunas tareas en la celda 3D (por ejemplo A*, Voraz, Profundidad u Obstaculo imprevisto) y vuelve a preguntar.",
            "total_indexed": 0,
            "sources": [],
        }

    sources = _retrieve_relevant_runs(clean_q, all_rows, top_k=4)
    q_norm = normalize_text(clean_q)

    # Detectar si la pregunta apunta a una tarea especifica
    scoped_rows = all_rows
    scoped_name = ""
    for kw, tid, label in (
        ("pick", "pick_and_place", "Pick & Place"),
        ("banda", "pick_and_place", "Pick & Place"),
        ("soldar", "multi_weld", "Soldar Puerta"),
        ("puerta", "multi_weld", "Soldar Puerta"),
        ("pasillo", "narrow_corridor", "Pasillo Estrecho"),
    ):
        if kw in q_norm:
            matched = [r for r in all_rows if r["task_id"] == tid]
            if matched:
                scoped_rows = matched
                scoped_name = f" en {label}"
            break

    failures = [r for r in scoped_rows if r["found"] == 0]
    over_budget_runs = [r for r in scoped_rows if r["found"] == 1 and r.get("within_budget", 1) == 0]
    successes = [r for r in scoped_rows if r["found"] == 1]
    unexpected_runs = [r for r in scoped_rows if r["had_unexpected"] == 1]
    cached_runs = [r for r in scoped_rows if r["from_cache"] == 1]

    parts: List[str] = []
    if any(w in q_norm for w in ("fallo", "falla", "error", "detuvo", "pierde", "bloque", "expectativa", "presupuesto", "900")):
        if not failures and not over_budget_runs:
            parts.append(
                f"De {len(scoped_rows)} ejecuciones guardadas{scoped_name}, ninguna fallo ni supero las expectativas (>900 posturas)."
            )
        else:
            flagged = failures + over_budget_runs
            by_algo = Counter(r["algorithm_name"] for r in flagged)
            top_algo, top_cnt = by_algo.most_common(1)[0]
            parts.append(
                f"Se detectaron {len(failures)} fallos totales y {len(over_budget_runs)} corridas fuera de expectativas (>900 posturas) "
                f"de {len(scoped_rows)} registros{scoped_name}. La estrategia mas problematica fue {top_algo} ({top_cnt} veces)."
            )
            if failures:
                reason = failures[0]["reason"] or "limite de posturas o bloqueo"
                parts.append(f"Ultimo fallo (#{failures[0]['id']}): {reason}")
            elif over_budget_runs:
                ob = over_budget_runs[0]
                parts.append(f"Ejemplo fuera de expectativas (#{ob['id']}): probo {ob['nodes_expanded']} posturas con energia {ob['energy']}.")
    elif any(w in q_norm for w in ("imprevisto", "emergencia", "inesperado", "caja", "carrito")):
        if not unexpected_runs:
            parts.append(
                f"No hay corridas guardadas con 'Obstaculo imprevisto'{scoped_name} dentro de los {len(scoped_rows)} registros."
            )
        else:
            ok_u = [r for r in unexpected_runs if r["found"] == 1]
            if ok_u:
                best_u = min(ok_u, key=lambda r: r["energy"])
                parts.append(
                    f"Existen {len(unexpected_runs)} corridas con obstaculo imprevisto ({len(ok_u)} exitosas). "
                    f"La mejor recuperacion fue #{best_u['id']} con {best_u['algorithm_name']} en {best_u['task_name']}: "
                    f"energia {best_u['energy']}, {best_u['nodes_expanded']} posturas y ciclo de {best_u['cycle_seconds']} s."
                )
            else:
                parts.append(
                    f"Se registraron {len(unexpected_runs)} intentos con imprevisto y quedaron bloqueados ({unexpected_runs[0]['reason']})."
                )
    elif any(w in q_norm for w in ("carga", "transpor", "pieza", "entreg", "peso", "kg", "kilo", "bateria", "bastidor", "lidar", "lote")):
        delivered_rows = [r for r in scoped_rows if r.get("delivered", r["found"]) == 1]
        aborted_rows = [r for r in scoped_rows if r.get("delivered", r["found"]) == 0]
        total_kg = round(sum(float(r.get("weight_kg", 0.0)) for r in delivered_rows), 1)
        total_m = round(sum(float(r.get("transport_distance_m", 0.0)) for r in delivered_rows), 2)
        total_tax = round(sum(float(r.get("payload_energy_tax", 0.0)) for r in delivered_rows), 1)
        by_cargo = Counter(r.get("cargo_name", "Modulo Bateria EV") for r in delivered_rows)
        top_cargo_txt = (
            f" Pieza principal entregada: {by_cargo.most_common(1)[0][0]} ({by_cargo.most_common(1)[0][1]} u.)."
            if by_cargo
            else ""
        )
        parts.append(
            f"Registro SQL de carga transportada{scoped_name}: {len(delivered_rows)} piezas entregadas con exito "
            f"({total_kg} kg movidos en {total_m} m de recorrido con pinza cerrada y +{total_tax} de energia por peso) "
            f"y {len(aborted_rows)} traslados abortados.{top_cargo_txt}"
        )
    elif any(w in q_norm for w in ("memoria", "cache", "recuerda", "recordo")):
        parts.append(
            f"De {len(scoped_rows)} ejecuciones registradas{scoped_name}, {len(cached_runs)} se recuperaron al instante desde la Memoria SQL (CBR) sin recalcular posturas."
        )
    elif any(w in q_norm for w in ("peor", "lento", "costoso", "gasto mas", "mas energia")):
        if not successes:
            parts.append(f"Aun no hay corridas exitosas{scoped_name} para comparar.")
        else:
            worst_e = max(successes, key=lambda r: (r["energy"], r["cycle_seconds"]))
            parts.append(
                f"La corrida exitosa mas costosa{scoped_name} fue #{worst_e['id']} con {worst_e['algorithm_name']} "
                f"en {worst_e['task_name']}: energia {worst_e['energy']}, ciclo de {worst_e['cycle_seconds']} s y {worst_e['nodes_expanded']} posturas."
            )
    elif any(w in q_norm for w in ("energia", "rapido", "tiempo", "ciclo", "mejor", "eficiente", "menor", "ahorro")):
        if not successes:
            parts.append(f"Aun no hay corridas exitosas{scoped_name} para comparar energia.")
        else:
            best_e = min(successes, key=lambda r: (r["energy"], r["nodes_expanded"]))
            worst_e = max(successes, key=lambda r: r["energy"])
            parts.append(
                f"Analizando {len(successes)} corridas exitosas{scoped_name}, la mas eficiente fue #{best_e['id']} "
                f"con {best_e['algorithm_name']} en {best_e['task_name']}: energia {best_e['energy']}, "
                f"{best_e['nodes_expanded']} posturas y ciclo de {best_e['cycle_seconds']} s."
            )
            if worst_e["id"] != best_e["id"] and worst_e["energy"] > best_e["energy"]:
                extra = round(worst_e["energy"] - best_e["energy"], 1)
                parts.append(f"En contraste, #{worst_e['id']} ({worst_e['algorithm_name']}) gasto {worst_e['energy']} (+{extra} de energia).")
    else:
        top = sources[0]
        parts.append(
            f"Resumen de {len(scoped_rows)} corridas guardadas{scoped_name} ({len(successes)} exitosas, {len(failures)} fallos): "
            f"el registro mas relevante es #{top['id']} ({top['task_name']} con {top['algorithm_name']}), "
            f"energia {top['energy']} y {top['nodes_expanded']} posturas "
            f"({'completado en ' + str(top['cycle_seconds']) + ' s' if top['found'] else 'detenido por fallo'})."
        )

    return {
        "question": clean_q,
        "answer": " ".join(parts),
        "total_indexed": len(all_rows),
        "sources": [
            {
                "id": s["id"],
                "created_at": s["created_at"],
                "task_name": s["task_name"],
                "algorithm_name": s["algorithm_name"],
                "found": bool(s["found"]),
                "is_optimal": bool(s["is_optimal"]),
                "nodes_expanded": s["nodes_expanded"],
                "energy": s["energy"],
                "cycle_seconds": s["cycle_seconds"],
                "had_unexpected": bool(s["had_unexpected"]),
                "from_cache": bool(s["from_cache"]),
                "cargo_name": s.get("cargo_name", "Modulo Bateria EV"),
                "weight_kg": s.get("weight_kg", 18.0),
                "delivered": bool(s.get("delivered", s["found"])),
                "rag_score": s["rag_score"],
            }
            for s in sources
        ],
    }
