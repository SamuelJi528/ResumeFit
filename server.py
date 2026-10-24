import hmac
import os
import time
from collections import OrderedDict, deque
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import BoundedSemaphore, Lock

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from file_utils import MAX_FILE_BYTES, extract_text
from models import MAX_JOB, MAX_RESUME, Refinement, Review, evidence_coverage
from providers import AIConfig, AIError
from reports import report_text
from reviewer import refine_bullet, review_resume


ROOT = Path(__file__).resolve().parent


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resume: str = Field(min_length=100, max_length=MAX_RESUME)
    job: str = Field(min_length=100, max_length=MAX_JOB)
    use_examples: bool = True


class RefineInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    original: str = Field(min_length=1, max_length=1000)
    current: str = Field(min_length=1, max_length=1200)
    feedback: str = Field(min_length=1, max_length=600)


class ReportMetadata(BaseModel):
    provider: str = Field(max_length=30)
    model: str = Field(max_length=100)
    generated_at: str = Field(max_length=60)
    use_examples: bool


class Revision(Refinement):
    feedback: str = Field(max_length=600)
    provider: str = Field(max_length=30)
    model: str = Field(max_length=100)


class ExportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    review: Review
    metadata: ReportMetadata
    refinements: dict[int, list[Revision]] = Field(default_factory=dict)


class RequestError(Exception):
    def __init__(self, message, status=400):
        self.message = message
        self.status = status


class GenerationLimits:
    def __init__(self, per_minute, daily_limit):
        self.per_minute = per_minute
        self.daily_limit = daily_limit
        self.clients = OrderedDict()
        self.lock = Lock()
        self.slots = BoundedSemaphore(2)
        self.day = None
        self.count = 0

    @contextmanager
    def reserve(self, address):
        if not self.slots.acquire(blocking=False):
            raise RequestError("The review service is busy. Please try again shortly.", 503)
        try:
            with self.lock:
                now = time.monotonic()
                today = datetime.now(timezone.utc).date()
                if today != self.day:
                    self.day, self.count = today, 0
                if self.count >= self.daily_limit:
                    raise RequestError("This demo has reached its daily review limit. Please try again later.", 429)
                recent = self.clients.setdefault(address, deque())
                self.clients.move_to_end(address)
                while recent and now - recent[0] >= 60:
                    recent.popleft()
                if len(recent) >= self.per_minute:
                    raise RequestError("Too many requests. Wait a minute and try again.", 429)
                recent.append(now)
                self.count += 1
                while len(self.clients) > 1024:
                    self.clients.popitem(last=False)
            yield
        finally:
            self.slots.release()


