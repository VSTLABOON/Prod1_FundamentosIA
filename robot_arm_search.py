"""
robot_arm_search.py
Motor en Python para Planificacion de Movimientos de un Brazo Robotico 2D
en una celda automotriz (Puebla: soldadura y ensamble evitando colisiones).

Elementos formales implementados:
    S          : Espacio de Configuraciones (C-Space) discreto (theta1, theta2) en pasos de 5 grados (72 x 72 = 5,184 estados).
    s0         : Configuracion angular inicial de reposo.
    A(s)       : Movimientos angulares del hombro (+-5 deg) y codo (+-5 deg).
    Result(s,a): Nuevo par (theta1', theta2') valido sin colision con obstaculos de planta.
    GoalTest(s): Efector final (antorcha) dentro del radio de soldadura del punto objetivo.
    c(s,a,s')  : Energia mecanica (mover hombro pesado = 1.6, mover codo ligero = 1.0).
"""

from __future__ import annotations

import heapq
import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


STEP_DEG = 5
GRID_N = 360 // STEP_DEG  # 72 x 72 = 5,184 configuraciones

# Geometria de la celda 2D (440 x 380 px)
BASE_X = 220.0
BASE_Y = 215.0
L1 = 95.0   # Eslabon 1 (hombro -> codo)
L2 = 80.0   # Eslabon 2 (codo -> antorcha)
ARM_PAD = 5.0
GOAL_TOLERANCE = 15.0

COST_SHOULDER = 1.6
COST_ELBOW = 1.0


@dataclass(frozen=True)
class PlantObstacle:
    id: str
    label: str
    kind: str  # 'car_body' | 'pillar' | 'press' | 'conveyor'
    x: float
    y: float
    w: float
    h: float


PRESET_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "welding_door": {
        "id": "welding_door",
        "name": "Celda de Soldadura (Puerta)",
        "description": "El brazo debe rodear la puerta automotriz y un pilar de nave para soldar el punto superior.",
        "start_deg": (165, 340),
        "target": (335.0, 130.0),
        "obstacles": [
            PlantObstacle("obs_door", "Carroceria / Puerta", "car_body", 275.0, 175.0, 70.0, 42.0),
            PlantObstacle("obs_pillar", "Pilar Nave", "pillar", 95.0, 75.0, 32.0, 58.0),
            PlantObstacle("obs_conv", "Banda Transp.", "conveyor", 45.0, 315.0, 135.0, 32.0),
        ],
    },
    "narrow_chassis": {
        "id": "narrow_chassis",
        "name": "Ensamble Chasis Estrecho",
        "description": "Dos estructuras industriales forman un pasillo estrecho hacia el punto de ensamble.",
        "start_deg": (165, 35),
        "target": (355.0, 215.0),
        "obstacles": [
            PlantObstacle("obs_press", "Prensa Troquel", "press", 295.0, 68.0, 54.0, 68.0),
            PlantObstacle("obs_chassis", "Chasis Inferior", "car_body", 290.0, 278.0, 74.0, 48.0),
            PlantObstacle("obs_pillar2", "Columna Seguridad", "pillar", 92.0, 95.0, 32.0, 50.0),
        ],
    },
    "double_barrier": {
        "id": "double_barrier",
        "name": "Barrera en L (Muestra desvios)",
        "description": "Una cabina y un marco bloquean el camino directo; Voraz toma un rodeo costoso mientras A* encuentra la ruta optima.",
        "start_deg": (95, 35),
        "target": (340.0, 255.0),
        "obstacles": [
            PlantObstacle("obs_wall1", "Cabina Pintura", "press", 275.0, 140.0, 30.0, 75.0),
            PlantObstacle("obs_wall2", "Marco Superior", "car_body", 275.0, 108.0, 65.0, 24.0),
            PlantObstacle("obs_conv2", "Banda Baja", "conveyor", 45.0, 325.0, 125.0, 30.0),
        ],
    },
}

