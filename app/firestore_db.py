# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Firestore database layer for LifeSync agent.

Important: Hardcode the GCP project ID as a string.
On Agent Platform, google.auth.default() and GOOGLE_CLOUD_PROJECT return
the numeric project number, which breaks Firestore client calls.
"""

from datetime import datetime, timezone
from typing import Any
import uuid
from google.cloud import firestore

# Hardcoded GCP Project ID
PROJECT_ID = "qwiklabs-gcp-03-5e6e400fb101"

_client: firestore.Client | None = None


def get_db() -> firestore.Client:
    """Get or create singleton Firestore client with hardcoded project ID."""
    global _client
    if _client is None:
        _client = firestore.Client(project=PROJECT_ID)
    return _client


def search_workouts_db(
    category: str = "",
    max_duration_minutes: int = 0,
    equipment: str = "",
) -> list[dict[str, Any]]:
    """Query workouts from Firestore collection with optional filters."""
    db = get_db()
    col = db.collection("workouts")
    docs = col.stream()

    results: list[dict[str, Any]] = []
    category_lower = category.strip().lower() if category else ""
    equipment_lower = equipment.strip().lower() if equipment else ""

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        # Category filter (e.g. desk_mobility, express_cardio, core, strength, recovery)
        if category_lower and category_lower not in data.get("category", "").lower():
            continue

        # Max duration filter
        if max_duration_minutes > 0 and data.get("duration_minutes", 0) > max_duration_minutes:
            continue

        # Equipment filter (e.g. none, chair, dumbbells, yoga mat)
        if equipment_lower and equipment_lower not in data.get("equipment", "").lower():
            continue

        results.append(data)

    return results


def get_workout_db(workout_id: str) -> dict[str, Any] | None:
    """Fetch a single workout by its document ID."""
    db = get_db()
    doc_ref = db.collection("workouts").document(workout_id.strip())
    doc = doc_ref.get()
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return data


def save_workout_db(
    title: str,
    category: str,
    duration_minutes: int,
    equipment: str = "none",
    difficulty: str = "beginner",
    target_muscles: list[str] | None = None,
    instructions: list[str] | None = None,
    burnout_friendly: bool = True,
    calories_burned_approx: int = 50,
) -> dict[str, Any]:
    """Save a new workout to the Firestore collection."""
    db = get_db()
    slug = title.strip().lower().replace(" ", "-")[:30]
    doc_id = f"{slug}-{uuid.uuid4().hex[:6]}"

    record = {
        "id": doc_id,
        "title": title.strip(),
        "category": category.strip().lower(),
        "duration_minutes": duration_minutes,
        "equipment": equipment.strip().lower(),
        "difficulty": difficulty.strip().lower(),
        "target_muscles": target_muscles or ["full body"],
        "instructions": instructions or ["Follow proper form and breathe steadily."],
        "burnout_friendly": burnout_friendly,
        "calories_burned_approx": calories_burned_approx,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    db.collection("workouts").document(doc_id).set(record)
    return record


def log_completion_db(
    workout_id: str,
    notes: str = "",
    energy_rating: int = 4,
) -> dict[str, Any]:
    """Log completion of a workout in Firestore 'workout_logs' collection."""
    db = get_db()
    log_id = f"log-{uuid.uuid4().hex[:8]}"

    # Verify workout existence if possible
    workout_doc = get_workout_db(workout_id)
    workout_title = workout_doc["title"] if workout_doc else workout_id

    log_entry = {
        "id": log_id,
        "workout_id": workout_id,
        "workout_title": workout_title,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "notes": notes.strip(),
        "energy_rating": max(1, min(5, energy_rating)),
    }

    db.collection("workout_logs").document(log_id).set(log_entry)
    return log_entry