def create_app(test_config=None):
    if test_config is None:
        load_dotenv(ROOT / ".env")
    # Vercel serves public/ from its CDN; Flask serves the same URLs locally.
    app = Flask(__name__, static_folder="public/static", static_url_path="/static")
    app.config.update(
        MAX_CONTENT_LENGTH=MAX_FILE_BYTES + 65536,
        GEMINI_API_KEY=os.getenv("GEMINI_API_KEY", ""),
        GEMINI_MODEL=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        SITE_ACCESS_CODE=os.getenv("SITE_ACCESS_CODE", ""),
        REQUESTS_PER_MINUTE=int(os.getenv("REQUESTS_PER_MINUTE", "5")),
        DAILY_GENERATION_LIMIT=int(os.getenv("DAILY_GENERATION_LIMIT", "100")),
    )
    if test_config:
        app.config.update(test_config)
    if os.getenv("TRUST_PROXY", "0") == "1":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    limits = GenerationLimits(app.config["REQUESTS_PER_MINUTE"], app.config["DAILY_GENERATION_LIMIT"])
    app.extensions["generation_limits"] = limits

    @app.before_request
    def protect_api():
        if request.path.startswith("/api/") and request.method == "POST":
            origin = request.headers.get("Origin")
            if origin and origin != request.host_url.rstrip("/"):
                raise RequestError("Requests must come from this website.", 403)
            code = app.config["SITE_ACCESS_CODE"]
            if code and not hmac.compare_digest(code.encode(), request.headers.get("X-Access-Code", "").encode()):
                raise RequestError("Enter the demo access code to continue.", 401)

    @app.after_request
    def security_headers(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; base-uri 'self'; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.errorhandler(RequestError)
    def handle_request_error(error):
        response = jsonify(error=error.message)
        response.status_code = error.status
        if error.status == 429:
            response.headers["Retry-After"] = "60"
        return response

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        first = error.errors(include_input=False, include_url=False)[0]
        field = ".".join(str(part) for part in first["loc"])
        return jsonify(error=f"Check {field}: {first['msg']}"), 400

    @app.errorhandler(AIError)
    def handle_ai_error(error):
        app.logger.warning("Gemini request failed: %s", error)
        return jsonify(error="The AI service could not complete this request. Please try again or contact the site owner."), 502

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        message = "Use a file smaller than 3 MB." if error.code == 413 else error.description
        if request.path.startswith("/api/"):
            return jsonify(error=message), error.code
        return error

    def parse_input(model):
        if not request.is_json:
            raise RequestError("Send this request as JSON.", 415)
        data = request.get_json()
        return model.model_validate(data)

    def ai_config():
        key = app.config["GEMINI_API_KEY"]
        if not key.strip():
            raise RequestError("The review service is not configured yet. Please contact the site owner.", 503)
        return AIConfig(model=app.config["GEMINI_MODEL"], api_key=key)

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", ready=bool(app.config["GEMINI_API_KEY"].strip()))

    @app.get("/api/config")
    def config():
        return jsonify(
            ready=bool(app.config["GEMINI_API_KEY"].strip()),
            requires_access_code=bool(app.config["SITE_ACCESS_CODE"]),
            limits={"resume": MAX_RESUME, "job": MAX_JOB, "file_bytes": MAX_FILE_BYTES},
        )

    @app.get("/api/sample")
    def sample():
        return jsonify(resume=(ROOT / "samples/resume.txt").read_text(encoding="utf-8"),
                       job=(ROOT / "samples/job_description.txt").read_text(encoding="utf-8"))

    @app.post("/api/extract")
    def extract():
        upload = request.files.get("file")
        if not upload or not upload.filename:
            raise RequestError("Choose a PDF, DOCX, or TXT file.")
        try:
            text = extract_text(upload.filename, upload.read(MAX_FILE_BYTES + 1))
        except ValueError as error:
            raise RequestError(str(error)) from None
        if len(text) > MAX_RESUME:
            raise RequestError(f"This document is too long. Paste a version under {MAX_RESUME:,} characters.")
        return jsonify(text=text)

    @app.post("/api/review")
    def review():
        data = parse_input(ReviewInput)
        config = ai_config()
        try:
            with limits.reserve(request.remote_addr or "unknown"):
                result = review_resume(config, data.resume, data.job, data.use_examples)
        except ValueError as error:
            raise RequestError(str(error)) from None
        return jsonify(
            review=result.model_dump(),
            metrics={"coverage": evidence_coverage(result),
                     "supported": sum(item.status == "Supported" for item in result.requirements),
                     "gaps": sum(item.status != "Supported" for item in result.requirements)},
            metadata={"provider": "Gemini", "model": config.model, "use_examples": data.use_examples,
                      "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        )

    @app.post("/api/refine")
    def refine():
        data = parse_input(RefineInput)
        config = ai_config()
        try:
            with limits.reserve(request.remote_addr or "unknown"):
                result = refine_bullet(config, data.original, data.current, data.feedback)
        except ValueError as error:
            raise RequestError(str(error)) from None
        return jsonify(**result.model_dump(), provider="Gemini", model=config.model)

    @app.post("/api/export")
    def export():
        data = parse_input(ExportInput)
        if sum(len(items) for items in data.refinements.values()) > 50:
            raise RequestError("Export up to 50 revisions at a time.")
        histories = {index: [item.model_dump() for item in items] for index, items in data.refinements.items()}
        text = report_text(data.review, data.metadata.model_dump(), histories)
        return Response(text, mimetype="text/plain", headers={
            "Content-Disposition": 'attachment; filename="resume_review.txt"'
        })

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "8000")), debug=False)