TASK_PRESETS: Dict[str, Dict[str, Any]] = {
    "pick_and_place": {
        "id": "pick_and_place",
        "name": "Pick & Place",
        "subtitle": "Recoge una pieza de la banda y colocala en la prensa sin chocar.",
        "start_deg": (170, 15),
        "waypoints": [
            {"id": "wp_pick", "label": "Tomar pieza en Banda", "action": "pick", "x": 118.0, "y": 275.0},
            {"id": "wp_place", "label": "Colocar en Prensa", "action": "place", "x": 316.0, "y": 142.0},
        ],
        "obstacles": [
            PlantObstacle("obs_conv", "Banda Transp.", "conveyor", 45.0, 298.0, 128.0, 30.0),
            PlantObstacle("obs_pillar", "Pilar Nave", "pillar", 90.0, 65.0, 30.0, 52.0),
            PlantObstacle("obs_door", "Carroceria / Puerta", "car_body", 275.0, 182.0, 68.0, 38.0),
            PlantObstacle("obs_press", "Prensa Troquel", "press", 295.0, 68.0, 54.0, 56.0),
        ],
        "unexpected": {"id": "obs_emergency", "label": "Carrito Imprevisto", "kind": "press", "x": 135.0, "y": 230.0, "w": 26.0, "h": 26.0},
    },
    "multi_weld": {
        "id": "multi_weld",
        "name": "Soldar Puerta (3 pts)",
        "subtitle": "Suelda 3 puntos reales de la puerta en secuencia continua.",
        "start_deg": (165, 340),
        "waypoints": [
            {"id": "wp_1", "label": "1. Bisagra superior", "action": "weld", "x": 325.0, "y": 125.0},
            {"id": "wp_2", "label": "2. Marco lateral", "action": "weld", "x": 358.0, "y": 195.0},
            {"id": "wp_3", "label": "3. Chapa inferior", "action": "weld", "x": 318.0, "y": 258.0},
        ],
        "obstacles": [
            PlantObstacle("obs_door", "Carroceria / Puerta", "car_body", 272.0, 174.0, 68.0, 42.0),
            PlantObstacle("obs_pillar", "Pilar Nave", "pillar", 95.0, 75.0, 32.0, 58.0),
            PlantObstacle("obs_conv", "Banda Transp.", "conveyor", 45.0, 315.0, 135.0, 32.0),
        ],
        "unexpected": {"id": "obs_emergency", "label": "Caja Imprevista", "kind": "press", "x": 225.0, "y": 75.0, "w": 32.0, "h": 32.0},
    },
    "narrow_corridor": {
        "id": "narrow_corridor",
        "name": "Pasillo Estrecho",
        "subtitle": "Maniobra fina entre prensa y chasis para fijar dos puntos de ensamble.",
        "start_deg": (165, 35),
        "waypoints": [
            {"id": "wp_1", "label": "1. Nucleo central", "action": "weld", "x": 355.0, "y": 215.0},
            {"id": "wp_2", "label": "2. Soporte superior", "action": "weld", "x": 335.0, "y": 162.0},
        ],
        "obstacles": [
            PlantObstacle("obs_press", "Prensa Troquel", "press", 295.0, 68.0, 54.0, 68.0),
            PlantObstacle("obs_chassis", "Chasis Inferior", "car_body", 290.0, 278.0, 74.0, 48.0),
            PlantObstacle("obs_pillar2", "Columna Seguridad", "pillar", 92.0, 95.0, 32.0, 50.0),
        ],
        "unexpected": {"id": "obs_emergency", "label": "Carrito Imprevisto", "kind": "press", "x": 130.0, "y": 105.0, "w": 30.0, "h": 30.0},
    },
}

ALGORITHMS_INFO: Dict[str, Dict[str, Any]] = {
    "astar": {
        "id": "astar",
        "name": "A* (Heuristica)",
        "paradigm": "Heuristica (Informada)",
        "description": "Combina energia acumulada g(n) y distancia angular h(n) para rodear obstaculos con minima exploracion.",
    },
    "ucs": {
        "id": "ucs",
        "name": "Costo Uniforme",
        "paradigm": "Ciega con costo",
        "description": "Garantiza el menor gasto energetico g(n), pero explora el mapa angular en todas direcciones.",
    },
    "greedy": {
        "id": "greedy",
        "name": "Busqueda Voraz",
        "paradigm": "Heuristica pura",
        "description": "Avanza directo hacia el angulo meta usando solo h(n); puede chocar con barreras y tomar rodeos costosos.",
    },
    "bfs": {
        "id": "bfs",
        "name": "Anchura (BFS)",
        "paradigm": "Ciega",
        "description": "Explora por ondas sin saber donde esta la meta ni distinguir el gasto energetico del hombro.",
    },
    "dfs": {
        "id": "dfs",
        "name": "Profundidad (DFS)",
        "paradigm": "Ciega",
        "description": "Se lanza por una rama hasta el fondo; suele dar giros largos o agotar su limite de pasos.",
    },
}


def forward_kinematics(i1: int, i2: int) -> Tuple[float, float, float, float]:
    """Calcula (elbow_x, elbow_y, tip_x, tip_y) a partir de indices angulares (i1, i2)."""
    a1 = math.radians(i1 * STEP_DEG)
    a2 = math.radians((i1 + i2) * STEP_DEG)
    ex = BASE_X + L1 * math.cos(a1)
    ey = BASE_Y - L1 * math.sin(a1)
    tx = ex + L2 * math.cos(a2)
    ty = ey - L2 * math.sin(a2)
    return ex, ey, tx, ty


