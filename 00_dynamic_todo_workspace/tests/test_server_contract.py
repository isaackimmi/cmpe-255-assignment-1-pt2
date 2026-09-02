import ast
import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SERVER = ROOT / "server"


class ServerContractTests(unittest.TestCase):
    def test_server_is_split_into_focused_layers(self):
        expected = (
            "main.py",
            "app/factory.py",
            "app/api/routes.py",
            "app/models/schemas.py",
            "app/repositories/workspace.py",
            "app/services/workspace.py",
        )
        for relative_path in expected:
            source = (SERVER / relative_path).read_text()
            ast.parse(source)
        self.assertLess(len((SERVER / "main.py").read_text().splitlines()), 10)

    def test_routes_and_validation_contracts_remain_explicit(self):
        routes = (SERVER / "app/api/routes.py").read_text()
        schemas = (SERVER / "app/models/schemas.py").read_text()
        service = (SERVER / "app/services/workspace.py").read_text()
        for route in ("/health", "/workspace", "/readiness", "/tasks", "/agent-check"):
            self.assertIn(route, routes)
        self.assertIn("max_length=120", schemas)
        self.assertIn('Literal["high", "medium", "low"]', schemas)
        self.assertIn("title = request.title.strip()", service)
        self.assertGreaterEqual(service.count("status_code=404"), 2)

    def test_planning_boundary_and_safe_copy_are_explicit(self):
        seed = (SERVER / "app/repositories/seed.py").read_text()
        repository = (SERVER / "app/repositories/workspace.py").read_text()
        self.assertIn("planning-only", seed)
        self.assertIn("no model artifact", seed)
        self.assertGreaterEqual(repository.count("deepcopy"), 4)

    def test_react_client_has_composable_layers_and_radix_primitives(self):
        package = (ROOT / "client/package.json").read_text()
        lockfile = (ROOT / "client/package-lock.json").read_text()
        api = (ROOT / "client/src/services/api.js").read_text()
        hook = (ROOT / "client/src/hooks/useWorkspace.js").read_text()
        components = list((ROOT / "client/src/components").rglob("*.jsx"))
        self.assertIn('"react"', package)
        self.assertIn('"@radix-ui/react-checkbox"', package)
        self.assertIn('"vitest"', package)
        self.assertIn('"lockfileVersion": 3', lockfile)
        self.assertIn("VITE_API_BASE_URL", api)
        self.assertIn("workspaceApi.getWorkspace", hook)
        self.assertGreaterEqual(len(components), 12)

    def test_vite_proxy_matches_api_prefix(self):
        config = (ROOT / "client/vite.config.js").read_text()
        self.assertIn('"/api"', config)
        self.assertIn('target: "http://127.0.0.1:8000"', config)
        self.assertIn("react()", config)

    def test_routes_use_services_and_typed_responses(self):
        routes = (SERVER / "app/api/routes.py").read_text()
        self.assertNotIn("service.repository", routes)
        self.assertIn("response_model=WorkspaceResponse", routes)
        self.assertIn("response_model=list[TaskResponse]", routes)

    def test_api_behavior_when_fastapi_is_installed(self):
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            self.skipTest("FastAPI dependencies are optional for static contract checks")
        sys.path.insert(0, str(SERVER))
        try:
            server = importlib.import_module("main")
            server.app.state.workspace_repository.reset()
            client = TestClient(server.app)
            response = client.post("/api/tasks", json={"title": "Profile holiday flags", "priority": "high"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()[0]["title"], "Profile holiday flags")
            self.assertEqual(client.post("/api/tasks", json={"title": "   "}).status_code, 422)
            self.assertEqual(client.patch("/api/tasks/999", json={"done": True}).status_code, 404)
            self.assertEqual(client.delete("/api/tasks/999").status_code, 404)
            self.assertEqual(client.post("/api/agent-check").json()["status"], "demo-only")
        finally:
            sys.path.pop(0)
