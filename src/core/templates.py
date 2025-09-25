from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict

from .models import ProjectState, ExportOptions


def _templates_dir() -> Path:
    base = Path(os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming")))
    d = base / "PhotoWatermark2" / "templates"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_last(state: ProjectState, export: ExportOptions) -> None:
    data = {
        "project": asdict(state),
        "export": asdict(export),
    }
    path = _templates_dir() / "last.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_last() -> tuple[ProjectState | None, ExportOptions | None]:
    path = _templates_dir() / "last.json"
    if not path.exists():
        return None, None
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        project = ProjectState(**data["project"])  # type: ignore[arg-type]
        export = ExportOptions(**data["export"])  # type: ignore[arg-type]
        return project, export
    except Exception:
        return None, None


def save_named(name: str, state: ProjectState, export: ExportOptions) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in ("_", "-", ".")) or "template"
    path = _templates_dir() / f"{safe}.json"
    data = {
        "project": asdict(state),
        "export": asdict(export),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def list_templates() -> list[str]:
    return [p.name for p in _templates_dir().glob("*.json") if p.name != "last.json"]


def delete_template(name: str) -> None:
    p = _templates_dir() / name
    if p.exists():
        p.unlink()


