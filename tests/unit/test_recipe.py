from app.recipe_rescuer import generate_fridge_rescue_recipe


def test_fridge_rescue_eggs_beans():
    res = generate_fridge_rescue_recipe(["eggs", "black beans", "salsa"])
    assert "Southwestern" in res["recipe_title"]
    assert res["prep_time_minutes"] <= 10
    assert len(res["instructions"]) > 0
    assert res["estimated_macros"]["protein_grams"] >= 20
    assert "anti_takeout_tip" in res


def test_fridge_rescue_tuna_rice():
    res = generate_fridge_rescue_recipe(["canned tuna", "leftover rice"])
    assert "Tuna" in res["recipe_title"]
    assert res["prep_time_minutes"] <= 10
    assert res["estimated_macros"]["protein_grams"] >= 30


def test_fridge_rescue_fallback():
    res = generate_fridge_rescue_recipe(["mushrooms", "bell pepper", "tofu"])
    assert res["prep_time_minutes"] <= 10
    assert len(res["instructions"]) > 0
    assert res["estimated_macros"]["calories"] > 0
