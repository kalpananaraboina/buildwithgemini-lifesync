from app.nutrition_calculator import compute_tdee_and_macros


def test_tdee_calculation_male():
    res = compute_tdee_and_macros(
        weight_lbs=175,
        height_inches=70,
        age_years=30,
        gender="male",
        activity_level="sedentary",
        goal="maintain",
    )
    assert res["user_profile"]["gender"] == "male"
    assert res["energy_targets"]["bmr_calories"] > 1500
    assert res["energy_targets"]["tdee_calories"] > res["energy_targets"]["bmr_calories"]
    assert res["macronutrients"]["protein_grams"] > 0
    assert res["macronutrients"]["carbohydrates_grams"] > 0
    assert res["macronutrients"]["fat_grams"] > 0
    assert res["hydration_target_liters"] > 2.0


def test_tdee_calculation_fat_loss():
    res = compute_tdee_and_macros(
        weight_kg=60,
        height_cm=165,
        age_years=28,
        gender="female",
        activity_level="light",
        goal="fat_loss",
    )
    assert res["user_profile"]["gender"] == "female"
    assert res["energy_targets"]["daily_target_calories"] < res["energy_targets"]["tdee_calories"]
    assert res["macronutrients"]["protein_grams"] > 100
