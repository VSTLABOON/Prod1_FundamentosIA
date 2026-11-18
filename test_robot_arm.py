"""
test_robot_arm.py
Pruebas unitarias y de integracion Flask para el Brazo Robotico 3D,
la Bitacora SQLite, Memoria de Rutas (CBR) y Mini-RAG.
"""

import os
import tempfile
import unittest

import arm_storage
import database as db
import robot_arm_search
from app import app


class TestRobotArmSearch(unittest.TestCase):
    def test_all_presets_solve_with_astar_more_efficient_than_ucs(self):
        for pid, sc in robot_arm_search.PRESET_SCENARIOS.items():
            obs = [vars(o) for o in sc["obstacles"]]
            astar = robot_arm_search.solve_arm_motion("astar", sc["start_deg"], sc["target"], obs)
            ucs = robot_arm_search.solve_arm_motion("ucs", sc["start_deg"], sc["target"], obs)

            self.assertTrue(astar["found"], f"A* fallo en preset {pid}")
            self.assertTrue(astar["is_optimal"])
            self.assertTrue(ucs["found"])
            self.assertAlmostEqual(astar["energy"], ucs["energy"], places=1)
            self.assertLess(astar["nodes_expanded"], ucs["nodes_expanded"])

    def test_dfs_fails_and_greedy_takes_suboptimal_detour(self):
        sc = robot_arm_search.PRESET_SCENARIOS["narrow_chassis"]
        obs = [vars(o) for o in sc["obstacles"]]

        dfs = robot_arm_search.solve_arm_motion("dfs", sc["start_deg"], sc["target"], obs)
        self.assertFalse(dfs["found"])
        self.assertEqual(dfs["status"], "failed")

        greedy = robot_arm_search.solve_arm_motion("greedy", sc["start_deg"], sc["target"], obs)
        self.assertTrue(greedy["found"])
        self.assertFalse(greedy["is_optimal"])

    def test_dfs_path_transitions_are_valid_steps(self):
        sc = robot_arm_search.PRESET_SCENARIOS["double_barrier"]
        obs = [vars(o) for o in sc["obstacles"]]
        dfs = robot_arm_search.solve_arm_motion("dfs", sc["start_deg"], sc["target"], obs)
        self.assertTrue(dfs["found"])
        path = dfs["path"]
        for i in range(1, len(path)):
            d1 = robot_arm_search.circular_step_dist(path[i][0], path[i - 1][0])
            d2 = robot_arm_search.circular_step_dist(path[i][1], path[i - 1][1])
            self.assertEqual(d1 + d2, 1)

    def test_unreachable_goal_detected_cleanly(self):
        res = robot_arm_search.solve_arm_motion("astar", (165, 340), (430.0, 360.0), [])
        self.assertFalse(res["found"])
        self.assertEqual(res["status"], "unreachable_goal")

    def test_all_practical_tasks_complete_and_reroute_around_unexpected(self):
        for tid, task in robot_arm_search.TASK_PRESETS.items():
            obs = [vars(o) for o in task["obstacles"]]
            astar = robot_arm_search.solve_arm_sequence("astar", task["start_deg"], task["waypoints"], obs)
            self.assertTrue(astar["found"], f"A* fallo en tarea practica {tid}")
            self.assertEqual(astar["completed_stages"], len(task["waypoints"]))

            astar_unexp = robot_arm_search.solve_arm_sequence(
                "astar", task["start_deg"], task["waypoints"], obs + [task["unexpected"]]
            )
            self.assertTrue(astar_unexp["found"], f"A* fallo con imprevisto en {tid}")

            dfs = robot_arm_search.solve_arm_sequence("dfs", task["start_deg"], task["waypoints"], obs)
            self.assertFalse(dfs["found"], f"Se esperaba fallo de DFS en {tid}")


