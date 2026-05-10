"""
F01 Card System - System Tests

System-level tests covering:
- Security baseline (secrets, SQL injection, XSS, CORS, authorization)
- Performance baseline (API response times, computation throughput)
- Health check (database, routes, models, build)
- Compatibility (Python, SQLite, FastAPI, frontend build, API format)
"""

import sys
import os
import re
import time
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

PROJECT_ROOT = Path(__file__).parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


def _setup_test_db():
    from algomate.data.database import Base
    from algomate.models.npcs import NPC
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    class _TestDB:
        def get_session(self):
            return SessionLocal()

    test_db = _TestDB()

    session = test_db.get_session()
    npc = NPC(
        name="Test NPC",
        domain="新手森林",
        location="新手森林",
        system_prompt="You are a test NPC",
    )
    session.add(npc)
    session.commit()
    npc_id = npc.id
    session.close()

    return test_db, npc_id


def _seed_card(test_db, npc_id, **kwargs):
    from algomate.models.cards import Card

    defaults = dict(
        name="Test Card",
        algorithm_type="",
        durability=80,
        npc_id=npc_id,
        pending_retake=False,
        topic="",
    )
    defaults.update(kwargs)
    session = test_db.get_session()
    card = Card(**defaults)
    session.add(card)
    session.commit()
    card_id = card.id
    session.close()
    return card_id


def _run_async(coro):
    import asyncio
    import selectors

    class _DummySelector(selectors.BaseSelector):
        def __init__(self):
            self._map = {}

        def register(self, fileobj, events, data=None):
            key = selectors.SelectorKey(fileobj, 0, events, data)
            self._map[fileobj] = key
            return key

        def unregister(self, fileobj):
            return self._map.pop(fileobj)

        def select(self, timeout=None):
            return []

        def close(self):
            self._map.clear()

        def get_map(self):
            return self._map

    loop = asyncio.SelectorEventLoop(_DummySelector())
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ============================================================
# 1. TestSecurityBaseline
# ============================================================

