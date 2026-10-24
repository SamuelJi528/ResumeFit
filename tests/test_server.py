import io
import json
from pathlib import Path

import pytest

import reviewer
import server
from providers import AIError


@pytest.fixture
def app(monkeypatch, review_data):
    monkeypatch.delenv("TRUST_PROXY", raising=False)
    def generate(config, messages, schema):
        if schema.get("title") == "Refinement":
            return json.dumps({"improved": "Built a React menu and cart interface.", "explanation": "Shorter wording."})
        return json.dumps(review_data)
    monkeypatch.setattr(reviewer, "generate", generate)
    return server.create_app({"TESTING": True, "GEMINI_API_KEY": "private-test-key",
                              "SITE_ACCESS_CODE": "", "REQUESTS_PER_MINUTE": 100,
                              "DAILY_GENERATION_LIMIT": 100})


@pytest.fixture
def client(app):
    return app.test_client()


def test_home_and_assets_do_not_expose_key(client):
    for path in ["/", "/static/app.js", "/static/styles.css", "/api/config", "/api/health"]:
        response = client.get(path)
        assert response.status_code == 200
        assert b"private-test-key" not in response.data
        assert "'self'" in response.headers["Content-Security-Policy"]
    assert client.get("/.env").status_code == 404
    assert client.get("/providers.py").status_code == 404


def test_home_assets_match_vercel_public_files(client):
    root = Path(__file__).resolve().parents[1]
    home = client.get("/").get_data(as_text=True)
    for filename in ("app.js", "styles.css", "favicon.svg"):
        url = f"/static/{filename}"
        asset = root / "public" / "static" / filename
        assert asset.is_file(), f"Vercel must serve {url} from public/"
        assert url in home
        assert client.get(url).data == asset.read_bytes()


def test_complete_review_refinement_and_export(client, resume, job):
    response = client.post("/api/review", json={"resume": resume, "job": job, "use_examples": True})
    assert response.status_code == 200
    result = response.json
    assert result["metrics"] == {"coverage": 60, "supported": 1, "gaps": 2}
    bullet = result["review"]["bullet_rewrites"][0]
    revised = client.post("/api/refine", json={"original": bullet["original"],
                         "current": bullet["improved"], "feedback": "Make it shorter"})
    assert revised.status_code == 200
    assert revised.json["improved"] == "Built a React menu and cart interface."
    revision = {**revised.json, "feedback": "Make it shorter"}
    report = client.post("/api/export", json={"review": result["review"], "metadata": result["metadata"],
                         "refinements": {"0": [revision]}})
    assert report.status_code == 200
    assert "attachment" in report.headers["Content-Disposition"]
    assert b"Revision 1" in report.data and b"60%" in report.data
    assert b"private-test-key" not in report.data


@pytest.mark.parametrize("body", [{}, {"resume": "short", "job": "short"},
                                  {"resume": "x" * 12001, "job": "y" * 100}])
def test_bad_review_input_rejected(client, body):
    assert client.post("/api/review", json=body).status_code == 400


def test_bad_refinement_input_rejected(client):
    assert client.post("/api/refine", json={"original": "x", "current": "y", "feedback": ""}).status_code == 400


def test_json_content_type_required(client):
    assert client.post("/api/review", data={"resume": "x" * 100, "job": "y" * 100}).status_code == 415


def test_cross_origin_post_rejected(client, resume, job):
    response = client.post("/api/review", json={"resume": resume, "job": job}, headers={"Origin": "https://other.example"})
    assert response.status_code == 403


def test_same_origin_allowed(client, resume, job):
    assert client.post("/api/review", json={"resume": resume, "job": job}, headers={"Origin": "http://localhost"}).status_code == 200


def test_https_origin_and_client_ip_behind_vercel_proxy(app, monkeypatch, resume, job):
    monkeypatch.setenv("TRUST_PROXY", "1")
    proxy_app = server.create_app(dict(app.config))
    client = proxy_app.test_client()
    headers = {"Origin": "https://resumefit.vercel.app",
               "X-Forwarded-Proto": "https", "X-Forwarded-For": "203.0.113.7"}
    response = client.post("/api/review", base_url="http://resumefit.vercel.app",
                           json={"resume": resume, "job": job}, headers=headers)
    assert response.status_code == 200
    assert "203.0.113.7" in proxy_app.extensions["generation_limits"].clients
    headers["Origin"] = "https://other.example"
    assert client.post("/api/review", base_url="http://resumefit.vercel.app",
                       json={"resume": resume, "job": job}, headers=headers).status_code == 403


def test_optional_access_code(app, resume, job):
    app.config["SITE_ACCESS_CODE"] = "class-code"
    client = app.test_client()
    assert client.get("/api/config").json["requires_access_code"] is True
    assert client.post("/api/review", json={"resume": resume, "job": job}).status_code == 401
    assert client.post("/api/review", json={"resume": resume, "job": job},
                       headers={"X-Access-Code": "class-code"}).status_code == 200


def test_missing_server_key_is_clear_and_private(app, resume, job):
    app.config["GEMINI_API_KEY"] = ""
    client = app.test_client()
    assert client.get("/api/health").json["ready"] is False
    response = client.post("/api/review", json={"resume": resume, "job": job})
    assert response.status_code == 503
    assert "site owner" in response.json["error"]


def test_per_minute_limit(app, resume, job):
    app.extensions["generation_limits"].per_minute = 1
    client = app.test_client()
    body = {"resume": resume, "job": job}
    assert client.post("/api/review", json=body).status_code == 200
    response = client.post("/api/review", json=body)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


def test_global_daily_limit(app, resume, job):
    app.extensions["generation_limits"].daily_limit = 1
    client = app.test_client()
    body = {"resume": resume, "job": job}
    assert client.post("/api/review", json=body, environ_base={"REMOTE_ADDR": "127.0.0.2"}).status_code == 200
    response = client.post("/api/review", json=body, environ_base={"REMOTE_ADDR": "127.0.0.3"})
    assert response.status_code == 429


def test_busy_service_does_not_queue_unlimited_requests(app, resume, job):
    slots = app.extensions["generation_limits"].slots
    slots.acquire()
    slots.acquire()
    try:
        response = app.test_client().post("/api/review", json={"resume": resume, "job": job})
        assert response.status_code == 503
    finally:
        slots.release()
        slots.release()


def test_ai_error_does_not_expose_details(client, monkeypatch, resume, job):
    def fail(*args):
        raise AIError("Gemini denied access")
    monkeypatch.setattr(server, "review_resume", fail)
    response = client.post("/api/review", json={"resume": resume, "job": job})
    assert response.status_code == 502
    assert "Gemini denied" not in response.json["error"]


def test_upload_and_sample(client, resume):
    response = client.post("/api/extract", data={"file": (io.BytesIO(resume.encode()), "resume.txt")})
    assert response.status_code == 200 and response.json["text"] == resume.strip()
    assert client.get("/api/sample").json["resume"].startswith("ALEX MORGAN")


def test_unsupported_and_missing_uploads(client):
    assert client.post("/api/extract").status_code == 400
    assert client.post("/api/extract", data={"file": (io.BytesIO(b"not executable"), "resume.exe")}).status_code == 400


def test_oversized_request_returns_json(client):
    response = client.post("/api/extract", data=b"x" * (3 * 1024 * 1024 + 65537), content_type="application/octet-stream")
    assert response.status_code == 413 and response.is_json


def test_api_replies_are_not_cached(client):
    assert client.get("/api/config").headers["Cache-Control"] == "no-store"
