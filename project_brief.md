# My agent: LifeSync
One-liner: A conversational wellness coach that helps busy professionals balance high-demand work with fitness and nutrition through a catalog of time-efficient workouts, adaptive meal recipes, and daily recovery routines.

Tool coverage:
- Memory: Remembers work schedule intensity (heavy meeting days vs. deep work), energy patterns, fitness level, available home/gym equipment, dietary preferences and allergies, and daily check-in history.
- Tools:
  - `search_workouts`: Looks up routines based on available time (5-min desk stretch, 20-min express workout, 45-min strength) and muscle focus.
  - `fridge_rescue_recipe`: Generates nutritious 10-minute recipes based on 2-3 ingredients on hand to prevent fast-food takeout.
  - `generate_grocery_list`: Compiles selected weekly meals into a categorized grocery checklist.
  - `log_daily_balance`: Records daily metrics (desk hours, sleep quality, workout completed, mood) to track burnout risk.
- Catalog/UI:
  - Workout Cards: Render exercise name, duration, target muscle group, equipment needed, and step-by-step form cues.
  - Meal & Recipe Cards: Render dish name, prep time, estimated macros (calories, protein, carbs, fats), and ingredient lists.
  - Daily Balance Scorecard: Table displaying work hours vs. active minutes, hydration, and recovery readiness.
- Image gen: Generates appetizing dish presentation images for recommended quick meals, visual posture/stretch guides, and weekly achievement badges.
- Sandbox: Calculates TDEE (Total Daily Energy Expenditure), target macro splits, and work-to-movement ratio computations.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Code sandbox for macro/TDEE calculations, calendar integration for workday intensity triage, end-of-day shutdown ritual prompt.