def _segment_intersects_aabb(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    rx: float,
    ry: float,
    rw: float,
    rh: float,
    pad: float = ARM_PAD,
) -> bool:
    """Prueba exacta de interseccion segmento-rectangulo (Liang-Barsky) con margen de seguridad."""
    min_x = rx - pad
    max_x = rx + rw + pad
    min_y = ry - pad
    max_y = ry + rh + pad

    dx = x2 - x1
    dy = y2 - y1
    t0 = 0.0
    t1 = 1.0

    for p, q in ((-dx, x1 - min_x), (dx, max_x - x1), (-dy, y1 - min_y), (dy, max_y - y1)):
        if p == 0.0:
            if q < 0.0:
                return False
        else:
            r = q / p
            if p < 0.0:
                if r > t1:
                    return False
                if r > t0:
                    t0 = r
            else:
                if r < t0:
                    return False
                if r < t1:
                    t1 = r
    return True


def _finite_float(val: Any, name: str) -> float:
    """Convierte y valida que un valor numerico sea finito (sin NaN ni Inf)."""
    num = float(val)
    if not math.isfinite(num):
        raise ValueError(f"Valor no finito para '{name}'")
    return num


def validate_start_deg(start_deg: Any) -> Tuple[int, int]:
    """Valida que start_deg contenga 2 angulos finitos."""
    if not isinstance(start_deg, (list, tuple)) or len(start_deg) < 2:
        raise ValueError("start_deg debe contener [theta1, theta2]")
    d1 = int(round(_finite_float(start_deg[0], "start_deg[0]")))
    d2 = int(round(_finite_float(start_deg[1], "start_deg[1]")))
    return d1, d2


def validate_waypoints(raw_waypoints: Any) -> List[Dict[str, Any]]:
    """Valida la lista de puntos objetivo (entre 1 y 10 waypoints validos)."""
    if raw_waypoints is None:
        return [dict(w) for w in TASK_PRESETS["pick_and_place"]["waypoints"]]
    if not isinstance(raw_waypoints, list) or len(raw_waypoints) == 0:
        raise ValueError("waypoints debe ser una lista no vacia")
    if len(raw_waypoints) > 10:
        raise ValueError("Maximo 10 puntos objetivo permitidos por secuencia")

    validated: List[Dict[str, Any]] = []
    for idx, wp in enumerate(raw_waypoints):
        if not isinstance(wp, dict) or "x" not in wp or "y" not in wp:
            raise ValueError(f"Waypoint {idx} invalido: requiere 'x' e 'y'")
        wx = _finite_float(wp["x"], f"waypoints[{idx}].x")
        wy = _finite_float(wp["y"], f"waypoints[{idx}].y")
        validated.append({
            "id": str(wp.get("id", f"wp_{idx}")),
            "label": str(wp.get("label", f"Punto {idx + 1}")),
            "action": str(wp.get("action", "weld")),
            "x": wx,
            "y": wy,
        })
    return validated


def parse_obstacles(raw_obstacles: Optional[List[Dict[str, Any]]]) -> List[PlantObstacle]:
    """Convierte obstaculos enviados desde la UI a objetos PlantObstacle validados."""
    if raw_obstacles is None:
        return list(PRESET_SCENARIOS["welding_door"]["obstacles"])
    if not isinstance(raw_obstacles, list):
        raise ValueError("obstacles debe ser una lista")
    if len(raw_obstacles) > 20:
        raise ValueError("Maximo 20 obstaculos permitidos")

    parsed: List[PlantObstacle] = []
    for idx, item in enumerate(raw_obstacles):
        if not isinstance(item, dict):
            continue
        try:
            x = _finite_float(item["x"], "obstacle.x")
            y = _finite_float(item["y"], "obstacle.y")
            w = max(16.0, min(300.0, _finite_float(item["w"], "obstacle.w")))
            h = max(16.0, min(300.0, _finite_float(item["h"], "obstacle.h")))
        except (KeyError, TypeError, ValueError):
            continue
        parsed.append(
            PlantObstacle(
                id=str(item.get("id", f"obs_{idx}")),
                label=str(item.get("label", "Obstaculo")),
                kind=str(item.get("kind", "car_body")),
                x=x,
                y=y,
                w=w,
                h=h,
            )
        )
    return parsed


