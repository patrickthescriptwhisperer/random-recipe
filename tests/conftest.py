"""Shared fixtures for recipe and Flask tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import app as flask_app


SAMPLE_RECIPES = [
    {
        "id": "first-taste-veg",
        "title": "Steamed carrot",
        "ages": ["around_6_months"],
        "meal_types": ["first_tastes"],
        "ingredients": ["1 carrot"],
        "steps": ["Steam until soft", "Mash or serve as soft sticks"],
        "notes": "Simple first taste",
        "source": "Test fixture",
    },
    {
        "id": "banana-porridge",
        "title": "Banana porridge",
        "ages": ["around_6_months", "7_to_9_months"],
        "meal_types": ["breakfast"],
        "ingredients": ["1 banana", "2 tbsp oats"],
        "steps": ["Cook oats", "Mash banana and stir in"],
        "prep_time": "5 mins",
        "cook_time": "10 mins",
        "portions": "2",
        "source": "Test fixture",
    },
    {
        "id": "lentil-lunch",
        "title": "Lentil mash",
        "ages": ["7_to_9_months", "10_to_12_months"],
        "meal_types": ["lunch", "dinner"],
        "ingredients": ["50g red lentils", "1 carrot"],
        "steps": ["Simmer lentils", "Mash with cooked carrot"],
    },
    {
        "id": "finger-toast",
        "title": "Toast fingers",
        "ages": ["10_to_12_months", "12_months_or_older"],
        "meal_types": ["finger_foods", "snack"],
        "ingredients": ["1 slice bread"],
        "steps": ["Toast lightly", "Cut into fingers"],
    },
    {
        "id": "dinner-curry",
        "title": "Mild veg curry",
        "ages": ["12_months_or_older"],
        "meal_types": ["dinner"],
        "ingredients": ["Sweet potato", "Chickpeas"],
        "steps": ["Simmer until soft", "Mash lightly for younger eaters"],
        "notes": "No added salt",
    },
    {
        "id": "adult-pasta",
        "title": "Adult pasta",
        "ages": ["adult"],
        "meal_types": ["dinner"],
        "ingredients": ["200g pasta", "Tomato sauce"],
        "steps": ["Cook pasta", "Warm sauce and combine"],
        "prep_time": "5 mins",
        "cook_time": "12 mins",
        "portions": "2",
    },
]


@pytest.fixture
def sample_recipes():
    return [dict(recipe) for recipe in SAMPLE_RECIPES]


@pytest.fixture
def recipes_file(tmp_path: Path, sample_recipes):
    path = tmp_path / "recipes.json"
    path.write_text(json.dumps(sample_recipes), encoding="utf-8")
    return path


@pytest.fixture
def empty_recipes_file(tmp_path: Path):
    path = tmp_path / "recipes.json"
    path.write_text("[]", encoding="utf-8")
    return path


@pytest.fixture
def client(recipes_file: Path):
    flask_app.config["RECIPES_PATH"] = recipes_file
    flask_app.config["TESTING"] = True
    flask_app.config["ALLOW_PUBLIC_RECIPE_EDITS"] = True
    with flask_app.test_client() as test_client:
        yield test_client


@pytest.fixture
def empty_client(empty_recipes_file: Path):
    flask_app.config["RECIPES_PATH"] = empty_recipes_file
    flask_app.config["TESTING"] = True
    flask_app.config["ALLOW_PUBLIC_RECIPE_EDITS"] = True
    with flask_app.test_client() as test_client:
        yield test_client


@pytest.fixture
def readonly_client(recipes_file: Path):
    flask_app.config["RECIPES_PATH"] = recipes_file
    flask_app.config["TESTING"] = True
    flask_app.config["ALLOW_PUBLIC_RECIPE_EDITS"] = False
    with flask_app.test_client() as test_client:
        yield test_client