class TestFlaskArmEndpoints(unittest.TestCase):
    def setUp(self):
        self.orig_db_path = db.DB_PATH
        self.tmp_dir = tempfile.TemporaryDirectory()
        db.DB_PATH = os.path.join(self.tmp_dir.name, "test_glossary.db")
        db.init_db()
        arm_storage.init_arm_tables()
        self.client = app.test_client()

    def tearDown(self):
        db.DB_PATH = self.orig_db_path
        self.tmp_dir.cleanup()

    def test_health_and_index_render_brazo_section(self):
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()["status"], "ok")

        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("sectionBrazo", html)
        self.assertIn("brazo_robotico.js", html)

    def test_arm_presets_solve_and_compare_endpoints(self):
        presets_resp = self.client.get("/api/arm/presets")
        self.assertEqual(presets_resp.status_code, 200)
        data = presets_resp.get_json()["data"]
        self.assertEqual(len(data["presets"]), 3)
        self.assertEqual(len(data["tasks"]), 3)

        solve_resp = self.client.post(
            "/api/arm/solve",
            json={"algorithm": "astar", "start_deg": [165, 340], "target": [335, 130]},
        )
        self.assertEqual(solve_resp.status_code, 200)
        self.assertTrue(solve_resp.get_json()["data"]["found"])

        seq_resp = self.client.post(
            "/api/arm/solve-sequence",
            json={"algorithm": "astar", "start_deg": [170, 15]},
        )
        self.assertEqual(seq_resp.status_code, 200)
        self.assertTrue(seq_resp.get_json()["data"]["found"])

        cmp_seq_resp = self.client.post(
            "/api/arm/compare-sequence",
            json={"start_deg": [170, 15]},
        )
        self.assertEqual(cmp_seq_resp.status_code, 200)
        self.assertEqual(len(cmp_seq_resp.get_json()["data"]["comparisons"]), 5)

    def test_arm_validation_rejects_malformed_inputs_with_400(self):
        self.assertEqual(
            self.client.post("/api/arm/solve-sequence", json={"algorithm": "invalido"}).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/api/arm/solve-sequence", json={"waypoints": [{}]}).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/api/arm/solve-sequence", json={"waypoints": []}).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/api/arm/solve-sequence", json={"start_deg": [10]}).status_code,
            400,
        )
        self.assertEqual(
            self.client.delete("/api/arm/history?scope=invalid").status_code,
            400,
        )

    def test_sql_history_route_memory_and_mini_rag(self):
        r1 = self.client.post(
            "/api/arm/solve-sequence",
            json={
                "task_id": "pick_and_place",
                "task_name": "Pick & Place",
                "algorithm": "astar",
                "start_deg": [170, 15],
                "use_memory": True,
                "record_run": True,
            },
        )
        self.assertEqual(r1.status_code, 200)
        self.assertTrue(r1.get_json()["data"]["found"])
        self.assertFalse(r1.get_json()["data"]["from_cache"])

        r2 = self.client.post(
            "/api/arm/solve-sequence",
            json={
                "task_id": "pick_and_place",
                "task_name": "Pick & Place",
                "algorithm": "astar",
                "start_deg": [170, 15],
                "use_memory": True,
                "record_run": True,
            },
        )
        self.assertEqual(r2.status_code, 200)
        self.assertTrue(r2.get_json()["data"]["from_cache"])

        r3 = self.client.post(
            "/api/arm/solve-sequence",
            json={
                "task_id": "pick_and_place",
                "task_name": "Pick & Place",
                "algorithm": "dfs",
                "start_deg": [170, 15],
                "use_memory": True,
                "record_run": True,
            },
        )
        self.assertEqual(r3.status_code, 200)
        self.assertFalse(r3.get_json()["data"]["found"])

        hist = self.client.get("/api/arm/history?filter=all")
        self.assertEqual(hist.status_code, 200)
        hdata = hist.get_json()["data"]
        self.assertEqual(hdata["kpis"]["total_runs"], 3)
        self.assertEqual(hdata["kpis"]["total_failures"], 1)
        self.assertEqual(hdata["kpis"]["total_from_cache"], 1)
        self.assertEqual(hdata["kpis"]["cache_count"], 1)

        rag_fail = self.client.post("/api/arm/rag", json={"question": "¿Que estrategia fallo mas?"})
        self.assertEqual(rag_fail.status_code, 200)
        self.assertIn("Profundidad", rag_fail.get_json()["data"]["answer"])

        rag_energy = self.client.post("/api/arm/rag", json={"question": "¿Cual gasto menos energia?"})
        self.assertEqual(rag_energy.status_code, 200)
        self.assertGreater(len(rag_energy.get_json()["data"]["sources"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