def compute_cspace(
    obstacles: List[PlantObstacle],
    target_x: float,
    target_y: float,
) -> Tuple[List[List[int]], Set[Tuple[int, int]]]:
    """
    Construye el Espacio de Configuraciones (72 x 72):
      - 0: configuracion libre
      - 1: colision con algun obstaculo de la planta
      - 2: configuracion libre que alcanza el punto objetivo (Meta)
    """
    grid = [[0] * GRID_N for _ in range(GRID_N)]
    goals: Set[Tuple[int, int]] = set()
    tol_sq = GOAL_TOLERANCE * GOAL_TOLERANCE

    for i1 in range(GRID_N):
        a1 = math.radians(i1 * STEP_DEG)
        ex = BASE_X + L1 * math.cos(a1)
        ey = BASE_Y - L1 * math.sin(a1)

        # Verificar si el primer eslabon (hombro->codo) ya colisiona
        link1_hit = any(
            _segment_intersects_aabb(BASE_X, BASE_Y, ex, ey, ob.x, ob.y, ob.w, ob.h)
            for ob in obstacles
        )
        if link1_hit:
            grid[i1] = [1] * GRID_N
            continue

        row = grid[i1]
        for i2 in range(GRID_N):
            a2 = math.radians((i1 + i2) * STEP_DEG)
            tx = ex + L2 * math.cos(a2)
            ty = ey - L2 * math.sin(a2)

            if any(
                _segment_intersects_aabb(ex, ey, tx, ty, ob.x, ob.y, ob.w, ob.h)
                for ob in obstacles
            ):
                row[i2] = 1
            else:
                dx = tx - target_x
                dy = ty - target_y
                if dx * dx + dy * dy <= tol_sq:
                    row[i2] = 2
                    goals.add((i1, i2))

    return grid, goals


def circular_step_dist(a: int, b: int) -> int:
    """Distancia minima en pasos sobre un circulo de GRID_N (72) posiciones."""
    d = abs(a - b)
    return min(d, GRID_N - d)


def angular_heuristic(
    node: Tuple[int, int],
    goals: Set[Tuple[int, int]],
) -> float:
    """Heuristica admisible de energia minima hasta la configuracion meta mas cercana."""
    if not goals:
        return 0.0
    i1, i2 = node
    best = float("inf")
    for g1, g2 in goals:
        h = COST_SHOULDER * circular_step_dist(i1, g1) + COST_ELBOW * circular_step_dist(i2, g2)
        if h < best:
            best = h
    return best


def _neighbors(i1: int, i2: int) -> Tuple[Tuple[int, int, float], ...]:
    """4 vecinos en el espacio toroidal (theta1, theta2) con su costo energetico."""
    return (
        ((i1 + 1) % GRID_N, i2, COST_SHOULDER),
        ((i1 - 1) % GRID_N, i2, COST_SHOULDER),
        (i1, (i2 + 1) % GRID_N, COST_ELBOW),
        (i1, (i2 - 1) % GRID_N, COST_ELBOW),
    )


def _reconstruct(
    parents: Dict[Tuple[int, int], Optional[Tuple[int, int]]],
    goal: Tuple[int, int],
) -> List[Tuple[int, int]]:
    path: List[Tuple[int, int]] = []
    curr: Optional[Tuple[int, int]] = goal
    while curr is not None:
        path.append(curr)
        curr = parents.get(curr)
    path.reverse()
    return path


def _path_energy(path: List[Tuple[int, int]]) -> float:
    energy = 0.0
    for idx in range(1, len(path)):
        p1, p2 = path[idx - 1]
        c1, c2 = path[idx]
        if c1 != p1:
            energy += COST_SHOULDER
        if c2 != p2:
            energy += COST_ELBOW
    return round(energy, 1)


