import threading

import pytest
from werkzeug.serving import make_server

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test.sqlite"),
            "SECRET_KEY": "test-key",
            "WTF_CSRF_ENABLED": False,
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def live_url(tmp_path):
    # Системные тесты используют настоящую CSRF-защиту и отдельную базу.
    application = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "system.sqlite"),
            "SECRET_KEY": "system-test-key",
        }
    )
    server = make_server("127.0.0.1", 0, application)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
