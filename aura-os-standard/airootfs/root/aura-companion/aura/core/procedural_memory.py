"""Процедурная память: "как делать X"."""
from __future__ import annotations
import hashlib, json, math, os, re, sqlite3, struct, time
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_DB = Path(os.environ.get("AURA_PROCEDURE_DB", str(Path.home() / ".cache/aura/procedures.db")))
SIM_THRESHOLD = 0.85
HOT_CACHE = 64
MAX_CANDIDATES = 512
MIN_TRUST = 0.5
MIN_FAILS_TO_DISABLE = 2

_STOP = {"и", "а", "но", "что", "чтобы", "как", "так", "это", "мне", "я", "мы", "ты", "вы", "он", "она", "пожалуйста", "давай", "хочу", "надо", "нужно", "можно", "уже", "же", "ли"}
_PUNCT = re.compile(r"[^\w\s]+", re.UNICODE)
_WS = re.compile(r"\s+")

def normalize(text: str) -> str:
    t = text.lower()
    t = _PUNCT.sub(" ", t)
    words = [w for w in _WS.split(t) if w and w not in _STOP]
    return " ".join(words)

def goal_hash(goal: str) -> str:
    return hashlib.sha256(normalize(goal).encode("utf-8")).hexdigest()

@dataclass
class Procedure:
    id: int
    goal_hash: str
    goal_text: str
    signature: str
    steps: list[dict]
    success_count: int
    fail_count: int
    last_used: float
    created_at: float
    embedding: list[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.fail_count
        return self.success_count / total if total else 0.0

    @property
    def is_trusted(self) -> bool:
        return self.success_rate >= MIN_TRUST or self.fail_count < MIN_FAILS_TO_DISABLE

class ProceduralMemory:
    def __init__(self, db_path=None, embedder=None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._embedder = embedder
        self._hot = {}
        self._init_db()


    def log_episode(self, user_input: str, tool_used: str, result: str) -> None:
        """Записать эпизод в память."""
        import time
        with sqlite3.connect(self.db_path) as c:
            c.execute(
                "INSERT INTO episodes (ts, user_input, tool_used, result) VALUES (?, ?, ?, ?)",
                (time.time(), user_input, tool_used, result[:500])
            )
            c.commit()

    def get_recent_episodes(self, limit: int = 3) -> str:
        """Получить последние N эпизодов в виде текста для контекста."""
        with sqlite3.connect(self.db_path) as c:
            c.row_factory = sqlite3.Row
            rows = c.execute(
                "SELECT user_input, tool_used, result FROM episodes ORDER BY ts DESC LIMIT ?",
                (limit,)
            ).fetchall()
        
        if not rows:
            return "Нет недавних действий."
            
        lines = []
        for r in reversed(rows):
            lines.append(f"User: {r['user_input']} -> Tool: {r['tool_used']} -> Результат: {r['result'][:100]}")
        return "\n".join(lines)

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS procedures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_hash TEXT NOT NULL UNIQUE,
                    goal_text TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    embedding BLOB,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    fail_count INTEGER NOT NULL DEFAULT 0,
                    last_used REAL NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_proc_last_used ON procedures(last_used DESC);
                
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    user_input TEXT NOT NULL,
                    tool_used TEXT,
                    result TEXT
                );
            """)
            c.commit()

    def _embed(self, text: str) -> list[float]:
        if self._embedder is None: return []
        try: return list(self._embedder.embed(text))
        except Exception: return []

    @staticmethod
    def _pack(emb: list[float]) -> bytes | None:
        return struct.pack(f"{len(emb)}f", *emb) if emb else None

    @staticmethod
    def _unpack(blob: bytes | None) -> list[float]:
        return list(struct.unpack(f"{len(blob)//4}f", blob)) if blob else []

    @staticmethod
    def _cos(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b): return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb) if na and nb else 0.0

    def recall(self, goal: str) -> Procedure | None:
        h = goal_hash(goal)
        if h in self._hot and self._hot[h].is_trusted: return self._hot[h]

        with sqlite3.connect(self.db_path) as c:
            c.row_factory = sqlite3.Row
            row = c.execute("SELECT * FROM procedures WHERE goal_hash = ?", (h,)).fetchone()
            if row:
                proc = self._row_to_proc(row)
                if proc.is_trusted:
                    self._remember_hot(proc)
                    return proc
                return None

            if self._embedder is None: return None
            qv = self._embed(normalize(goal))
            if not qv: return None

            rows = c.execute("SELECT * FROM procedures ORDER BY last_used DESC LIMIT ?", (MAX_CANDIDATES,)).fetchall()
            best, best_score = None, 0.0
            for r in rows:
                s = self._cos(qv, self._unpack(r["embedding"]))
                if s > best_score: best, best_score = r, s
            if best is None or best_score < SIM_THRESHOLD: return None
            proc = self._row_to_proc(best)
            if not proc.is_trusted: return None
            self._remember_hot(proc)
            return proc

    def _remember_hot(self, proc: Procedure) -> None:
        self._hot[proc.goal_hash] = proc
        if len(self._hot) > HOT_CACHE:
            oldest = min(self._hot.values(), key=lambda p: p.last_used)
            self._hot.pop(oldest.goal_hash, None)

    @staticmethod
    def _row_to_proc(row: sqlite3.Row) -> Procedure:
        return Procedure(
            id=row["id"], goal_hash=row["goal_hash"], goal_text=row["goal_text"],
            signature=row["signature"], steps=json.loads(row["steps_json"]),
            success_count=row["success_count"], fail_count=row["fail_count"],
            last_used=row["last_used"], created_at=row["created_at"],
            embedding=ProceduralMemory._unpack(row["embedding"])
        )

    def learn(self, goal: str, steps: list[dict], success: bool = True) -> None:
        if not steps: return
        h = goal_hash(goal)
        sig = normalize(goal)
        emb = self._pack(self._embed(sig))
        now = time.time()
        with sqlite3.connect(self.db_path) as c:
            c.row_factory = sqlite3.Row
            row = c.execute("SELECT id FROM procedures WHERE goal_hash = ?", (h,)).fetchone()
            if row:
                if success:
                    c.execute("UPDATE procedures SET success_count = success_count + 1, last_used = ?, steps_json = ?, embedding = COALESCE(?, embedding) WHERE id = ?", (now, json.dumps(steps, ensure_ascii=False), emb, row["id"]))
                else:
                    c.execute("UPDATE procedures SET fail_count = fail_count + 1, last_used = ? WHERE id = ?", (now, row["id"]))
            else:
                c.execute("INSERT INTO procedures (goal_hash, goal_text, signature, steps_json, embedding, success_count, fail_count, last_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (h, goal, sig, json.dumps(steps, ensure_ascii=False), emb, 1 if success else 0, 0 if success else 1, now, now))
            c.commit()
        self._hot.pop(h, None)

    def mark_failed(self, procedure: Procedure | int) -> None:
        pid = procedure.id if isinstance(procedure, Procedure) else procedure
        with sqlite3.connect(self.db_path) as c:
            c.execute("UPDATE procedures SET fail_count = fail_count + 1, last_used = ? WHERE id = ?", (time.time(), pid))
            c.commit()
        self._hot = {k: v for k, v in self._hot.items() if v.id != pid}

    def stats(self) -> dict:
        with sqlite3.connect(self.db_path) as c:
            total = c.execute("SELECT COUNT(*) FROM procedures").fetchone()[0]
            top = c.execute("SELECT goal_text, success_count, fail_count FROM procedures ORDER BY success_count DESC LIMIT 10").fetchall()
        return {"total": total, "hot": len(self._hot), "top": [{"goal": g, "ok": s, "fail": f} for g, s, f in top]}
