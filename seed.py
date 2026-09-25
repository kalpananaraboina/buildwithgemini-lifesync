"""Seed Firestore with initial workout routines for LifeSync."""

from google.cloud import firestore

# Hardcode GCP Project ID as a string.
# On Agent Platform, google.auth.default() and GOOGLE_CLOUD_PROJECT return the project number,
# which breaks Firestore calls if used instead of the project ID.
PROJECT_ID = "qwiklabs-gcp-03-5e6e400fb101"

SEEDED_WORKOUTS = [
    {
        "id": "desk-mobility-reset",
        "title": "5-Min Desk Mobility & Posture Reset",
        "category": "desk_mobility",
        "duration_minutes": 5,
        "equipment": "chair",
        "difficulty": "beginner",
        "target_muscles": ["neck", "shoulders", "chest", "hip flexors"],
        "burnout_friendly": True,
        "instructions": [
            "Seated spinal twist: 30s each side with gentle diaphragmatic breathing.",
            "Desk chest opener: place hands behind head, extend upper back over chair back (5 slow reps).",
            "Seated figure-4 hip stretch: ankle over opposite knee, hinge forward gently (45s each leg).",
            "Standing quad stretch with chair support (30s each side)."
        ],
        "calories_burned_approx": 20,
    },
    {
        "id": "lunchtime-energy-hiit",
        "title": "15-Min Lunchtime Energy HIIT",
        "category": "express_cardio",
        "duration_minutes": 15,
        "equipment": "none",
        "difficulty": "intermediate",
        "target_muscles": ["full body", "legs", "core"],
        "burnout_friendly": False,
        "instructions": [
            "Warmup: 2 minutes of brisk high knees and arm circles.",
            "Circuit (3 rounds, 40s work / 20s rest): Bodyweight squats, mountain climbers, alternating reverse lunges, shadow boxing.",
            "Cooldown: 1 minute gentle forward fold and slow breathing."
        ],
        "calories_burned_approx": 130,
    },
    {
        "id": "core-back-stabilizer",
        "title": "10-Min Core & Lower Back Stabilizer",
        "category": "core",
        "duration_minutes": 10,
        "equipment": "yoga mat",
        "difficulty": "beginner",
        "target_muscles": ["abs", "lower back", "glutes"],
        "burnout_friendly": True,
        "instructions": [
            "Deadbugs: 3 sets of 10 slow controlled reps.",
            "Bird-dogs: 3 sets of 8 reps per side focusing on neutral spine.",
            "Glute bridges: 2 sets of 15 reps with 2-second hold at the top.",
            "Child's pose: 60s deep relaxation breathing to decompress lower back."
        ],
        "calories_burned_approx": 55,
    },
    {
        "id": "dumbbell-full-body",
        "title": "20-Min Dumbbell Full-Body Strength",
        "category": "strength",
        "duration_minutes": 20,
        "equipment": "dumbbells",
        "difficulty": "intermediate",
        "target_muscles": ["legs", "shoulders", "upper back", "arms"],
        "burnout_friendly": False,
        "instructions": [
            "Goblet Squats: 3 sets of 10 reps.",
            "Dumbbell Romanian Deadlifts: 3 sets of 10 reps.",
            "Standing Overhead Dumbbell Press: 3 sets of 8 reps.",
            "Bent-over Dumbbell Rows: 3 sets of 10 reps."
        ],
        "calories_burned_approx": 160,
    },
    {
        "id": "evening-stress-release",
        "title": "8-Min Evening Stress Decompression",
        "category": "recovery",
        "duration_minutes": 8,
        "equipment": "yoga mat",
        "difficulty": "beginner",
        "target_muscles": ["full body", "nervous system"],
        "burnout_friendly": True,
        "instructions": [
            "Legs-up-the-wall pose: 3 minutes with 4s inhale, 6s exhale.",
            "Supine spinal twist: 90s each side.",
            "Corpse pose (Savasana): 2 minutes relaxing jaw, eyes, and shoulders."
        ],
        "calories_burned_approx": 25,
    },
]


def seed():
    print(f"Connecting to Firestore with project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("workouts")

    for workout in SEEDED_WORKOUTS:
        doc_id = workout["id"]
        collection_ref.document(doc_id).set(workout)
        print(f"  ✓ Seeded workout '{workout['title']}' (id: {doc_id})")

    print(f"\nSuccessfully seeded {len(SEEDED_WORKOUTS)} workouts into 'workouts' collection in {PROJECT_ID}!")


if __name__ == "__main__":
    seed()