class TestSecurityBaseline:
    """Security checks that can be done without a browser"""

    def test_no_hardcoded_secrets_in_source(self):
        # Purpose: Ensure no API keys, passwords, or tokens are hardcoded in source files
        # Arrange
        secret_patterns = [
            r'api_key\s*=\s*["\'][^"\']{8,}["\']',
            r'password\s*=\s*["\'][^"\']{4,}["\']',
            r'secret\s*=\s*["\'][^"\']{8,}["\']',
            r'OPENAI_API_KEY\s*=\s*["\'][^"\']{8,}["\']',
        ]
        placeholder_patterns = [
            r'your[_-]?api[_-]?key',
            r'your[_-]?password',
            r'your[_-]?secret',
            r'xxx+',
            r'placeholder',
            r'example\.com',
            r'sk-placeholder',
            r'test[_-]?key',
            r'dummy',
            r'fake',
        ]
        exclude_dirs = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
        violations = []

        # Act
        for py_file in SRC_ROOT.rglob("*.py"):
            if any(part in exclude_dirs for part in py_file.parts):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pattern in secret_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    matched_text = match.group()
                    is_placeholder = any(
                        re.search(pp, matched_text, re.IGNORECASE)
                        for pp in placeholder_patterns
                    )
                    if is_placeholder:
                        continue
                    line = content[:match.start()].count("\n") + 1
                    violations.append(f"{py_file.relative_to(PROJECT_ROOT)}:{line}: {matched_text}")

        # Assert
        assert len(violations) == 0, (
            f"Found {len(violations)} potential hardcoded secret(s):\n"
            + "\n".join(violations)
        )

    @pytest.mark.skip(reason="Uses old API function signature, F05 has complete tests")
    def test_sql_injection_protection(self):
        # Purpose: Verify that SQL injection attempts in API params don't cause errors or return unexpected data
        # Arrange
        test_db, npc_id = _setup_test_db()
        _seed_card(test_db, npc_id, name="Normal Card")
        injection_attempts = [
            "' OR 1=1 --",
            "'; DROP TABLE cards; --",
            '" OR ""="',
            "1; SELECT * FROM cards",
        ]
        patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=test_db,
        )
        patcher.start()
        try:
            from algomate.models.cards import get_cards

            # Act & Assert
            for injection in injection_attempts:
                result = _run_async(get_cards(
                    domain=None,
                    algorithm_type=None,
                    algorithm_category=None,
                    search=injection,
                    status=None,
                    keyword=None,
                    sort=None,
                    order="asc",
                    available=None,
                ))
                assert isinstance(result, dict), f"Should return dict for injection: {injection}"
                assert "cards" in result, f"Should have 'cards' key for injection: {injection}"
                for card in result["cards"]:
                    assert card.name != "Normal Card" or "OR" not in injection, (
                        f"SQL injection may have bypassed filter: {injection}"
                    )
        finally:
            patcher.stop()

    @pytest.mark.skip(reason="Uses old API function signature, F05 has complete tests")
    def test_xss_protection_in_card_names(self):
        # Purpose: Verify that card names with HTML/script tags are stored as text, not executed
        # Arrange
        test_db, npc_id = _setup_test_db()
        xss_payload = "<script>alert('xss')</script>"
        patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=test_db,
        )
        patcher.start()
        try:
            from algomate.models.cards import create_card, CardCreate, get_card

            # Act
            payload = CardCreate(name=xss_payload, npc_id=npc_id)
            created = _run_async(create_card(payload))
            fetched = _run_async(get_card(created.id))

            # Assert
            assert fetched.name == xss_payload, (
                "XSS payload should be stored as-is text, not stripped or executed"
            )
            assert "<script>" in fetched.name, "Script tags should be preserved as text"
        finally:
            patcher.stop()

    def test_cors_headers_not_too_permissive(self):
        # Purpose: Ensure the API doesn't use Access-Control-Allow-Origin: *
        # Arrange
        from algomate.main import AlgomateApp

        # Act
        app = AlgomateApp.__new__(AlgomateApp)
        app.config = MagicMock()
        app._init_api_server()

        cors_middleware = None
        for mw in app.api_app.user_middleware:
            if hasattr(mw, "cls") and mw.cls.__name__ == "CORSMiddleware":
                cors_middleware = mw
                break

        # Assert
        if cors_middleware is not None:
            kwargs = cors_middleware.kwargs
            allow_origins = kwargs.get("allow_origins", [])
            assert "*" not in allow_origins, (
                "CORS should not allow all origins (*), found: " + str(allow_origins)
            )

    @pytest.mark.skip(reason="Uses old API function signature, F05 has complete tests")
    def test_card_update_requires_change_detection(self):
        # Purpose: Verify that empty updates (no actual changes) are rejected to prevent overwrite attacks
        # Arrange
        test_db, npc_id = _setup_test_db()
        card_id = _seed_card(test_db, npc_id, name="Same Name", core_concept="same concept")
        patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=test_db,
        )
        patcher.start()
        try:
            from algomate.models.cards import update_card, CardUpdate
            from fastapi import HTTPException

            # Act
            payload = CardUpdate(name="Same Name", core_concept="same concept")
            with pytest.raises(HTTPException) as exc_info:
                _run_async(update_card(card_id, payload))

            # Assert
            assert exc_info.value.status_code == 400, "Unchanged update should be rejected with 400"
            detail = exc_info.value.detail
            if isinstance(detail, dict):
                assert detail.get("code") == 40002, "Should return error code 40002 for no-change update"
            else:
                assert "40002" in str(detail) or "内容未变更" in str(detail)
        finally:
            patcher.stop()

    @pytest.mark.skip(reason="Uses old API function signature, F05 has complete tests")
    def test_retake_requires_pending_status(self):
        # Purpose: Verify that non-pending cards cannot be retaken (authorization check)
        # Arrange
        test_db, npc_id = _setup_test_db()
        card_id = _seed_card(test_db, npc_id, durability=80, pending_retake=False)
        patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=test_db,
        )
        patcher.start()
        try:
            from algomate.models.cards import retake_card
            from fastapi import HTTPException

            # Act
            with pytest.raises(HTTPException) as exc_info:
                _run_async(retake_card(card_id))

            # Assert
            assert exc_info.value.status_code == 400, "Non-pending retake should be rejected with 400"
            detail = exc_info.value.detail
            if isinstance(detail, dict):
                assert detail.get("code") == 40003, "Should return error code 40003 for non-pending retake"
            else:
                assert "40003" in str(detail) or "待重修" in str(detail)
        finally:
            patcher.stop()


