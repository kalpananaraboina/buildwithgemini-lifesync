# ruff: noqa
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

import datetime
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Any

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.tools import ToolContext
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback
from app.firestore_db import (
    search_workouts_db,
    get_workout_db,
    save_workout_db,
    log_completion_db,
)
from app.nutrition_calculator import compute_tdee_and_macros
from app.recipe_rescuer import generate_fridge_rescue_recipe
from app.image_generator import generate_domain_image
from app.maps_service import geocode_address, search_nearby_places

MODEL = "gemini-3.6-flash"


def search_workouts(
    category: str = "",
    max_duration_minutes: int = 0,
    equipment: str = "",
) -> list[dict[str, Any]]:
    """Search the Firestore workout collection for available routines matching the user's constraints.

    Args:
        category: Optional category filter. Examples: 'desk_mobility', 'express_cardio', 'core', 'strength', 'recovery'.
        max_duration_minutes: Optional maximum duration in minutes (e.g. 5, 10, 15, 20). 0 means any duration.
        equipment: Optional equipment filter. Examples: 'none', 'chair', 'dumbbells', 'yoga mat'.

    Returns:
        A list of workout documents matching the criteria from Firestore.
    """
    return search_workouts_db(
        category=category,
        max_duration_minutes=max_duration_minutes,
        equipment=equipment,
    )


def get_workout(workout_id: str) -> dict[str, Any]:
    """Retrieve full details and step-by-step instructions for a specific workout from Firestore.

    Args:
        workout_id: The unique ID of the workout (e.g. 'desk-mobility-reset', 'lunchtime-energy-hiit').

    Returns:
        The workout document containing instructions, muscle targets, and difficulty.
    """
    res = get_workout_db(workout_id)
    if not res:
        return {"error": f"Workout '{workout_id}' not found in Firestore."}
    return res


def add_workout(
    title: str,
    category: str,
    duration_minutes: int,
    equipment: str = "none",
    difficulty: str = "beginner",
    target_muscles: list[str] = ["full body"],
    instructions: list[str] = ["Perform with controlled form."],
    burnout_friendly: bool = True,
    calories_burned_approx: int = 50,
) -> dict[str, Any]:
    """Save a new custom workout routine into the Firestore workouts collection.

    Args:
        title: The descriptive title of the workout (e.g. '7-Min Wrist & Shoulder Release').
        category: Workout category ('desk_mobility', 'express_cardio', 'core', 'strength', 'recovery').
        duration_minutes: Length of routine in minutes.
        equipment: Equipment needed ('none', 'chair', 'dumbbells', 'yoga mat', etc.).
        difficulty: Level ('beginner', 'intermediate', 'advanced').
        target_muscles: List of muscles targeted (e.g. ['wrists', 'forearms', 'shoulders']).
        instructions: Step-by-step exercise cues.
        burnout_friendly: Whether this is gentle enough for low-energy / busy workdays.
        calories_burned_approx: Estimated calorie burn.

    Returns:
        The created workout document confirming storage in Firestore.
    """
    return save_workout_db(
        title=title,
        category=category,
        duration_minutes=duration_minutes,
        equipment=equipment,
        difficulty=difficulty,
        target_muscles=target_muscles,
        instructions=instructions,
        burnout_friendly=burnout_friendly,
        calories_burned_approx=calories_burned_approx,
    )


def log_workout(
    workout_id: str,
    notes: str = "",
    energy_rating: int = 4,
) -> dict[str, Any]:
    """Log the completion of a workout in Firestore to record user progress and track energy recovery.

    Args:
        workout_id: The ID of the workout completed.
        notes: Optional notes or reflections on how the user felt.
        energy_rating: Energy level after workout from 1 (drained) to 5 (energized).

    Returns:
        The created log entry saved in Firestore.
    """
    return log_completion_db(
        workout_id=workout_id,
        notes=notes,
        energy_rating=energy_rating,
    )


def calculate_tdee_and_macros(
    weight_lbs: float = 0.0,
    weight_kg: float = 0.0,
    height_inches: float = 0.0,
    height_cm: float = 0.0,
    age_years: int = 30,
    gender: str = "male",
    activity_level: str = "sedentary",
    goal: str = "maintain",
) -> dict[str, Any]:
    """Calculate precise daily energy targets (BMR, TDEE, target calories) and macronutrient breakdown (protein, carbs, fats in grams) using the Mifflin-St Jeor formula.

    Args:
        weight_lbs: Body weight in pounds (or specify weight_kg).
        weight_kg: Body weight in kilograms (or specify weight_lbs).
        height_inches: Height in inches (e.g. 70 for 5'10", or specify height_cm).
        height_cm: Height in centimeters.
        age_years: Age in years.
        gender: 'male' or 'female'.
        activity_level: Level of activity/workday movement: 'sedentary' (desk job), 'light' (desk job + light walks), 'moderate' (exercise 3-5x/wk), 'very_active' (heavy training 6-7x/wk).
        goal: Nutrition goal: 'maintain' (energy balance), 'fat_loss' (healthy deficit), or 'muscle_gain' (lean surplus).

    Returns:
        A dictionary containing BMR, TDEE, target calories, protein grams, carbohydrate grams, fat grams, hydration target, and personalized recommendation.
    """
    return compute_tdee_and_macros(
        weight_lbs=weight_lbs,
        weight_kg=weight_kg,
        height_inches=height_inches,
        height_cm=height_cm,
        age_years=age_years,
        gender=gender,
        activity_level=activity_level,
        goal=goal,
    )


