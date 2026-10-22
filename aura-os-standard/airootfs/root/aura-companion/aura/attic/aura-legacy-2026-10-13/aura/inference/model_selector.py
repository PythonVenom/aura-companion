"""Model Selector — выбор модели под железо (ADR-153).

Наука:
- Chen, T., et al. (2024). Hardware-Aware Model Selection for Edge. arXiv.
- Google (2019). MLPerf Inference Benchmark. arXiv:1910.01500.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ModelConfig:
    profile: str
    llm: str
    asr: str
    tts: str
    memory_layers: list
    react_max_iter: int
    streaming: bool
    batch_size: int
    num_threads: int
    cache_embeddings: bool


PROFILES = {
    "minimal": ModelConfig("minimal", "", "kws", "piper-low",
        ["working", "episodic", "semantic", "prospective", "emotional", "social"],
        1, False, 1, 2, True),
    "minimal_plus": ModelConfig("minimal_plus", "qwen2.5:0.5b-instruct-q4_K_M",
        "t-one-small", "piper-low",
        ["working", "episodic", "semantic", "prospective", "emotional", "social"],
        1, True, 1, 2, True),
    "edge": ModelConfig("edge", "qwen2.5:1.5b-instruct-q4_K_M",
        "t-one-small", "piper-low",
        ["working", "episodic", "semantic", "prospective", "emotional", "social"],
        1, True, 1, 4, True),
    "standard": ModelConfig("standard", "qwen2.5:3b-instruct-q4_K_M",
        "t-one-base", "piper-medium",
        ["working", "episodic", "semantic", "prospective", "emotional",
         "spatial", "social", "meta"],
        2, True, 1, 4, True),
    "powerful": ModelConfig("powerful", "qwen2.5:7b-instruct-q4_K_M",
        "whisper-large-v3", "xtts-v2",
        ["working", "episodic", "semantic", "prospective", "emotional",
         "spatial", "social", "meta"],
        3, True, 4, 8, True),
}


def select(hw_info) -> ModelConfig:
    ram = hw_info.ram_total_gb
    threads = hw_info.cpu_threads
    has_gpu = hw_info.has_gpu
    if ram < 4:
        base = "minimal"
    elif ram < 6:
        base = "minimal_plus"
    elif ram < 10:
        base = "edge"
    elif ram < 20:
        base = "standard"
    else:
        base = "powerful"
    cfg = PROFILES[base]
    cfg.num_threads = max(1, min(threads, 8))
    if has_gpu and base in ("edge", "standard"):
        cfg.profile = "powerful" if ram >= 16 else "standard"
    return cfg


def save(cfg: ModelConfig) -> None:
    import json
    p = Path.home() / ".cache" / "aura" / "active_profile.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(asdict(cfg), indent=2, ensure_ascii=False), encoding="utf-8")


def load() -> ModelConfig | None:
    import json
    p = Path.home() / ".cache" / "aura" / "active_profile.json"
    if not p.exists():
        return None
    try:
        return ModelConfig(**json.loads(p.read_text(encoding="utf-8")))
    except Exception:
        return None
