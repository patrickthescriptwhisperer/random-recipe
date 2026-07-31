"""Random Recipe — single-page random recipe picker."""

from __future__ import annotations

import json
import os
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from recipes import (
    AGE_LABELS,
    AGES,
    MEAL_TYPE_LABELS,
    MEAL_TYPES,
    add_recipe,
    build_recipe,
    filter_recipes,
    load_recipes,
    parse_recipes_list,
    pick_random,
    save_recipes,
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RECIPES_PATH = BASE_DIR / "data" / "recipes.json"
MAX_UPLOAD_BYTES = 1 * 1024 * 1024


def _env_flag(name: str, default: bool = False) -> bool:
    """Parse a truthy env flag (1/true/yes/on). Missing var uses default."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


app = Flask(__name__)
app.config["RECIPES_PATH"] = DEFAULT_RECIPES_PATH
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "random-recipe-local-dev")
app.config["ALLOW_PUBLIC_RECIPE_EDITS"] = _env_flag("ALLOW_PUBLIC_RECIPE_EDITS", False)


def _normalize_filter(value: str | None, allowed: tuple[str, ...]) -> str | None:
    if not value or not value.strip():
        return None
    cleaned = value.strip()
    if cleaned not in allowed:
        return None
    return cleaned


def _can_edit() -> bool:
    return bool(app.config["ALLOW_PUBLIC_RECIPE_EDITS"])


def edits_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not _can_edit():
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def _render_index():
    recipes_path = Path(app.config["RECIPES_PATH"])
    all_recipes = load_recipes(recipes_path)

    age = _normalize_filter(request.args.get("age"), AGES)
    meal_type = _normalize_filter(request.args.get("meal_type"), MEAL_TYPES)
    exclude_id = request.args.get("exclude") or None

    matched = filter_recipes(all_recipes, age=age, meal_type=meal_type)
    recipe = pick_random(matched, exclude_id=exclude_id)

    empty_reason = None
    if not all_recipes:
        empty_reason = "no_data"
    elif not matched:
        empty_reason = "no_match"

    return render_template(
        "index.html",
        recipe=recipe,
        empty_reason=empty_reason,
        age=age or "",
        meal_type=meal_type or "",
        ages=AGES,
        meal_types=MEAL_TYPES,
        age_labels=AGE_LABELS,
        meal_type_labels=MEAL_TYPE_LABELS,
        match_count=len(matched),
        recipe_count=len(all_recipes),
        can_edit=_can_edit(),
    )


@app.get("/health")
def health():
    return "ok", 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/")
def index():
    return _render_index()


@app.post("/import")
@edits_required
def import_recipes():
    upload = request.files.get("recipes_file")
    if upload is None or not upload.filename:
        flash("Choose a JSON file to import.", "error")
        return redirect(url_for("index", _anchor="import"))

    try:
        raw_text = upload.read().decode("utf-8")
        raw = json.loads(raw_text)
    except UnicodeDecodeError:
        flash("Import failed: file must be UTF-8 text.", "error")
        return redirect(url_for("index", _anchor="import"))
    except json.JSONDecodeError:
        flash("Import failed: file is not valid JSON.", "error")
        return redirect(url_for("index", _anchor="import"))

    if not isinstance(raw, list):
        flash("Import failed: JSON must be an array of recipes.", "error")
        return redirect(url_for("index", _anchor="import"))

    recipes = parse_recipes_list(raw)
    if raw and not recipes:
        flash("Import failed: no valid recipes found in the file.", "error")
        return redirect(url_for("index", _anchor="import"))

    try:
        save_recipes(Path(app.config["RECIPES_PATH"]), recipes)
    except OSError:
        flash(
            "Import failed: could not write recipes file. "
            "Check that PUID/PGID match the owner of ./data.",
            "error",
        )
        return redirect(url_for("index", _anchor="import"))

    if recipes:
        flash(
            f"Imported {len(recipes)} recipe{'s' if len(recipes) != 1 else ''} "
            "(replaced the previous list).",
            "success",
        )
    else:
        flash("Imported an empty list (previous recipes were replaced).", "success")
    return redirect(url_for("index"))


@app.post("/recipes")
@edits_required
def create_recipe():
    recipe = build_recipe(
        title=request.form.get("title"),
        ages=request.form.getlist("ages"),
        meal_types=request.form.getlist("meal_types"),
        ingredients_text=request.form.get("ingredients"),
        steps_text=request.form.get("steps"),
        prep_time=request.form.get("prep_time"),
        cook_time=request.form.get("cook_time"),
        portions=request.form.get("portions"),
        notes=request.form.get("notes"),
        source=request.form.get("source"),
    )
    if recipe is None:
        flash(
            "Could not add recipe. Check title, ages, meal types, "
            "and at least one ingredient and step (one per line).",
            "error",
        )
        return redirect(url_for("index", _anchor="add-recipe"))

    recipes_path = Path(app.config["RECIPES_PATH"])
    existing = load_recipes(recipes_path)
    if any(r.get("id") == recipe["id"] for r in existing):
        flash(f'A recipe with id "{recipe["id"]}" already exists.', "error")
        return redirect(url_for("index", _anchor="add-recipe"))

    try:
        add_recipe(recipes_path, recipe)
    except OSError:
        flash(
            "Could not save recipe. "
            "Check that PUID/PGID match the owner of ./data.",
            "error",
        )
        return redirect(url_for("index", _anchor="add-recipe"))

    flash(f'Added “{recipe["title"]}”.', "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
