"""Profile Ledger ??? ???????????? ?? ?????????? ?????? ?????????????? (???? Steam).
??????????: Micro-credentials (EU 2024), Ed25519 signing,
        LinkedIn Skills Verification.
"""
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

LEDGER = Path.home() / ".local/share/aura/mentor/ledger.jsonl"


@dataclass
class Achievement:
    user: str
    skill_id: str
    score: int            # 0-100
    verified_at: str
    reviewer: str = "aura"  # aura | human | company
    signature: str = ""     # sha256 (Ed25519 ??????????)

    def sign(self, secret: str = "aura-local"):
        raw = f"{self.user}:{self.skill_id}:{self.score}:{self.verified_at}:{secret}"
        self.signature = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self


class ProfileLedger:
    def __init__(self, user: str = "batya"):
        self.user = user
        LEDGER.parent.mkdir(parents=True, exist_ok=True)

    def add(self, skill_id: str, score: int, reviewer: str = "aura") -> Achievement:
        ach = Achievement(
            user=self.user,
            skill_id=skill_id,
            score=score,
            verified_at=datetime.now().isoformat(),
            reviewer=reviewer,
        ).sign()
        with LEDGER.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(ach), ensure_ascii=False) + "\n")
        return ach

    def list(self) -> list:
        if not LEDGER.exists():
            return []
        return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]

    def career_score(self) -> dict:
        """?????? ?? ????????: score ?? reviewer_multiplier."""
        multipliers = {"aura": 1.0, "human": 1.5, "company": 2.0}
        ach = self.list()
        total = sum(a["score"] * multipliers.get(a["reviewer"], 1.0)
                    for a in ach)
        return {
            "achievements": len(ach),
            "career_score": round(total, 1),
            "by_reviewer": {r: sum(1 for a in ach if a["reviewer"] == r)
                            for r in multipliers},
        }


if __name__ == "__main__":
    pl = ProfileLedger("test_batya")
    pl.add("bash-basics", 85, "aura")
    pl.add("python-syntax", 92, "human")
    print("=== LEDGER ===")
    for a in pl.list():
        print(f"  {a['skill_id']:20} score={a['score']:3} by={a['reviewer']:8} sig={a['signature']}")
    print(f"\nCareer: {pl.career_score()}")
