import ast
import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE = (ROOT / "server" / "main.py").read_text()
ast.parse(SOURCE)

class ServerContractTests(unittest.TestCase):
    def test_fastapi_app_and_routes_exist(self):
        self.assertIn("FastAPI(", SOURCE)
        for route in ("/api/health", "/api/workspace", "/api/readiness", "/api/tasks", "/api/agent-check"):
            self.assertIn(route, SOURCE)

    def test_task_contracts_validate_and_handle_unknown_ids(self):
        self.assertIn("TaskCreate", SOURCE); self.assertIn("TaskUpdate", SOURCE)
        self.assertIn("max_length=120", SOURCE); self.assertIn("Literal[\"high\", \"medium\", \"low\"]", SOURCE)
        self.assertIn("title.strip()", SOURCE); self.assertGreaterEqual(SOURCE.count("HTTPException(404"), 2)

    def test_planning_boundary_and_safe_copy_are_explicit(self):
        self.assertIn("planning-only", SOURCE); self.assertIn("no model artifact", SOURCE)
        self.assertIn("deepcopy(state)", SOURCE)

    def test_vite_proxy_matches_api_prefix(self):
        config = (ROOT / "client" / "vite.config.js").read_text()
        client = (ROOT / "client" / "src" / "main.js").read_text()
        self.assertIn('"/api"', config); self.assertIn("target: \"http://127.0.0.1:8000\"", config)
        self.assertIn("VITE_API_BASE_URL", client); self.assertIn('api("/workspace")', client)

    def test_api_behavior_when_fastapi_is_installed(self):
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("FastAPI dependencies are optional for static contract checks")
        sys.path.insert(0, str(ROOT / "server"))
        try:
            server = importlib.import_module("main")
            server.state = server.deepcopy(server.SEED)
            client = TestClient(server.app)
            response = client.post("/api/tasks", json={"title": "Profile holiday flags", "priority": "high"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()[0]["title"], "Profile holiday flags")
            self.assertEqual(client.post("/api/tasks", json={"title": "   "}).status_code, 422)
            self.assertEqual(client.patch("/api/tasks/999", json={"done": True}).status_code, 404)
            self.assertEqual(client.delete("/api/tasks/999").status_code, 404)
        finally:
            sys.path.pop(0)