def solve_arm_motion(
    algorithm: str = "astar",
    start_deg: Tuple[int, int] = (210, 35),
    target: Tuple[float, float] = (325.0, 125.0),
    raw_obstacles: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Ejecuta la busqueda en el C-Space del brazo robotico 2D en Python.
    Delega en el motor unificado _solve_stage_on_cspace para evitar duplicacion.
    """
    algo = (algorithm or "astar").strip().lower()
    if algo not in ALGORITHMS_INFO:
        raise ValueError(f"Algoritmo no soportado: '{algorithm}'")

    d1, d2 = validate_start_deg(start_deg)
    if not isinstance(target, (list, tuple)) or len(target) < 2:
        raise ValueError("target debe contener [x, y]")
    tx = _finite_float(target[0], "target[0]")
    ty = _finite_float(target[1], "target[1]")

    obstacles = parse_obstacles(raw_obstacles)
    start = (
        round((d1 % 360) / STEP_DEG) % GRID_N,
        round((d2 % 360) / STEP_DEG) % GRID_N,
    )

    t0 = time.perf_counter()
    base_grid, tips = compute_base_cspace(obstacles)
    cspace, goals = mark_goals_on_cspace(base_grid, tips, tx, ty)
    stage_res = _solve_stage_on_cspace(algo, start, cspace, goals, tx, ty)
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return {
        "algorithm": ALGORITHMS_INFO[algo],
        "status": stage_res["status"],
        "found": stage_res["found"],
        "reason": stage_res["reason"],
        "start": stage_res["start"],
        "target": [tx, ty],
        "cspace": stage_res["cspace"],
        "explored": stage_res["explored"],
        "path": stage_res["path"],
        "path_frames": stage_res["path_frames"],
        "nodes_expanded": stage_res["nodes_expanded"],
        "energy": stage_res["energy"],
        "steps": stage_res["steps"],
        "is_optimal": stage_res["is_optimal"],
        "execution_time_ms": elapsed_ms,
    }


def _quick_astar_energy(
    cspace: List[List[int]],
    start: Tuple[int, int],
    goals: Set[Tuple[int, int]],
) -> Optional[float]:
    counter = 0
    heap: List[Tuple[float, int, Tuple[int, int], float]] = [(angular_heuristic(start, goals), counter, start, 0.0)]
    best_g: Dict[Tuple[int, int], float] = {start: 0.0}
    closed: Set[Tuple[int, int]] = set()
    while heap:
        _, _, curr, g_val = heapq.heappop(heap)
        if curr in closed:
            continue
        if curr in goals:
            return round(g_val, 1)
        closed.add(curr)
        for n1, n2, step_e in _neighbors(*curr):
            if cspace[n1][n2] == 1 or (n1, n2) in closed:
                continue
            new_g = g_val + step_e
            if new_g < best_g.get((n1, n2), float("inf")):
                best_g[(n1, n2)] = new_g
                counter += 1
                heapq.heappush(heap, (new_g + angular_heuristic((n1, n2), goals), counter, (n1, n2), new_g))
    return None


def compare_arm_algorithms(
    start_deg: Tuple[int, int] = (210, 35),
    target: Tuple[float, float] = (325.0, 125.0),
    raw_obstacles: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Ejecuta los 5 algoritmos sobre la misma celda robotica y compara eficiencia y fallos."""
    results = []
    for algo_id in ("astar", "ucs", "greedy", "bfs", "dfs"):
        res = solve_arm_motion(
            algorithm=algo_id,
            start_deg=start_deg,
            target=target,
            raw_obstacles=raw_obstacles,
        )
        results.append({
            "algorithm_id": algo_id,
            "algorithm_name": res["algorithm"]["name"],
            "paradigm": res["algorithm"]["paradigm"],
            "found": res["found"],
            "status": res["status"],
            "reason": res["reason"],
            "is_optimal": res["is_optimal"],
            "nodes_expanded": res["nodes_expanded"],
            "energy": res["energy"],
            "steps": res["steps"],
            "execution_time_ms": res["execution_time_ms"],
        })
    return {"comparisons": results}


def get_presets_payload() -> Dict[str, Any]:
    """Devuelve escenarios reales de planta y geometria del robot."""
    presets = []
    for p in PRESET_SCENARIOS.values():
        presets.append({
            "id": p["id"],
            "name": p["name"],
            "description": p["description"],
            "start_deg": list(p["start_deg"]),
            "target": list(p["target"]),
            "obstacles": [
                {"id": o.id, "label": o.label, "kind": o.kind, "x": o.x, "y": o.y, "w": o.w, "h": o.h}
                for o in p["obstacles"]
            ],
        })

    tasks = []
    for t in TASK_PRESETS.values():
        tasks.append({
            "id": t["id"],
            "name": t["name"],
            "subtitle": t["subtitle"],
            "start_deg": list(t["start_deg"]),
            "waypoints": [dict(w) for w in t["waypoints"]],
            "obstacles": [
                {"id": o.id, "label": o.label, "kind": o.kind, "x": o.x, "y": o.y, "w": o.w, "h": o.h}
                for o in t["obstacles"]
            ],
            "unexpected": dict(t["unexpected"]),
        })

    return {
        "base": [BASE_X, BASE_Y],
        "l1": L1,
        "l2": L2,
        "grid_n": GRID_N,
        "step_deg": STEP_DEG,
        "goal_tolerance": GOAL_TOLERANCE,
        "presets": presets,
        "tasks": tasks,
        "algorithms": list(ALGORITHMS_INFO.values()),
    }


def compute_base_cspace(obstacles: List[PlantObstacle]) -> Tuple[List[List[int]], List[List[Tuple[float, float]]]]:
    """
    Precalcula el mapa de colisiones (0 libre, 1 colision) y las posiciones del efector final
    una sola vez por configuracion de obstaculos para acelerar secuencias multi-punto.
    """
    grid = [[0] * GRID_N for _ in range(GRID_N)]
    tips: List[List[Tuple[float, float]]] = [[(0.0, 0.0)] * GRID_N for _ in range(GRID_N)]

    for i1 in range(GRID_N):
        a1 = math.radians(i1 * STEP_DEG)
        ex = BASE_X + L1 * math.cos(a1)
        ey = BASE_Y - L1 * math.sin(a1)

        if any(_segment_intersects_aabb(BASE_X, BASE_Y, ex, ey, ob.x, ob.y, ob.w, ob.h) for ob in obstacles):
            grid[i1] = [1] * GRID_N
            continue

        row = grid[i1]
        tip_row = tips[i1]
        for i2 in range(GRID_N):
            a2 = math.radians((i1 + i2) * STEP_DEG)
            tx = ex + L2 * math.cos(a2)
            ty = ey - L2 * math.sin(a2)
            tip_row[i2] = (tx, ty)
            if any(_segment_intersects_aabb(ex, ey, tx, ty, ob.x, ob.y, ob.w, ob.h) for ob in obstacles):
                row[i2] = 1

    return grid, tips


def mark_goals_on_cspace(
    base_grid: List[List[int]],
    tips: List[List[Tuple[float, float]]],
    target_x: float,
    target_y: float,
) -> Tuple[List[List[int]], Set[Tuple[int, int]]]:
    """Clona el mapa de colisiones y marca con 2 los estados libres que alcanzan (target_x, target_y)."""
    tol_sq = GOAL_TOLERANCE * GOAL_TOLERANCE
    cspace = [row[:] for row in base_grid]
    goals: Set[Tuple[int, int]] = set()

    for i1 in range(GRID_N):
        row = cspace[i1]
        tip_row = tips[i1]
        for i2 in range(GRID_N):
            if row[i2] == 0:
                tx, ty = tip_row[i2]
                dx = tx - target_x
                dy = ty - target_y
                if dx * dx + dy * dy <= tol_sq:
                    row[i2] = 2
                    goals.add((i1, i2))
    return cspace, goals


def _solve_stage_on_cspace(
    algo: str,
    start: Tuple[int, int],
    cspace: List[List[int]],
    goals: Set[Tuple[int, int]],
    tx: float,
    ty: float,
) -> Dict[str, Any]:
    """Ejecuta un algoritmo de busqueda sobre un C-Space ya construido."""
    s1, s2 = start
    if cspace[s1][s2] == 1:
        return {
            "status": "start_blocked",
            "found": False,
            "reason": "El brazo quedo bloqueado por un obstaculo en su postura actual.",
            "start": [s1, s2],
            "cspace": cspace,
            "explored": [],
            "path": [],
            "path_frames": [],
            "end_node": None,
            "nodes_expanded": 0,
            "energy": 0.0,
            "steps": 0,
            "is_optimal": False,
        }

    if not goals:
        dist_from_base = math.hypot(tx - BASE_X, ty - BASE_Y)
        reason = (
            "Uno de los puntos objetivo quedo fuera del alcance del brazo."
            if dist_from_base > (L1 + L2 + GOAL_TOLERANCE) or dist_from_base < abs(L1 - L2) - GOAL_TOLERANCE
            else "Un obstaculo bloquea todos los angulos para alcanzar el siguiente punto."
        )
        return {
            "status": "unreachable_goal",
            "found": False,
            "reason": reason,
            "start": [s1, s2],
            "cspace": cspace,
            "explored": [],
            "path": [],
            "path_frames": [],
            "end_node": None,
            "nodes_expanded": 0,
            "energy": 0.0,
            "steps": 0,
            "is_optimal": False,
        }

    explored_order: List[Tuple[int, int]] = []
    found_goal: Optional[Tuple[int, int]] = None
    parents: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    failure_reason = ""

    if algo == "bfs":
        q: deque[Tuple[int, int]] = deque([start])
        seen: Set[Tuple[int, int]] = {start}
        while q:
            curr = q.popleft()
            explored_order.append(curr)
            if curr in goals:
                found_goal = curr
                break
            for n1, n2, _ in _neighbors(*curr):
                if cspace[n1][n2] != 1 and (n1, n2) not in seen:
                    seen.add((n1, n2))
                    parents[(n1, n2)] = curr
                    q.append((n1, n2))

    elif algo == "dfs":
        max_dfs = 900
        stack: List[Tuple[Tuple[int, int], Optional[Tuple[int, int]]]] = [(start, None)]
        visited: Set[Tuple[int, int]] = set()
        while stack:
            if len(explored_order) >= max_dfs:
                failure_reason = f"Se perdio dando vueltas y agoto su limite de {max_dfs} posturas."
                break
            curr, parent_node = stack.pop()
            if curr in visited:
                continue
            visited.add(curr)
            parents[curr] = parent_node
            explored_order.append(curr)
            if curr in goals:
                found_goal = curr
                break
            for n1, n2, _ in reversed(_neighbors(*curr)):
                if cspace[n1][n2] != 1 and (n1, n2) not in visited:
                    stack.append(((n1, n2), curr))

    else:
        counter = 0
        h0 = angular_heuristic(start, goals)
        f0 = 0.0 if algo == "ucs" else h0
        heap: List[Tuple[float, int, Tuple[int, int], float]] = [(f0, counter, start, 0.0)]
        best_g: Dict[Tuple[int, int], float] = {start: 0.0}
        closed: Set[Tuple[int, int]] = set()
        max_exp = 1800 if algo == "greedy" else 6000

        while heap:
            if len(explored_order) >= max_exp:
                failure_reason = f"Agoto el limite de {max_exp} posturas sin lograr rodear el obstaculo."
                break
            _, _, curr, g_val = heapq.heappop(heap)
            if curr in closed:
                continue
            if algo in ("ucs", "astar") and g_val > best_g.get(curr, float("inf")):
                continue
            closed.add(curr)
            explored_order.append(curr)
            if curr in goals:
                found_goal = curr
                break

            for n1, n2, step_e in _neighbors(*curr):
                if cspace[n1][n2] == 1 or (n1, n2) in closed:
                    continue
                new_g = g_val + step_e
                if algo == "greedy":
                    if (n1, n2) in best_g:
                        continue
                    best_g[(n1, n2)] = new_g
                    parents[(n1, n2)] = curr
                    counter += 1
                    heapq.heappush(heap, (angular_heuristic((n1, n2), goals), counter, (n1, n2), new_g))
                else:
                    if new_g < best_g.get((n1, n2), float("inf")):
                        best_g[(n1, n2)] = new_g
                        parents[(n1, n2)] = curr
                        h_val = angular_heuristic((n1, n2), goals) if algo == "astar" else 0.0
                        counter += 1
                        heapq.heappush(heap, (new_g + h_val, counter, (n1, n2), new_g))

    path = _reconstruct(parents, found_goal) if found_goal is not None else []
    energy = _path_energy(path) if path else 0.0
    is_optimal = False
    if found_goal is not None:
        if algo in ("astar", "ucs"):
            is_optimal = True
        else:
            ref_opt = _quick_astar_energy(cspace, start, goals)
            is_optimal = ref_opt is not None and abs(energy - ref_opt) <= 0.05

    path_frames = []
    for i1, i2 in path:
        ex, ey, tip_x, tip_y = forward_kinematics(i1, i2)
        path_frames.append({
            "i1": i1,
            "i2": i2,
            "deg1": i1 * STEP_DEG,
            "deg2": i2 * STEP_DEG,
            "ex": round(ex, 1),
            "ey": round(ey, 1),
            "tx": round(tip_x, 1),
            "ty": round(tip_y, 1),
        })

    if found_goal is None and not failure_reason:
        failure_reason = "No existe ningun camino libre hacia el siguiente objetivo."

    return {
        "status": "solved" if found_goal is not None else "failed",
        "found": found_goal is not None,
        "reason": failure_reason,
        "start": [s1, s2],
        "cspace": cspace,
        "explored": [list(pt) for pt in explored_order],
        "path": [list(pt) for pt in path],
        "path_frames": path_frames,
        "end_node": list(found_goal) if found_goal is not None else None,
        "nodes_expanded": len(explored_order),
        "energy": energy,
        "steps": max(0, len(path) - 1),
        "is_optimal": is_optimal,
    }


def solve_arm_sequence(
    algorithm: str = "astar",
    start_deg: Tuple[int, int] = (155, 340),
    waypoints: Optional[List[Dict[str, Any]]] = None,
    raw_obstacles: Optional[List[Dict[str, Any]]] = None,
    precomputed: Optional[Tuple[List[List[int]], List[List[Tuple[float, float]]]]] = None,
) -> Dict[str, Any]:
    """
    Planifica una tarea practica completa multi-etapa (Pick & Place o Soldadura Multi-punto).
    Cada etapa parte desde la postura final alcanzada en la etapa anterior.
    """
    algo = (algorithm or "astar").strip().lower()
    if algo not in ALGORITHMS_INFO:
        raise ValueError(f"Algoritmo no soportado: '{algorithm}'")

    d1, d2 = validate_start_deg(start_deg)
    valid_waypoints = validate_waypoints(waypoints)
    t0 = time.perf_counter()

    if precomputed is not None:
        base_grid, tips = precomputed
    else:
        obstacles = parse_obstacles(raw_obstacles)
        base_grid, tips = compute_base_cspace(obstacles)

    curr_start = (
        round((d1 % 360) / STEP_DEG) % GRID_N,
        round((d2 % 360) / STEP_DEG) % GRID_N,
    )

    stages: List[Dict[str, Any]] = []
    total_expanded = 0
    total_energy = 0.0
    total_steps = 0
    all_found = True
    all_optimal = True
    failure_reason = ""

    for idx, wp in enumerate(valid_waypoints):
        wx = wp["x"]
        wy = wp["y"]
        cspace, goals = mark_goals_on_cspace(base_grid, tips, wx, wy)
        stage_res = _solve_stage_on_cspace(algo, curr_start, cspace, goals, wx, wy)

        stage_entry = {
            "stage_index": idx,
            "label": wp["label"],
            "action": wp["action"],
            "target": [wx, wy],
            **stage_res,
        }
        stages.append(stage_entry)
        total_expanded += stage_res["nodes_expanded"]
        total_energy += stage_res["energy"]
        total_steps += stage_res["steps"]
        if not stage_res["is_optimal"]:
            all_optimal = False

        if not stage_res["found"]:
            all_found = False
            failure_reason = f"Se detuvo en '{stage_entry['label']}': {stage_res['reason']}"
            break

        curr_start = tuple(stage_res["end_node"])  # type: ignore[assignment]

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    completed_stages = sum(1 for s in stages if s["found"])
    cycle_seconds = round(total_steps * 0.08 + total_expanded * 0.0012, 1)

    return {
        "algorithm": ALGORITHMS_INFO[algo],
        "found": all_found,
        "is_optimal": all_found and all_optimal,
        "reason": failure_reason,
        "completed_stages": completed_stages,
        "total_stages": len(valid_waypoints),
        "nodes_expanded": total_expanded,
        "energy": round(total_energy, 1),
        "steps": total_steps,
        "cycle_seconds": cycle_seconds,
        "execution_time_ms": elapsed_ms,
        "stages": stages,
    }


def compare_arm_sequences(
    start_deg: Tuple[int, int] = (155, 340),
    waypoints: Optional[List[Dict[str, Any]]] = None,
    raw_obstacles: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compara las 5 estrategias reutilizando el mapa de colisiones base en Python."""
    d1, d2 = validate_start_deg(start_deg)
    valid_waypoints = validate_waypoints(waypoints)
    obstacles = parse_obstacles(raw_obstacles)
    precomputed = compute_base_cspace(obstacles)

    results = []
    for algo_id in ("astar", "ucs", "greedy", "bfs", "dfs"):
        res = solve_arm_sequence(
            algorithm=algo_id,
            start_deg=(d1, d2),
            waypoints=valid_waypoints,
            precomputed=precomputed,
        )
        results.append({
            "algorithm_id": algo_id,
            "algorithm_name": res["algorithm"]["name"],
            "found": res["found"],
            "is_optimal": res["is_optimal"],
            "reason": res["reason"],
            "completed_stages": res["completed_stages"],
            "total_stages": res["total_stages"],
            "nodes_expanded": res["nodes_expanded"],
            "energy": res["energy"],
            "steps": res["steps"],
            "cycle_seconds": res["cycle_seconds"],
            "execution_time_ms": res["execution_time_ms"],
        })
    return {"comparisons": results}


if __name__ == "__main__":
    for pid, sc in PRESET_SCENARIOS.items():
        print(f"\n=== ESCENARIO: {sc['name']} ===")
        cmp = compare_arm_algorithms(sc["start_deg"], sc["target"], [
            {"id": o.id, "label": o.label, "kind": o.kind, "x": o.x, "y": o.y, "w": o.w, "h": o.h}
            for o in sc["obstacles"]
        ])
        for row in cmp["comparisons"]:
            status = "OPTIMA" if row["is_optimal"] else ("LLEGO (NO OPT)" if row["found"] else "FALLO")
            print(
                f"[{row['algorithm_name']:<18}] {status:<14} | "
                f"Expandidos: {row['nodes_expanded']:>4} | Energia: {row['energy']:>5.1f} | "
                f"Pasos: {row['steps']:>3} | {row['execution_time_ms']:>5.1f} ms"
            )
