"""Unit tests for recipe load, filter, and random selection."""

from __future__ import annotations

import json
import random
from pathlib import Path

from recipes import (
    add_recipe,
    build_recipe,
    filter_recipes,
    id_from_title,
    lines_to_list,
    load_recipes,
    parse_recipes_list,
    pick_random,
    save_recipes,
)


def test_load_valid_recipes(recipes_file: Path, sample_recipes):
    loaded = load_recipes(recipes_file)
    assert len(loaded) == len(sample_recipes)
    assert loaded[0]["id"] == "first-taste-veg"


def test_load_empty_list(empty_recipes_file: Path):
    assert load_recipes(empty_recipes_file) == []


def test_load_missing_file(tmp_path: Path):
    assert load_recipes(tmp_path / "missing.json") == []


def test_load_malformed_json(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")
    assert load_recipes(path) == []


def test_load_non_list_json(tmp_path: Path):
    path = tmp_path / "obj.json"
    path.write_text('{"title": "nope"}', encoding="utf-8")
    assert load_recipes(path) == []


def test_load_skips_invalid_entries(tmp_path: Path, sample_recipes):
    payload = [
        sample_recipes[0],
        {"id": "broken", "title": "Missing fields"},
        {
            "id": "",
            "title": "Bad id",
            "ages": ["around_6_months"],
            "meal_types": ["breakfast"],
            "ingredients": ["x"],
            "steps": ["y"],
        },
        {
            "id": "blank-title",
            "title": "   ",
            "ages": ["around_6_months"],
            "meal_types": ["breakfast"],
            "ingredients": ["x"],
            "steps": ["y"],
        },
        {
            "id": "empty-ages",
            "title": "Empty ages",
            "ages": [],
            "meal_types": ["breakfast"],
            "ingredients": ["x"],
            "steps": ["y"],
        },
        {
            "id": "empty-meals",
            "title": "Empty meals",
            "ages": ["around_6_months"],
            "meal_types": [],
            "ingredients": ["x"],
            "steps": ["y"],
        },
        {
            "id": "empty-ingredients",
            "title": "Empty ingredients",
            "ages": ["around_6_months"],
            "meal_types": ["breakfast"],
            "ingredients": [],
            "steps": ["y"],
        },
        {
            "id": "empty-steps",
            "title": "Empty steps",
            "ages": ["around_6_months"],
            "meal_types": ["breakfast"],
            "ingredients": ["x"],
            "steps": [],
        },
        {
            "id": "bad-age",
            "title": "Bad age",
            "ages": ["toddler"],
            "meal_types": ["breakfast"],
            "ingredients": ["x"],
            "steps": ["y"],
        },
        {
            "id": "bad-meal",
            "title": "Bad meal",
            "ages": ["around_6_months"],
            "meal_types": ["brunch"],
            "ingredients": ["x"],
            "steps": ["y"],
        },
        "not-a-dict",
        sample_recipes[1],
    ]
    path = tmp_path / "mixed.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    loaded = load_recipes(path)
    assert [r["id"] for r in loaded] == ["first-taste-veg", "banana-porridge"]


def test_filter_by_age_only(sample_recipes):
    matched = filter_recipes(sample_recipes, age="around_6_months")
    assert {r["id"] for r in matched} == {"first-taste-veg", "banana-porridge"}


def test_filter_adult_age(sample_recipes):
    matched = filter_recipes(sample_recipes, age="adult")
    assert [r["id"] for r in matched] == ["adult-pasta"]


def test_filter_by_meal_type_only(sample_recipes):
    matched = filter_recipes(sample_recipes, meal_type="dinner")
    assert {r["id"] for r in matched} == {
        "lentil-lunch",
        "dinner-curry",
        "adult-pasta",
    }


def test_filter_by_age_and_meal_type(sample_recipes):
    matched = filter_recipes(
        sample_recipes, age="7_to_9_months", meal_type="breakfast"
    )
    assert [r["id"] for r in matched] == ["banana-porridge"]


def test_filter_any_returns_all(sample_recipes):
    assert filter_recipes(sample_recipes) == sample_recipes
    assert filter_recipes(sample_recipes, age="", meal_type="  ") == sample_recipes


def test_filter_multi_tag_intersection(sample_recipes):
    matched = filter_recipes(sample_recipes, meal_type="snack")
    assert [r["id"] for r in matched] == ["finger-toast"]


def test_filter_no_matches(sample_recipes):
    assert filter_recipes(sample_recipes, age="around_6_months", meal_type="dinner") == []


def test_filter_unknown_age_returns_empty(sample_recipes):
    assert filter_recipes(sample_recipes, age="not-an-age") == []


def test_filter_unknown_meal_returns_empty(sample_recipes):
    assert filter_recipes(sample_recipes, meal_type="brunch") == []


def test_pick_random_empty():
    assert pick_random([]) is None


def test_pick_random_returns_member(sample_recipes):
    rng = random.Random(0)
    picked = pick_random(sample_recipes, rng=rng)
    assert picked in sample_recipes


def test_pick_random_avoids_exclude_when_possible(sample_recipes):
    rng = random.Random(1)
    picked = pick_random(sample_recipes, exclude_id="banana-porridge", rng=rng)
    assert picked is not None
    assert picked["id"] != "banana-porridge"


def test_pick_random_falls_back_when_only_one_candidate(sample_recipes):
    only = [sample_recipes[0]]
    picked = pick_random(only, exclude_id="first-taste-veg")
    assert picked == only[0]


def test_pick_random_exclude_missing_id_still_picks(sample_recipes):
    rng = random.Random(2)
    picked = pick_random(sample_recipes, exclude_id="does-not-exist", rng=rng)
    assert picked in sample_recipes


def test_parse_recipes_list_non_list():
    assert parse_recipes_list({"title": "nope"}) == []


def test_save_recipes_overwrites(tmp_path: Path, sample_recipes):
    path = tmp_path / "nested" / "recipes.json"
    save_recipes(path, sample_recipes[:1])
    assert path.is_file()
    assert load_recipes(path)[0]["id"] == "first-taste-veg"

    save_recipes(path, [])
    assert load_recipes(path) == []


def test_lines_to_list():
    assert lines_to_list("a\n\n b \n") == ["a", "b"]
    assert lines_to_list(None) == []
    assert lines_to_list("") == []


def test_id_from_title():
    assert id_from_title("Banana porridge") == "bananaporridge"
    assert id_from_title("  Mixed  Bean  Stew ") == "mixedbeanstew"
    assert id_from_title("") == ""
    assert id_from_title(None) == ""


def test_build_recipe_valid():
    recipe = build_recipe(
        title=" Banana porridge ",
        ages=["around_6_months", "not-real"],
        meal_types=["breakfast"],
        ingredients_text="1 banana\n2 tbsp oats",
        steps_text="Cook oats\nMash banana",
        prep_time=" 5 mins ",
        cook_time="10 mins",
        portions="2",
        notes=" Soft tip ",
        source=" Book ",
    )
    assert recipe is not None
    assert recipe["id"] == "bananaporridge"
    assert recipe["ages"] == ["around_6_months"]
    assert recipe["prep_time"] == "5 mins"
    assert recipe["cook_time"] == "10 mins"
    assert recipe["portions"] == "2"
    assert recipe["notes"] == "Soft tip"
    assert recipe["source"] == "Book"


def test_build_recipe_omits_blank_optional_fields():
    recipe = build_recipe(
        title="Plain Mash",
        ages=["around_6_months"],
        meal_types=["first_tastes"],
        ingredients_text="potato",
        steps_text="mash",
        prep_time="  ",
        cook_time="",
        portions=None,
    )
    assert recipe is not None
    assert "prep_time" not in recipe
    assert "cook_time" not in recipe
    assert "portions" not in recipe


def test_build_recipe_invalid_missing_ages():
    assert (
        build_recipe(
            title="Title",
            ages=[],
            meal_types=["breakfast"],
            ingredients_text="a",
            steps_text="b",
        )
        is None
    )


def test_add_recipe_appends(tmp_path: Path, sample_recipes):
    path = tmp_path / "recipes.json"
    save_recipes(path, sample_recipes[:1])
    add_recipe(path, sample_recipes[1])
    loaded = load_recipes(path)
    assert [r["id"] for r in loaded] == ["first-taste-veg", "banana-porridge"]
