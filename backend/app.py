import hashlib
import hmac
import json
import os
import re
import sqlite3
import uuid
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Literal
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

DATA_DIR = Path(os.environ.get("TEST_RESULTS_DATA_DIR", "./data"))
ARTIFACT_DIR = Path(os.environ.get("TEST_RESULTS_ARTIFACT_DIR", "./artifacts"))
MAX_UPLOAD = 32 * 1024 * 1024
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def identifier(value: str) -> str:
    if not ID_RE.fullmatch(value):
        raise ValueError("invalid identifier")
    return value


class Project(StrictModel):
    id: str
    title: str
    description: str

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str: return identifier(value)


class CaseStep(StrictModel):
    action: str = Field(min_length=1)
    expected: str = Field(min_length=1)

    @field_validator("action", "expected")
    @classmethod
    def nonblank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class Case(StrictModel):
    id: str
    project_id: str
    title: str = Field(min_length=1)
    path: list[str] = Field(min_length=1)
    requirement: str
    preconditions: list[str]
    steps: list[CaseStep] = Field(min_length=1)
    priority: Literal["P0", "P1", "P2"]
    tags: list[str]
    source: str

    @field_validator("id", "project_id")
    @classmethod
    def valid_ids(cls, value: str) -> str: return identifier(value)

    @field_validator("title")
    @classmethod
    def nonblank_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class Catalog(StrictModel):
    project: Project
    cases: list[Case]


class Run(StrictModel):
    id: str
    project_id: str
    title: str
    environment: str
    kind: Literal["browser", "blackbox", "whitebox", "import"]
    started_at: str
    versions: dict[str, str]
    scope_case_ids: list[str] = Field(min_length=1)
    summary: str
    source: str

    @field_validator("id", "project_id")
    @classmethod
    def valid_ids(cls, value: str) -> str: return identifier(value)

    @field_validator("started_at")
    @classmethod
    def valid_time(cls, value: str) -> str:
        parse_time(value); return value


class Mark(StrictModel):
    x: int = Field(ge=0); y: int = Field(ge=0); w: int = Field(gt=0); h: int = Field(gt=0); label: str | int

    @field_validator("label")
    @classmethod
    def valid_label(cls, value: str | int) -> str | int:
        if isinstance(value, str) and (not value.strip() or len(value) > 160):
            raise ValueError("label must contain 1 to 160 readable characters")
        if isinstance(value, int) and not isinstance(value, bool) and not 0 <= value <= 999999:
            raise ValueError("numeric label is out of range")
        return value


class Crop(StrictModel):
    x: int = Field(ge=0); y: int = Field(ge=0); w: int = Field(gt=0); h: int = Field(gt=0)


class Evidence(StrictModel):
    artifact_id: str
    caption: str
    media_type: str = "image/png"
    marks: list[Mark] | None = None
    crop: Crop | None = None


class ResultStep(StrictModel):
    action: str
    expected: str
    actual: str
    status: Literal["passed", "failed", "blocked", "not_run", "skipped"]
    evidence: list[Evidence]


class Issue(StrictModel):
    title: str
    url: str


class Result(StrictModel):
    case_id: str
    status: Literal["passed", "failed", "blocked", "not_run", "skipped"]
    actual: str
    steps: list[ResultStep]
    evidence: list[Evidence]
    issues: list[Issue]
    recorded_at: str
    notes: str

    @field_validator("case_id")
    @classmethod
    def valid_case_id(cls, value: str) -> str: return identifier(value)

    @field_validator("recorded_at")
    @classmethod
    def valid_time(cls, value: str) -> str:
        parse_time(value); return value


class Finish(StrictModel):
    state: Literal["completed", "interrupted"]
    summary: str


def parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("must be ISO8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("must include timezone")
    return parsed


def validate_artifact(data: bytes, media_type: str) -> None:
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "file exceeds 32 MiB limit")
    signatures = {
        "image/png": False,
        "image/jpeg": False,
        "image/webp": False,
        "application/pdf": data.startswith(b"%PDF-"),
        "text/plain": False,
        "text/markdown": False,
        "application/json": False,
    }
    if media_type in ("image/png", "image/jpeg", "image/webp"):
        try:
            with Image.open(BytesIO(data)) as image:
                expected_format = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}[media_type]
                if image.format == expected_format and image.width > 0 and image.height > 0:
                    image.verify()
                    signatures[media_type] = True
        except (UnidentifiedImageError, OSError, ValueError):
            pass
    if media_type in ("text/plain", "text/markdown"):
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            pass
        else:
            signatures[media_type] = True
    if media_type == "application/json":
        try:
            json.loads(data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
        else:
            signatures[media_type] = True
    if media_type not in signatures or not signatures[media_type] or not data:
        raise HTTPException(415, "unsupported or invalid file format")


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    class RequestConnection(sqlite3.Connection):
        def __exit__(self, exc_type, exc, tb):
            try:
                return super().__exit__(exc_type, exc, tb)
            finally:
                self.close()

    conn = sqlite3.connect(DATA_DIR / "test-results.sqlite3", timeout=10, factory=RequestConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,title TEXT NOT NULL,description TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS cases(id TEXT NOT NULL,project_id TEXT NOT NULL REFERENCES projects(id),body TEXT NOT NULL,PRIMARY KEY(project_id,id));
    CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id),body TEXT NOT NULL,state TEXT NOT NULL,finished_at TEXT);
    CREATE TABLE IF NOT EXISTS snapshots(run_id TEXT NOT NULL REFERENCES runs(id),case_id TEXT NOT NULL,body TEXT NOT NULL,PRIMARY KEY(run_id,case_id));
    CREATE TABLE IF NOT EXISTS results(run_id TEXT NOT NULL REFERENCES runs(id),case_id TEXT NOT NULL,body TEXT NOT NULL,digest TEXT NOT NULL,PRIMARY KEY(run_id,case_id));
    CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY,filename TEXT NOT NULL,media_type TEXT NOT NULL,path TEXT NOT NULL);
    """)
    return conn


def decode(row: sqlite3.Row | None, key: str = "body"):
    return json.loads(row[key]) if row else None


def counts(rows: list[sqlite3.Row], total: int) -> dict:
    result = {k: 0 for k in ("passed", "failed", "blocked", "not_run", "skipped")}
    for row in rows:
        result[json.loads(row["body"])["status"]] += 1
    result["not_run"] += total - len(rows)
    result["total"] = total
    return result


def read_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health(): return {"status": "ok"}

    @app.get("/api/projects")
    def projects():
        with connect() as db:
            rows = db.execute("SELECT p.*,count(c.id) n FROM projects p LEFT JOIN cases c ON c.project_id=p.id GROUP BY p.id ORDER BY p.id").fetchall()
            return [{"id": r["id"], "title": r["title"], "description": r["description"], "case_count": r["n"]} for r in rows]

    @app.get("/api/projects/{project_id}/cases")
    def project_cases(project_id: str):
        with connect() as db:
            return [decode(r) for r in db.execute("SELECT body FROM cases WHERE project_id=? ORDER BY id", (project_id,))]

    @app.get("/api/projects/{project_id}/runs")
    def project_runs(project_id: str):
        with connect() as db:
            runs = db.execute("SELECT * FROM runs WHERE project_id=? ORDER BY julianday(json_extract(body,'$.started_at')) DESC,rowid DESC", (project_id,)).fetchall()
            output = []
            for run in runs:
                total = db.execute("SELECT count(*) FROM snapshots WHERE run_id=?", (run["id"],)).fetchone()[0]
                res = db.execute("SELECT body FROM results WHERE run_id=?", (run["id"],)).fetchall()
                output.append({**decode(run), "state": run["state"], "finished_at": run["finished_at"], "counts": counts(res, total)})
            return output

    @app.get("/api/runs/{run_id}")
    def run_detail(run_id: str):
        with connect() as db:
            run = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if not run: raise HTTPException(404, "run not found")
            snaps = db.execute("SELECT s.case_id,s.body snapshot,r.body result FROM snapshots s LEFT JOIN results r ON r.run_id=s.run_id AND r.case_id=s.case_id WHERE s.run_id=? ORDER BY s.case_id", (run_id,)).fetchall()
            result_rows = db.execute("SELECT body FROM results WHERE run_id=?", (run_id,)).fetchall()
            run_obj = {**decode(run), "state": run["state"], "finished_at": run["finished_at"]}
            return {"run": run_obj, "cases": [{"case": json.loads(s["snapshot"]), "result": json.loads(s["result"]) if s["result"] else None} for s in snaps], "counts": counts(result_rows, len(snaps))}

    @app.get("/api/projects/{project_id}/cases/{case_id}")
    def case_history(project_id: str, case_id: str):
        with connect() as db:
            current = db.execute("SELECT body FROM cases WHERE project_id=? AND id=?", (project_id, case_id)).fetchone()
            if not current: raise HTTPException(404, "case not found")
            rows = db.execute("SELECT r.*,s.body snapshot,v.body result FROM snapshots s JOIN runs r ON r.id=s.run_id LEFT JOIN results v ON v.run_id=s.run_id AND v.case_id=s.case_id WHERE r.project_id=? AND s.case_id=? ORDER BY julianday(json_extract(r.body,'$.started_at')) DESC,r.rowid DESC", (project_id,case_id)).fetchall()
            return {"case": decode(current), "history": [{"run": {**decode(r), "state": r["state"], "finished_at": r["finished_at"]}, "result": json.loads(r["result"]) if r["result"] else None} for r in rows]}

    @app.get("/artifacts/{artifact_id}")
    def artifact(artifact_id: str):
        with connect() as db: row = db.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
        if not row: raise HTTPException(404, "artifact not found")
        return FileResponse(row["path"], media_type=row["media_type"], filename=row["filename"])

    static_dir = Path("static")
    if static_dir.is_dir():
        index_file = static_dir / "index.html"

        @app.get("/", include_in_schema=False)
        @app.get("/projects", include_in_schema=False)
        @app.get("/projects/{project_id}", include_in_schema=False)
        @app.get("/projects/{project_id}/runs/{run_id}", include_in_schema=False)
        @app.get("/projects/{project_id}/runs/{run_id}/cases/{case_id}", include_in_schema=False)
        def page_entry():
            return FileResponse(index_file, media_type="text/html")

        assets_dir = static_dir / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    return app


def write_app() -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def authorize(request, call_next):
        if request.url.path.startswith("/write/"):
            expected = os.environ.get("TEST_RESULTS_WRITE_TOKEN", "").encode()
            supplied = request.headers.get("Authorization", "")
            token = supplied[7:].encode() if supplied.startswith("Bearer ") else b""
            if not expected or not hmac.compare_digest(token, expected):
                return await _unauthorized()
        return await call_next(request)

    @app.get("/health")
    def health(): return {"status": "ok"}

    @app.put("/write/catalog")
    def catalog(payload: Catalog):
        if any(c.project_id != payload.project.id for c in payload.cases): raise HTTPException(422, "case project_id mismatch")
        with connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                db.execute("INSERT INTO projects VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,description=excluded.description", (payload.project.id,payload.project.title,payload.project.description))
                for case in payload.cases:
                    db.execute("INSERT INTO cases VALUES(?,?,?) ON CONFLICT(project_id,id) DO UPDATE SET body=excluded.body", (case.id,case.project_id,case.model_dump_json()))
                db.commit()
            except sqlite3.IntegrityError as exc:
                db.rollback(); raise HTTPException(409, "catalog update conflicts with existing data") from exc
            n = db.execute("SELECT count(*) FROM cases WHERE project_id=?", (payload.project.id,)).fetchone()[0]
        return {"project_id": payload.project.id, "case_count": n}

    @app.post("/write/runs")
    def create_run(payload: Run):
        with connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                cases = db.execute("SELECT id,body FROM cases WHERE project_id=?", (payload.project_id,)).fetchall()
                mapping = {r["id"]: r["body"] for r in cases}
                if len(set(payload.scope_case_ids)) != len(payload.scope_case_ids) or any(i not in mapping for i in payload.scope_case_ids):
                    raise HTTPException(422, "scope contains unknown or duplicate case")
                db.execute("INSERT INTO runs VALUES(?,?,?,'running',NULL)", (payload.id,payload.project_id,payload.model_dump_json()))
                for case_id in payload.scope_case_ids:
                    db.execute("INSERT INTO snapshots VALUES(?,?,?)", (payload.id,case_id,mapping[case_id]))
                db.commit()
            except sqlite3.IntegrityError as exc:
                db.rollback(); raise HTTPException(409, "run id already exists") from exc
            except Exception:
                db.rollback(); raise
        return {**payload.model_dump(), "state": "running", "finished_at": None}

    @app.post("/write/runs/{run_id}/results")
    def add_result(run_id: str, payload: Result):
        if payload.status in ("passed", "failed") and not payload.actual.strip(): raise HTTPException(422, "passed and failed results require actual observations")
        content = payload.model_dump_json()
        canonical = json.dumps(payload.model_dump(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        with connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                run = db.execute("SELECT state FROM runs WHERE id=?", (run_id,)).fetchone()
                if not run: raise HTTPException(404, "run not found")
                if run["state"] != "running": raise HTTPException(409, "run is frozen")
                scope = db.execute("SELECT 1 FROM snapshots WHERE run_id=? AND case_id=?", (run_id,payload.case_id)).fetchone()
                if not scope: raise HTTPException(422, "case is outside run scope")
                for item in [*payload.evidence, *(e for step in payload.steps for e in step.evidence)]:
                    if not db.execute("SELECT 1 FROM artifacts WHERE id=?", (item.artifact_id,)).fetchone(): raise HTTPException(422, "unknown artifact")
                old = db.execute("SELECT body,digest FROM results WHERE run_id=? AND case_id=?", (run_id,payload.case_id)).fetchone()
                if old:
                    if old["digest"] == digest: db.commit(); return json.loads(old["body"])
                    raise HTTPException(409, "result already recorded with different content")
                db.execute("INSERT INTO results VALUES(?,?,?,?)", (run_id,payload.case_id,content,digest))
                db.commit()
            except Exception:
                db.rollback(); raise
        return payload.model_dump()

    @app.post("/write/runs/{run_id}/finish")
    def finish(run_id: str, payload: Finish):
        finished = datetime.now().astimezone().isoformat()
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT body FROM runs WHERE id=? AND state='running'", (run_id,)).fetchone()
            if not row:
                exists = db.execute("SELECT 1 FROM runs WHERE id=?", (run_id,)).fetchone()
                if not exists: raise HTTPException(404, "run not found")
                raise HTTPException(409, "run already finished")
            body = json.loads(row["body"])
            body["summary"] = payload.summary
            updated = db.execute("UPDATE runs SET body=?,state=?,finished_at=? WHERE id=? AND state='running'", (json.dumps(body, ensure_ascii=False),payload.state,finished,run_id))
            if updated.rowcount != 1: raise HTTPException(409, "run already finished")
            row = db.execute("SELECT body FROM runs WHERE id=?", (run_id,)).fetchone()
        return {**decode(row), "summary": payload.summary, "state": payload.state, "finished_at": finished}

    @app.post("/write/artifacts")
    async def upload(file: UploadFile = File(...)):
        data = await file.read(MAX_UPLOAD + 1)
        name = Path(file.filename or "upload").name
        typ = file.content_type or "application/octet-stream"
        validate_artifact(data, typ)
        artifact_id = str(uuid.uuid4())
        suffix = Path(name).suffix[:16]
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        path = ARTIFACT_DIR / f"{artifact_id}{suffix}"
        path.write_bytes(data)
        with connect() as db:
            db.execute("INSERT INTO artifacts VALUES(?,?,?,?)", (artifact_id,name,typ,str(path)))
        return {"artifact_id": artifact_id, "filename": name, "media_type": typ, "url": f"/artifacts/{artifact_id}"}

    return app


async def _unauthorized():
    from fastapi.responses import JSONResponse
    return JSONResponse({"detail": "invalid bearer token"}, status_code=401)


def create_read_app() -> FastAPI: return read_app()
def create_write_app() -> FastAPI: return write_app()
