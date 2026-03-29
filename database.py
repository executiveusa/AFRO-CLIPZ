"""
AfroMations - Database Layer
SQLite (default, zero config) with Supabase upgrade path.
"""
import os
import json
import uuid
import aiosqlite
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

DB_PATH = os.environ.get("DB_PATH", str(Path(__file__).parent / "afromations.db"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    avatar_url TEXT,
    google_id TEXT,
    plan TEXT DEFAULT 'free',
    invite_code TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invite_requests (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    name TEXT,
    company TEXT,
    use_case TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT,
    status TEXT DEFAULT 'queued',
    job_type TEXT DEFAULT 'clip',
    query TEXT,
    input_path TEXT,
    output_path TEXT,
    progress INTEGER DEFAULT 0,
    message TEXT,
    error TEXT,
    result_data TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    lemon_squeezy_id TEXT,
    lemon_squeezy_customer_id TEXT,
    current_period_end TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS clips (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    project_id TEXT,
    title TEXT,
    file_path TEXT,
    duration REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
"""


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()
    print(f"✅ Database initialized: {DB_PATH}")


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


# ─── Users ────────────────────────────────────────────────────────────────────

async def create_user(email: str, name: str, google_id: str = None,
                      avatar_url: str = None) -> Dict[str, Any]:
    user = {
        "id": new_id(),
        "email": email,
        "name": name,
        "google_id": google_id,
        "avatar_url": avatar_url,
        "plan": "free",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (id, email, name, google_id, avatar_url, plan, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user["id"], user["email"], user["name"], user["google_id"],
             user["avatar_url"], user["plan"], user["created_at"], user["updated_at"])
        )
        await db.commit()
    return user


async def get_user_by_email(email: str) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE email = ?", (email,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_user_by_id(user_id: str) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def upsert_google_user(google_id: str, email: str, name: str,
                              avatar_url: str) -> Dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE google_id = ? OR email = ?",
                               (google_id, email)) as cur:
            row = await cur.fetchone()
        if row:
            user = dict(row)
            await db.execute(
                "UPDATE users SET google_id=?, name=?, avatar_url=?, updated_at=? WHERE id=?",
                (google_id, name, avatar_url, now_iso(), user["id"])
            )
            await db.commit()
            user.update({"google_id": google_id, "name": name, "avatar_url": avatar_url})
            return user
        return await create_user(email, name, google_id, avatar_url)


# ─── Invite Requests ──────────────────────────────────────────────────────────

async def create_invite_request(email: str, name: str, company: str = None,
                                 use_case: str = None) -> Dict:
    record = {
        "id": new_id(),
        "email": email,
        "name": name,
        "company": company,
        "use_case": use_case,
        "status": "pending",
        "created_at": now_iso(),
    }
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO invite_requests (id, email, name, company, use_case, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (record["id"], record["email"], record["name"], record["company"],
             record["use_case"], record["status"], record["created_at"])
        )
        await db.commit()
    return record


# ─── Jobs ─────────────────────────────────────────────────────────────────────

async def create_job(user_id: str, query: str, input_path: str = None,
                     project_id: str = None, job_type: str = "clip") -> Dict:
    job = {
        "id": new_id(),
        "user_id": user_id,
        "project_id": project_id,
        "status": "queued",
        "job_type": job_type,
        "query": query,
        "input_path": input_path,
        "output_path": None,
        "progress": 0,
        "message": "Job queued",
        "error": None,
        "result_data": None,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO jobs (id, user_id, project_id, status, job_type, query, "
            "input_path, output_path, progress, message, error, result_data, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job["id"], job["user_id"], job["project_id"], job["status"],
             job["job_type"], job["query"], job["input_path"], job["output_path"],
             job["progress"], job["message"], job["error"], job["result_data"],
             job["created_at"], job["updated_at"])
        )
        await db.commit()
    return job


async def update_job(job_id: str, **kwargs) -> None:
    kwargs["updated_at"] = now_iso()
    if "result_data" in kwargs and isinstance(kwargs["result_data"], dict):
        kwargs["result_data"] = json.dumps(kwargs["result_data"])
    cols = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [job_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE jobs SET {cols} WHERE id=?", vals)
        await db.commit()


async def get_job(job_id: str) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)) as cur:
            row = await cur.fetchone()
            if row:
                d = dict(row)
                if d.get("result_data"):
                    try:
                        d["result_data"] = json.loads(d["result_data"])
                    except Exception:
                        pass
                return d
            return None


async def get_user_jobs(user_id: str, limit: int = 20) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM jobs WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# ─── Projects ─────────────────────────────────────────────────────────────────

async def create_project(user_id: str, name: str, description: str = None) -> Dict:
    project = {
        "id": new_id(),
        "user_id": user_id,
        "name": name,
        "description": description,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO projects (id, user_id, name, description, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (project["id"], project["user_id"], project["name"],
             project["description"], project["created_at"], project["updated_at"])
        )
        await db.commit()
    return project


async def get_user_projects(user_id: str) -> List[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM projects WHERE user_id=? ORDER BY created_at DESC",
            (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# ─── Subscriptions ────────────────────────────────────────────────────────────

async def upsert_subscription(user_id: str, plan: str, ls_id: str = None,
                               ls_customer_id: str = None,
                               period_end: str = None,
                               status: str = "active") -> Dict:
    sub = {
        "id": new_id(),
        "user_id": user_id,
        "plan": plan,
        "status": status,
        "lemon_squeezy_id": ls_id,
        "lemon_squeezy_customer_id": ls_customer_id,
        "current_period_end": period_end,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO subscriptions "
            "(id, user_id, plan, status, lemon_squeezy_id, lemon_squeezy_customer_id, "
            "current_period_end, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (sub["id"], sub["user_id"], sub["plan"], sub["status"],
             sub["lemon_squeezy_id"], sub["lemon_squeezy_customer_id"],
             sub["current_period_end"], sub["created_at"], sub["updated_at"])
        )
        await db.commit()
    return sub


async def get_user_subscription(user_id: str) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM subscriptions WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None
