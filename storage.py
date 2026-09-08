import json
from datetime import datetime
from typing import List, Dict, Any
from config import STORAGE_FILE


def load_seen_jobs() -> Dict[str, Any]:
    if not STORAGE_FILE.exists():
        return {}
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {item if isinstance(item, str) else item.get("id", str(i)): item for i, item in enumerate(data)}
            return {}
    except Exception as e:
        print(f"Error reading {STORAGE_FILE.name}: {e}")
        return {}


def save_seen_jobs(seen_jobs: Dict[str, Any]) -> None:
    try:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(seen_jobs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error writing to {STORAGE_FILE.name}: {e}")


def filter_new_jobs(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen_jobs = load_seen_jobs()
    new_jobs = []

    for job in jobs:
        job_id = job.get("id")
        if not job_id:
            continue
        if job_id not in seen_jobs:
            new_jobs.append(job)

    return new_jobs


def record_jobs(jobs: List[Dict[str, Any]]) -> None:
    seen_jobs = load_seen_jobs()
    now_str = datetime.now().isoformat()

    for job in jobs:
        job_id = job.get("id")
        if not job_id:
            continue
        seen_jobs[job_id] = {
            "title": job.get("title", ""),
            "zone": job.get("zone", ""),
            "deadline": job.get("deadline", ""),
            "url": job.get("url", ""),
            "first_seen": now_str,
        }

    save_seen_jobs(seen_jobs)