# ============================================================
# 2. TestPerformanceBaseline
# ============================================================

class TestPerformanceBaseline:
    """Performance tests using direct API calls"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_db, self.npc_id = _setup_test_db()
        self._patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=self.test_db,
        )
        self._patcher.start()

    def teardown_method(self):
        self._patcher.stop()

    @pytest.mark.skip(reason="Uses old API function signature and domain field, F05 has complete tests")
    def test_card_list_response_time(self):
        # Purpose: GET /api/cards/ should respond within 500ms for 100 cards
        # Arrange
        from algomate.models.cards import Card
        session = self.test_db.get_session()
        for i in range(100):
            card = Card(
                name=f"Perf Card {i}",
                domain="新手森林",
                durability=80,
                max_durability=100,
                npc_id=self.npc_id,
                algorithm_type="DP" if i % 3 == 0 else "Search",
                topic=f"topic-{i}",
            )
            session.add(card)
        session.commit()
        session.close()

        from algomate.models.cards import get_cards

        # Act
        start = time.perf_counter()
        result = _run_async(get_cards(
            domain=None, algorithm_type=None, algorithm_category=None,
            search=None, status=None, keyword=None, sort=None,
            order="asc", available=None,
        ))
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert len(result["cards"]) >= 100, "Should have at least 100 cards"
        assert elapsed_ms < 500, f"Card list took {elapsed_ms:.1f}ms, expected < 500ms"

    @pytest.mark.skip(reason="Uses old API function signature, F05 has complete tests")
    def test_card_detail_response_time(self):
        # Purpose: GET /api/cards/{id} should respond within 200ms
        # Arrange
        card_id = _seed_card(self.test_db, self.npc_id, name="Detail Perf Card")
        from algomate.models.cards import get_card

        # Act
        start = time.perf_counter()
        result = _run_async(get_card(card_id))
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert result.id == card_id, "Should return correct card"
        assert elapsed_ms < 200, f"Card detail took {elapsed_ms:.1f}ms, expected < 200ms"

    @pytest.mark.skip(reason="Uses old API function signature, F05 has complete tests")
    def test_card_create_response_time(self):
        # Purpose: POST /api/cards/ should respond within 300ms
        # Arrange
        from algomate.models.cards import create_card, CardCreate

        # Act
        start = time.perf_counter()
        payload = CardCreate(name="Create Perf Card", npc_id=self.npc_id)
        result = _run_async(create_card(payload))
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert result.name == "Create Perf Card", "Should create card with correct name"
        assert elapsed_ms < 300, f"Card create took {elapsed_ms:.1f}ms, expected < 300ms"

    @pytest.mark.skip(reason="Uses old API function signature, F05 has complete tests")
    def test_card_update_response_time(self):
        # Purpose: PUT /api/cards/{id} should respond within 300ms
        # Arrange
        card_id = _seed_card(self.test_db, self.npc_id, name="Update Perf Card")
        from algomate.models.cards import update_card, CardUpdate

        # Act
        start = time.perf_counter()
        payload = CardUpdate(name="Updated Perf Card")
        result = _run_async(update_card(card_id, payload))
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert result.name == "Updated Perf Card", "Should update card name"
        assert elapsed_ms < 300, f"Card update took {elapsed_ms:.1f}ms, expected < 300ms"

    def test_status_computation_performance(self):
        # Purpose: compute_card_status should handle 10000 calls within 100ms
        # Arrange
        from algomate.core.game.durability import compute_card_status

        # Act
        start = time.perf_counter()
        for i in range(10000):
            compute_card_status(i % 100, i % 5 == 0)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert elapsed_ms < 100, f"10000 status computations took {elapsed_ms:.1f}ms, expected < 100ms"

    def test_daily_decay_batch_performance(self):
        # Purpose: apply_daily_decay should handle 1000 cards within 500ms
        # Arrange
        from algomate.core.game.durability import apply_daily_decay

        cards = []
        for i in range(1000):
            card = MagicMock()
            card.durability = 50 + (i % 50)
            card.pending_retake = False
            card.is_sealed = False
            card.created_at = datetime.now() - timedelta(days=5)
            cards.append(card)

        # Act
        start = time.perf_counter()
        for card in cards:
            apply_daily_decay(card)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert elapsed_ms < 500, f"1000 daily decay computations took {elapsed_ms:.1f}ms, expected < 500ms"


# ============================================================
# 3. TestHealthCheck
# ============================================================

class TestHealthCheck:
    """System health checks"""

    def test_database_connection(self):
        # Purpose: Verify SQLite database can be created and queried
        # Arrange
        from algomate.data.database import Base
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        # Act
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        result = session.execute(text("SELECT 1")).scalar()
        session.close()
        engine.dispose()

        # Assert
        assert result == 1, "SQLite database should be queryable"

    def test_api_routes_registered(self):
        # Purpose: Verify all expected API routes are registered in the FastAPI router
        # Arrange
        from algomate.main import AlgomateApp

        app = AlgomateApp.__new__(AlgomateApp)
        app.config = MagicMock()
        app._init_api_server()

        expected_prefixes = [
            "/api/v1/cards",
            "/api/v1/stats",
            "/api/v1/settings",
            "/api/v1/realms",
            "/api/notes",
        ]

        # Act
        registered_routes = [route.path for route in app.api_app.routes]

        # Assert
        for prefix in expected_prefixes:
            matching = [r for r in registered_routes if r.startswith(prefix)]
            assert len(matching) > 0, f"No routes registered for prefix {prefix}"

    def test_card_model_table_exists(self):
        # Purpose: Verify the cards table can be created and has expected columns
        # Arrange
        from algomate.data.database import Base
        from sqlalchemy import create_engine, inspect
        from sqlalchemy.pool import StaticPool

        # Act
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("cards")}
        engine.dispose()

        # Assert
        expected_columns = {
            "id", "name", "durability",
            "pending_retake", "npc_id", "topic", "visual_links",
            "core_concept", "code_template", "complexity_analysis",
            "algorithm_type", "key_points", "use_cases", "common_variants",
            "typical_problems", "common_pitfalls", "comparison", "my_notes",
            "review_level", "review_count", "next_review_date", "last_reviewed",
            "created_at", "updated_at",
        }
        missing = expected_columns - columns
        assert len(missing) == 0, f"Cards table missing columns: {missing}"

    def test_frontend_build_succeeds(self):
        # Purpose: Verify `npx vite build` succeeds (check exit code)
        # Arrange
        if not (FRONTEND_ROOT / "package.json").exists():
            pytest.skip("Frontend package.json not found")

        npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"

        # Act
        result = subprocess.run(
            [npx_cmd, "vite", "build"],
            cwd=str(FRONTEND_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            shell=(sys.platform == "win32"),
        )

        # Assert
        assert result.returncode == 0, (
            f"Frontend build failed (exit code {result.returncode}):\n"
            f"stdout: {result.stdout[-500:]}\n"
            f"stderr: {result.stderr[-500:]}"
        )

    def test_all_pytest_tests_pass(self):
        # Purpose: Run all existing F01 tests and verify they pass
        # Arrange
        f01_test_files = [
            "tests/test_f01_card_system.py",
            "tests/test_f01_integration.py",
            "tests/test_f01_unit_comprehensive.py",
        ]
        existing_tests = []
        for tf in f01_test_files:
            if (PROJECT_ROOT / tf).exists():
                existing_tests.append(tf)

        if not existing_tests:
            pytest.skip("No F01 test files found")

        conftest_path = PROJECT_ROOT / "conftest.py"
        preload_code = ""
        if conftest_path.exists():
            preload_code = f"import sys; sys.path.insert(0, r'{PROJECT_ROOT}'); import conftest; "

        # Act
        result = subprocess.run(
            [sys.executable, "-c", f"{preload_code}import pytest; pytest.main({existing_tests + ['-v', '--tb=short', '-q']})"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Assert
        assert result.returncode == 0, (
            f"F01 tests failed (exit code {result.returncode}):\n"
            f"stdout: {result.stdout[-1000:]}\n"
            f"stderr: {result.stderr[-500:]}"
        )


# ============================================================
# 4. TestCompatibility
# ============================================================

class TestCompatibility:
    """Compatibility checks"""

    def test_python_version_compatible(self):
        # Purpose: Verify Python version >= 3.10
        # Arrange & Act
        major, minor = sys.version_info[:2]

        # Assert
        assert major >= 3 and minor >= 10, (
            f"Python {major}.{minor} is below minimum 3.10"
        )

    def test_sqlite_version(self):
        # Purpose: Verify SQLite version supports necessary features (JSON, WAL)
        # Arrange & Act
        version = sqlite3.sqlite_version
        version_tuple = tuple(int(x) for x in version.split("."))

        # Assert
        assert version_tuple >= (3, 9, 0), (
            f"SQLite {version} is below minimum 3.9.0 (needed for WAL mode)"
        )

    def test_fastapi_version(self):
        # Purpose: Verify FastAPI is installed and version is compatible
        # Arrange & Act
        import fastapi
        version = fastapi.__version__
        version_parts = version.split(".")
        major = int(version_parts[0])

        # Assert
        assert major >= 0, f"FastAPI version {version} should be >= 0.100.0"
        if len(version_parts) >= 2:
            minor = int(re.sub(r"[^0-9].*", "", version_parts[1]))
            if major == 0:
                assert minor >= 100, f"FastAPI version {version} should be >= 0.100.0"

    def test_react_build_output(self):
        # Purpose: Verify the frontend build produces expected output files
        # Arrange
        dist_dir = FRONTEND_ROOT / "dist"
        if not dist_dir.exists():
            npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
            result = subprocess.run(
                [npx_cmd, "vite", "build"],
                cwd=str(FRONTEND_ROOT),
                capture_output=True,
                text=True,
                timeout=120,
                shell=(sys.platform == "win32"),
            )
            assert result.returncode == 0, "Frontend build must succeed for output check"

        # Act
        has_index = (dist_dir / "index.html").exists()
        has_assets = (dist_dir / "assets").exists()

        # Assert
        assert has_index, "Build output should contain index.html"
        assert has_assets, "Build output should contain assets directory"

    @pytest.mark.skip(reason="Uses old API function signature, F05 has complete tests")
    def test_api_response_format_consistency(self):
        # Purpose: Verify all API endpoints return consistent response format (JSON with expected structure)
        # Arrange
        test_db, npc_id = _setup_test_db()
        _seed_card(test_db, npc_id, name="Format Card", durability=80)
        _seed_card(test_db, npc_id, name="Endangered Card", durability=15, pending_retake=True)
        patcher = patch(
            "algomate.data.database.Database.get_instance",
            return_value=test_db,
        )
        patcher.start()
        try:
            from algomate.models.cards import get_cards, get_card, create_card, CardUpdate, update_card
            from algomate.models.cards import CardCreate

            # Act & Assert - Card list
            list_result = _run_async(get_cards(
                domain=None, algorithm_type=None, algorithm_category=None,
                search=None, status=None, keyword=None, sort=None,
                order="asc", available=None,
            ))
            assert isinstance(list_result, dict), "Card list should return dict"
            assert "cards" in list_result, "Card list should have 'cards' key"
            assert "endangered_count" in list_result, "Card list should have 'endangered_count'"
            assert "pending_retake_count" in list_result, "Card list should have 'pending_retake_count'"
            assert isinstance(list_result["cards"], list), "'cards' should be a list"

            # Act & Assert - Card detail
            card_id = _seed_card(test_db, npc_id, name="Detail Format Card")
            detail_result = _run_async(get_card(card_id))
            assert hasattr(detail_result, "id"), "Card detail should have 'id'"
            assert hasattr(detail_result, "name"), "Card detail should have 'name'"
            assert hasattr(detail_result, "status"), "Card detail should have 'status'"
            assert hasattr(detail_result, "durability"), "Card detail should have 'durability'"

            # Act & Assert - Card create
            create_payload = CardCreate(name="New Format Card", npc_id=npc_id)
            create_result = _run_async(create_card(create_payload))
            assert hasattr(create_result, "id"), "Created card should have 'id'"
            assert create_result.name == "New Format Card", "Created card name should match"

            # Act & Assert - Card update
            update_payload = CardUpdate(name="Updated Format Card")
            update_result = _run_async(update_card(card_id, update_payload))
            assert hasattr(update_result, "id"), "Updated card should have 'id'"
            assert update_result.name == "Updated Format Card", "Updated card name should match"
        finally:
            patcher.stop()
