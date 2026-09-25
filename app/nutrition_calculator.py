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

"""Deterministic TDEE (Total Daily Energy Expenditure) and Macronutrient Calculator."""

from typing import Any


def compute_tdee_and_macros(
    weight_lbs: float = 0.0,
    weight_kg: float = 0.0,
    height_inches: float = 0.0,
    height_cm: float = 0.0,
    age_years: int = 30,
    gender: str = "male",
    activity_level: str = "sedentary",
    goal: str = "maintain",
) -> dict[str, Any]:
    """Calculates BMR, TDEE, and macronutrient targets using the Mifflin-St Jeor formula."""
    # Normalize weight to kg
    if weight_kg > 0:
        w_kg = weight_kg
        w_lbs = weight_kg * 2.20462
    elif weight_lbs > 0:
        w_kg = weight_lbs / 2.20462
        w_lbs = weight_lbs
    else:
        # Default fallback: 70kg / 154lbs
        w_kg = 70.0
        w_lbs = 154.0

    # Normalize height to cm
    if height_cm > 0:
        h_cm = height_cm
    elif height_inches > 0:
        h_cm = height_inches * 2.54
    else:
        # Default fallback: 175cm (~5'9")
        h_cm = 175.0

    age = max(18, min(100, age_years))
    is_male = gender.strip().lower() in ["male", "m", "man"]

    # Mifflin-St Jeor BMR Equation
    if is_male:
        bmr = (10.0 * w_kg) + (6.25 * h_cm) - (5.0 * age) + 5
    else:
        bmr = (10.0 * w_kg) + (6.25 * h_cm) - (5.0 * age) - 161

    # Activity multiplier based on lifestyle/workday
    act_lower = activity_level.strip().lower()
    if "extra" in act_lower or "athlete" in act_lower:
        multiplier = 1.9
        act_desc = "Extra active (high physical job or double daily training)"
    elif "very" in act_lower or "heavy" in act_lower:
        multiplier = 1.725
        act_desc = "Very active (intense exercise 6-7 days/week)"
    elif "mod" in act_lower:
        multiplier = 1.55
        act_desc = "Moderately active (moderate exercise 3-5 days/week)"
    elif "light" in act_lower:
        multiplier = 1.375
        act_desc = "Lightly active (desk job with light movement/walks 1-3 days/week)"
    else:
        multiplier = 1.2
        act_desc = "Sedentary (desk job, minimal structured movement)"

    tdee = bmr * multiplier

    # Adjust for goal
    goal_lower = goal.strip().lower()
    if "loss" in goal_lower or "cut" in goal_lower or "deficit" in goal_lower or "lose" in goal_lower:
        target_cal = tdee - 400.0
        goal_desc = "Fat Loss (~400 kcal healthy daily deficit)"
        # Protein slightly higher for muscle sparing during deficit (~2.2g/kg)
        protein_g_per_kg = 2.2
    elif "gain" in goal_lower or "bulk" in goal_lower or "surplus" in goal_lower or "build" in goal_lower:
        target_cal = tdee + 350.0
        goal_desc = "Lean Muscle Gain (~350 kcal healthy daily surplus)"
        protein_g_per_kg = 2.0
    else:
        target_cal = tdee
        goal_desc = "Energy Balance & Weight Maintenance"
        protein_g_per_kg = 1.8

    # Apply safe floor
    min_floor = 1500.0 if is_male else 1200.0
    target_cal = max(min_floor, target_cal)

    # Macronutrient breakdown
    # 1. Protein: 4 kcal per gram
    protein_g = round(w_kg * protein_g_per_kg)
    protein_cal = protein_g * 4

    # 2. Fats: 25-30% of target calories, 9 kcal per gram
    fat_cal = target_cal * 0.28
    fat_g = round(fat_cal / 9.0)

    # 3. Carbs: remaining calories, 4 kcal per gram
    remaining_cal = max(0.0, target_cal - (protein_cal + (fat_g * 9.0)))
    carbs_g = round(remaining_cal / 4.0)
    carbs_cal = carbs_g * 4

    # Daily water requirement: ~35 ml per kg of bodyweight
    water_liters = round((w_kg * 0.035), 1)

    return {
        "user_profile": {
            "weight_lbs": round(w_lbs, 1),
            "weight_kg": round(w_kg, 1),
            "height_cm": round(h_cm, 1),
            "age": age,
            "gender": "male" if is_male else "female",
            "activity_profile": act_desc,
            "goal": goal_desc,
        },
        "energy_targets": {
            "bmr_calories": round(bmr),
            "tdee_calories": round(tdee),
            "daily_target_calories": round(target_cal),
        },
        "macronutrients": {
            "protein_grams": protein_g,
            "carbohydrates_grams": carbs_g,
            "fat_grams": fat_g,
            "protein_percent": round((protein_cal / target_cal) * 100),
            "carbs_percent": round((carbs_cal / target_cal) * 100),
            "fat_percent": round(((fat_g * 9.0) / target_cal) * 100),
        },
        "hydration_target_liters": water_liters,
        "recommendation": (
            f"Daily target: {round(target_cal)} kcal. Aim for {protein_g}g protein, "
            f"{carbs_g}g carbs, and {fat_g}g fats with {water_liters}L of water."
        ),
    }
