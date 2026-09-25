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

"""Pantry Fridge-Rescue recipe generator to prevent fast-food takeout on busy workdays."""

from typing import Any


def generate_fridge_rescue_recipe(
    ingredients: list[str],
    max_prep_minutes: int = 10,
    dietary_goal: str = "high_protein",
    servings: int = 1,
) -> dict[str, Any]:
    """Synthesizes a nutritious, fast 10-minute recipe from 2-4 pantry/fridge ingredients on hand."""
    cleaned_ingredients = [item.strip().lower() for item in ingredients if item.strip()]
    if not cleaned_ingredients:
        cleaned_ingredients = ["eggs", "spinach"]

    joined_names = " ".join(cleaned_ingredients)

    # 1. Southwestern Black Bean & Egg Scramble
    if any(k in joined_names for k in ["egg", "eggs"]) and any(k in joined_names for k in ["bean", "black bean", "salsa", "tortilla"]):
        return {
            "recipe_title": "10-Minute Southwestern Black Bean & Egg Scramble",
            "prep_time_minutes": min(max_prep_minutes, 10),
            "difficulty": "Easy (1 pan)",
            "ingredients_used": cleaned_ingredients,
            "pantry_staples_assumed": ["1 tsp olive oil or butter", "salt", "black pepper", "cumin (optional)"],
            "instructions": [
                "Warm 1 tsp oil in a non-stick skillet over medium heat.",
                "Rinse 1/2 cup of black beans and add to the skillet with a pinch of cumin/salt; warm for 2 minutes.",
                "Crack 2-3 eggs directly into the skillet, gently folding and scrambling until soft curds form (about 2-3 minutes).",
                "Remove from heat, top with 2-3 tbsp salsa, and enjoy straight from the bowl or wrapped in a warm tortilla.",
            ],
            "estimated_macros": {
                "calories": 360 * servings,
                "protein_grams": 26 * servings,
                "carbs_grams": 24 * servings,
                "fat_grams": 16 * servings,
            },
            "anti_takeout_tip": "Done in 8 minutes — saves ~$22 and 40 minutes of waiting for delivery!",
        }

    # 2. Spicy Canned Tuna & Rice Bowl
    if any(k in joined_names for k in ["tuna", "salmon", "canned fish"]) and any(k in joined_names for k in ["rice", "grain", "quinoa", "nori", "mayo"]):
        return {
            "recipe_title": "8-Minute High-Protein Spicy Tuna Rice Bowl",
            "prep_time_minutes": min(max_prep_minutes, 8),
            "difficulty": "Easy (No cook / microwave)",
            "ingredients_used": cleaned_ingredients,
            "pantry_staples_assumed": ["1 tsp sriracha or hot sauce", "1 tsp soy sauce", "sesame seeds"],
            "instructions": [
                "Microwave 1 cup of pre-cooked/leftover rice for 60 seconds.",
                "Drain 1 can of tuna and mix in a small bowl with 1 tsp light mayo (or Greek yogurt), 1 tsp sriracha, and 1 tsp soy sauce.",
                "Spoon the seasoned tuna over warm rice.",
                "Top with any available greens, cucumber slices, or crushed seaweed snack.",
            ],
            "estimated_macros": {
                "calories": 410 * servings,
                "protein_grams": 38 * servings,
                "carbs_grams": 44 * servings,
                "fat_grams": 8 * servings,
            },
            "anti_takeout_tip": "38g of lean protein in under 8 minutes without firing up the stove.",
        }

    # 3. Quick Veggie & Egg Fried Rice / Stir-Fry
    if any(k in joined_names for k in ["rice", "grain"]) and any(k in joined_names for k in ["egg", "eggs", "tofu", "chicken"]):
        return {
            "recipe_title": "10-Minute Desk-Break Protein Fried Rice",
            "prep_time_minutes": min(max_prep_minutes, 10),
            "difficulty": "Easy (1 skillet)",
            "ingredients_used": cleaned_ingredients,
            "pantry_staples_assumed": ["1 tbsp soy sauce", "1 tsp sesame or olive oil", "garlic powder"],
            "instructions": [
                "Heat skillet with 1 tsp oil over medium-high heat.",
                "Add chopped veggies or protein on hand (tofu, leftover chicken, or greens) and stir-fry for 2 minutes.",
                "Push veggies to side, crack 2 eggs in skillet, scramble until soft.",
                "Toss in 1 cup leftover cold rice, drizzle 1 tbsp soy sauce, and stir-fry vigorously for 3 minutes until sizzling.",
            ],
            "estimated_macros": {
                "calories": 430 * servings,
                "protein_grams": 27 * servings,
                "carbs_grams": 48 * servings,
                "fat_grams": 14 * servings,
            },
            "anti_takeout_tip": "Tastes like takeout fried rice with half the sodium and double the protein.",
        }

    # 4. 5-Minute Power Protein Parfait / Oats
    if any(k in joined_names for k in ["yogurt", "greek yogurt", "oat", "oats", "protein powder", "chia"]):
        return {
            "recipe_title": "5-Minute High-Protein Energy Parfait Bowl",
            "prep_time_minutes": min(max_prep_minutes, 5),
            "difficulty": "Zero Cook",
            "ingredients_used": cleaned_ingredients,
            "pantry_staples_assumed": ["cinnamon", "honey or maple syrup (optional)"],
            "instructions": [
                "Add 1 cup of plain Greek yogurt to a wide bowl.",
                "Stir in 1/2 scoop protein powder or 2 tbsp peanut butter until creamy and smooth.",
                "Top with oats, berries, nuts, or seeds from your pantry.",
                "Dust with cinnamon and enjoy immediately.",
            ],
            "estimated_macros": {
                "calories": 350 * servings,
                "protein_grams": 34 * servings,
                "carbs_grams": 30 * servings,
                "fat_grams": 9 * servings,
            },
            "anti_takeout_tip": "High satiety, zero cooking, and stabilizes blood sugar through long afternoon meetings.",
        }

    # 5. Dynamic Fallback: 10-Minute Express Skillet Medley
    title_items = " & ".join(item.capitalize() for item in cleaned_ingredients[:3])
    return {
        "recipe_title": f"10-Minute Express {title_items} Power Skillet",
        "prep_time_minutes": min(max_prep_minutes, 10),
        "difficulty": "Easy (1 pan)",
        "ingredients_used": cleaned_ingredients,
        "pantry_staples_assumed": ["1 tbsp cooking oil", "salt", "pepper", "garlic powder"],
        "instructions": [
            f"Prep your ingredients ({', '.join(cleaned_ingredients)}) by dicing into bite-sized pieces.",
            "Heat 1 tbsp oil in a skillet over medium heat.",
            "Add denser ingredients first, sautéing for 3-4 minutes until softened.",
            "Add remaining ingredients and season with salt, pepper, and garlic powder; toss for 3 minutes until hot.",
            "Serve hot directly on a plate or over toast/greens.",
        ],
        "estimated_macros": {
            "calories": 380 * servings,
            "protein_grams": 25 * servings,
            "carbs_grams": 30 * servings,
            "fat_grams": 15 * servings,
        },
        "anti_takeout_tip": "A quick, nourishing home-cooked meal ready before your delivery driver would have even accepted the order.",
    }
