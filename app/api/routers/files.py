import json
import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.services.storage_service import storage_service

router = APIRouter(prefix="/files", tags=["files"])


def _latest_json_file(platform: str, kind: Literal["raw", "processed"]) -> Path | None:
    platform = platform.lower()
    if kind == "raw":
        files = list(storage_service.raw_dir.glob(f"{platform}_*.json"))
    else:
        files = list(storage_service.processed_dir.glob(f"{platform}_processed_*.json"))

    if not files:
        return None

    return sorted(files, key=os.path.getmtime, reverse=True)[0]


@router.get("/latest/{platform}")
def get_latest_file(
    platform: str,
    kind: Literal["raw", "processed"] = Query("raw"),
):
    latest_file = _latest_json_file(platform, kind)
    if latest_file is None:
        return {
            "platform": platform.lower(),
            "kind": kind,
            "source_file": None,
            "total_records": 0,
            "data": [],
            "message": f"No {kind} data found for platform: {platform.lower()}",
        }

    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading {kind} data: {str(e)}")

    return {
        "platform": platform.lower(),
        "kind": kind,
        "source_file": latest_file.name,
        "total_records": len(data) if isinstance(data, list) else 1,
        "data": data,
    }


@router.get("/list/{platform}")
def list_files(
    platform: str,
    kind: Literal["raw", "processed", "all"] = Query("all"),
):
    platform = platform.lower()
    file_specs = []

    if kind in ("raw", "all"):
        file_specs.extend(("raw", file) for file in storage_service.raw_dir.glob(f"{platform}_*.json"))
    if kind in ("processed", "all"):
        file_specs.extend(("processed", file) for file in storage_service.processed_dir.glob(f"{platform}_processed_*.json"))

    files = []
    for file_kind, file_path in sorted(file_specs, key=lambda item: os.path.getmtime(item[1]), reverse=True):
        files.append(
            {
                "kind": file_kind,
                "name": file_path.name,
                "size_bytes": file_path.stat().st_size,
                "modified_at": file_path.stat().st_mtime,
            }
        )

    return {
        "platform": platform,
        "kind": kind,
        "total_files": len(files),
        "files": files,
    }