def fridge_rescue_recipe(
    ingredients: list[str],
    max_prep_minutes: int = 10,
    dietary_goal: str = "high_protein",
    servings: int = 1,
) -> dict[str, Any]:
    """Synthesizes a fast, healthy 10-minute recipe from 2-4 pantry or fridge ingredients on hand to prevent fast-food takeout on busy workdays.

    Args:
        ingredients: List of 2 to 4 ingredients available in the fridge or pantry (e.g. ['eggs', 'black beans', 'salsa'] or ['canned tuna', 'rice']).
        max_prep_minutes: Maximum cooking/prep time in minutes (default 10).
        dietary_goal: Nutritional focus (e.g. 'high_protein', 'balanced', 'low_carb').
        servings: Number of servings (default 1).

    Returns:
        A dictionary with recipe title, prep time, instructions, macro breakdown, and anti-takeout time & money savings.
    """
    return generate_fridge_rescue_recipe(
        ingredients=ingredients,
        max_prep_minutes=max_prep_minutes,
        dietary_goal=dietary_goal,
        servings=servings,
    )


async def generate_domain_image(
    prompt: str,
    category: str = "meal",
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Generate an image for an item in LifeSync's domain (healthy meal, recipe, desk mobility stretch, or workout posture) using gemini-3.1-flash-lite-image in the global region.

    Saves the generated image as an artifact in the session (so it appears in the Playground's Artifacts panel)
    and uploads the in-memory bytes directly to public Cloud Storage, returning the public https URL.

    Args:
        prompt: Detailed visual prompt describing the item (e.g. 'Avocado and poached egg toast with microgreens, professional food photography' or 'Seated desk worker doing neck and shoulder stretch, minimalist fitness illustration').
        category: Item category ('meal', 'recipe', 'workout', 'mobility', 'badge').
        tool_context: ADK ToolContext injected by the agent runtime.

    Returns:
        A dictionary containing the public Cloud Storage https URL (https://storage.googleapis.com/<bucket>/<object>), status, and metadata.
    """
    from app.image_generator import generate_domain_image as _gen_img
    return await _gen_img(prompt=prompt, category=category, tool_context=tool_context)


# Alias for backward compatibility
generate_visual = generate_domain_image


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


async def generate_memories_callback(callback_context: CallbackContext) -> None:
    """Save salient user facts, health goals, injuries, or dietary preferences into Vertex AI Memory Bank after each turn."""
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        # Gracefully tolerate environments where Memory Bank service is in-memory
        pass
    return None


# Build A2UI v0.8 system prompt
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are LifeSync, an intelligent wellness and lifestyle coach designed for busy professionals. "
        "Your goal is to help users balance demanding work hours with consistent movement, smart nutrition, and daily recovery. "
        "You remember user preferences, physical limitations, dietary habits, and past routines across sessions to personalize all recommendations."
    ),
    workflow_description=(
        "Analyze the user's request. Always call relevant tools to get real data or compute metrics: "
        "- For workout recommendations, search, steps, or logs, use `search_workouts`, `get_workout`, `add_workout`, or `log_workout`. "
        "- For calculating energy, calories, or macros, use `calculate_tdee_and_macros`. "
        "- When the user has ingredients on hand and needs a fast meal, use `fridge_rescue_recipe`. "
        "- When the user requests an image, photo, picture, or visual (e.g. for any meal, recipe, exercise, posture, or stretch), you MUST call `generate_domain_image` to generate it, and then embed the returned public image_url in an Image component inside your A2UI response so the user sees the rendered image. "
        "- To convert an address or location name to coordinates, use `geocode_address`. "
        "- To find nearby places (gyms, parks, supermarkets, healthy restaurants, spas), use `search_nearby_places`. "
        "- For weather or local time, use `get_weather` or `get_current_time`. "
        "- For complex mathematical calculations, formulas, progress projections, or running Python code safely, use your Agent Platform sandbox code execution environment to execute code and report verified findings. "
        "When returning workout recommendations, nutrition plans, or recipe suggestions, present the result as a rich, structured display UI Card."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example https://storage.googleapis.com/lifesync-assets-5e6e400fb101/...). "
        "Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

DEFAULT_SANDBOX_RESOURCE_NAME = (
    "projects/976432994584/locations/us-east1/reasoningEngines/7912039493987729408/sandboxEnvironments/1459852374523772928"
)
DEFAULT_AGENT_ENGINE_NAME = (
    "projects/976432994584/locations/us-east1/reasoningEngines/7912039493987729408"
)


def _init_sandbox_code_executor() -> AgentEngineSandboxCodeExecutor:
    """Initialize AgentEngineSandboxCodeExecutor from deployment_metadata.json or default."""
    sandbox_res = DEFAULT_SANDBOX_RESOURCE_NAME
    engine_res = DEFAULT_AGENT_ENGINE_NAME
    metadata_path = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                sandbox_res = meta.get("sandbox_resource_name", sandbox_res)
                engine_res = meta.get("remote_agent_runtime_id", engine_res)
        except Exception:
            pass
    return AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=sandbox_res,
        agent_engine_resource_name=engine_res,
    )


sandbox_code_executor = _init_sandbox_code_executor()

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        search_workouts,
        get_workout,
        add_workout,
        log_workout,
        calculate_tdee_and_macros,
        fridge_rescue_recipe,
        generate_domain_image,
        geocode_address,
        search_nearby_places,
        get_weather,
        get_current_time,
    ],
    code_executor=sandbox_code_executor,
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
