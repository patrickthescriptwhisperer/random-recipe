"""Load, filter, and pick recipes from a local JSON file."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

AGES = (
    "around_6_months",
    "7_to_9_months",
    "10_to_12_months",
    "12_months_or_older",
    "adult",
)

MEAL_TYPES = (
    "breakfast",
    "lunch",
    "dinner",
    "snack",
    "finger_foods",
    "first_tastes",
)

AGE_LABELS = {
    "around_6_months": "Around 6 months",
    "7_to_9_months": "7 to 9 months",
    "10_to_12_months": "10 to 12 months",
    "12_months_or_older": "12 months or older",
    "adult": "Adult",
}

MEAL_TYPE_LABELS = {
    "breakfast": "Breakfast",
    "lunch": "Lunch",
    "dinner": "Dinner",
    "snack": "Snack",
    "finger_foods": "Finger foods",
    "first_tastes": "First tastes",
}

REQUIRED_FIELDS = ("id", "title", "ages", "meal_types", "ingredients", "steps")


def is_valid_recipe(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    for field in REQUIRED_FIELDS:
        if field not in entry:
            return False
    if not isinstance(entry["id"], str) or not entry["id"].strip():
        return False
    if not isinstance(entry["title"], str) or not entry["title"].strip():
        return False
    if not isinstance(entry["ages"], list) or not entry["ages"]:
        return False
    if not isinstance(entry["meal_types"], list) or not entry["meal_types"]:
        return False
    if not isinstance(entry["ingredients"], list) or not entry["ingredients"]:
        return False
    if not isinstance(entry["steps"], list) or not entry["steps"]:
        return False
    if not all(age in AGES for age in entry["ages"]):
        return False
    if not all(meal in MEAL_TYPES for meal in entry["meal_types"]):
        return False
    return True


def lines_to_list(text: str | None) -> list[str]:
    """Split textarea input into non-empty trimmed lines."""
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def id_from_title(title: str | None) -> str:
    """Lowercase title with spaces removed (e.g. 'Banana porridge' -> 'bananaporridge')."""
    return "".join((title or "").lower().split())


def _optional_text(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def build_recipe(
    *,
    title: str | None,
    ages: list[str] | None,
    meal_types: list[str] | None,
    ingredients_text: str | None,
    steps_text: str | None,
    prep_time: str | None = None,
    cook_time: str | None = None,
    portions: str | None = None,
    notes: str | None = None,
    source: str | None = None,
) -> dict[str, Any] | None:
    """Build a recipe dict from form fields. Id is derived from title. Returns None if invalid."""
    title_clean = (title or "").strip()
    recipe: dict[str, Any] = {
        "id": id_from_title(title_clean),
        "title": title_clean,
        "ages": [a for a in (ages or []) if a in AGES],
        "meal_types": [m for m in (meal_types or []) if m in MEAL_TYPES],
        "ingredients": lines_to_list(ingredients_text),
        "steps": lines_to_list(steps_text),
    }
    for key, value in (
        ("prep_time", prep_time),
        ("cook_time", cook_time),
        ("portions", portions),
        ("notes", notes),
        ("source", source),
    ):
        cleaned = _optional_text(value)
        if cleaned is not None:
            recipe[key] = cleaned
    if not is_valid_recipe(recipe):
        return None
    return recipe


def load_recipes(path: Path | str) -> list[dict[str, Any]]:
    """Load recipes from JSON. Missing/malformed files yield []. Invalid entries are skipped."""
    file_path = Path(path)
    if not file_path.is_file():
        return []
    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    return parse_recipes_list(raw)


def parse_recipes_list(raw: Any) -> list[dict[str, Any]]:
    """Return valid recipes from a decoded JSON value. Non-lists yield []."""
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if is_valid_recipe(entry)]


def save_recipes(path: Path | str, recipes: list[dict[str, Any]]) -> None:
    """Overwrite the recipes JSON file with the given list."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(recipes, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def add_recipe(path: Path | str, recipe: dict[str, Any]) -> None:
    """Append a recipe to the file (overwrites the file with the extended list)."""
    recipes = load_recipes(path)
    recipes.append(recipe)
    save_recipes(path, recipes)


def filter_recipes(
    recipes: list[dict[str, Any]],
    *,
    age: str | None = None,
    meal_type: str | None = None,
) -> list[dict[str, Any]]:
    """Filter by age and/or meal type. Unknown values yield no matches."""
    age_filter = age.strip() if isinstance(age, str) and age.strip() else None
    meal_filter = (
        meal_type.strip() if isinstance(meal_type, str) and meal_type.strip() else None
    )

    if age_filter is not None and age_filter not in AGES:
        return []
    if meal_filter is not None and meal_filter not in MEAL_TYPES:
        return []

    matched = recipes
    if age_filter is not None:
        matched = [r for r in matched if age_filter in r.get("ages", [])]
    if meal_filter is not None:
        matched = [r for r in matched if meal_filter in r.get("meal_types", [])]
    return matched


def pick_random(
    recipes: list[dict[str, Any]],
    *,
    exclude_id: str | None = None,
    rng: random.Random | None = None,
) -> dict[str, Any] | None:
    """Pick a random recipe, avoiding exclude_id when at least two candidates exist."""
    if not recipes:
        return None

    chooser = rng.choice if rng is not None else random.choice
    candidates = recipes
    if exclude_id and len(recipes) >= 2:
        without = [r for r in recipes if r.get("id") != exclude_id]
        if without:
            candidates = without
    return chooser(candidates)
