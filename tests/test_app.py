"""Flask route integration tests."""

from __future__ import annotations

import io
import json
from pathlib import Path

from app import app as flask_app


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.data == b"ok"


def test_index_with_recipes(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Random Recipe" in html
    assert "Ingredients" in html
    assert "Steps" in html


def test_index_empty_data(empty_client):
    response = empty_client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "No recipes yet" in html
    assert "data/recipes.json" in html


def test_index_no_match_filters(client):
    response = client.get("/?age=around_6_months&meal_type=dinner")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "No recipes match" in html


def test_index_age_filter(client):
    response = client.get("/?age=around_6_months")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Around 6 months" in html
    assert "No recipes match" not in html
    assert 'value="adult"' in html
    assert ">Adult<" in html


def test_index_adult_filter(client):
    response = client.get("/?age=adult")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Adult pasta" in html
    assert "Adult" in html


def test_index_meal_filter(client):
    response = client.get("/?meal_type=breakfast")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Banana porridge" in html


def test_index_unknown_filters_treated_as_any(client):
    response = client.get("/?age=toddler&meal_type=brunch")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "No recipes yet" not in html
    assert "Ingredients" in html


def test_another_recipe_excludes_current(client):
    first = client.get("/?meal_type=dinner")
    assert first.status_code == 200
    html = first.get_data(as_text=True)
    assert 'name="exclude"' in html
    assert "New recipe" in html

    response = client.get("/?meal_type=dinner&exclude=lentil-lunch")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Lentil mash" not in html
    assert "Mild veg curry" in html or "Adult pasta" in html


def test_top_bar_controls(client):
    response = client.get("/")
    html = response.get_data(as_text=True)
    assert 'class="top-bar"' in html
    assert "Keep screen awake" in html
    assert "Dark mode" in html
    assert 'id="dark-mode"' in html
    assert 'data-theme="dark"' in html
    assert "New recipe" in html
    assert 'form="filters"' in html
    assert 'href="#add-recipe"' in html
    assert 'href="#import"' in html
    assert 'id="add-recipe"' in html
    assert 'id="import"' in html
    assert html.count("<details") >= 2
    assert "Add a recipe" in html
    assert "Import recipes" in html
    assert '<details class="form-panel" id="add-recipe">' in html
    assert '<details class="import-panel" id="import">' in html
    assert "import.js" in html
    assert "recipe-id.js" not in html


def test_index_uses_configured_recipes_path(tmp_path: Path, sample_recipes):
    path = tmp_path / "only.json"
    path.write_text(json.dumps([sample_recipes[0]]), encoding="utf-8")
    flask_app.config["RECIPES_PATH"] = path
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        response = test_client.get("/")
    assert response.status_code == 200
    assert "Steamed carrot" in response.get_data(as_text=True)


def test_import_overwrites_existing_file(client, recipes_file: Path, sample_recipes):
    payload = [sample_recipes[0]]
    data = {
        "recipes_file": (
            io.BytesIO(json.dumps(payload).encode("utf-8")),
            "recipes.json",
        )
    }
    response = client.post("/import", data=data, content_type="multipart/form-data")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

    saved = json.loads(recipes_file.read_text(encoding="utf-8"))
    assert len(saved) == 1
    assert saved[0]["id"] == "first-taste-veg"

    follow = client.get("/")
    html = follow.get_data(as_text=True)
    assert "Imported 1 recipe" in html
    assert "Steamed carrot" in html


def test_import_empty_array_clears_recipes(client, recipes_file: Path):
    data = {
        "recipes_file": (io.BytesIO(b"[]"), "empty.json")
    }
    response = client.post("/import", data=data, content_type="multipart/form-data")
    assert response.status_code == 302
    assert json.loads(recipes_file.read_text(encoding="utf-8")) == []

    follow = client.get("/")
    assert "No recipes yet" in follow.get_data(as_text=True)
    assert "empty list" in follow.get_data(as_text=True)


def test_import_rejects_missing_file(client, recipes_file: Path, sample_recipes):
    before = recipes_file.read_text(encoding="utf-8")
    response = client.post("/import", data={}, content_type="multipart/form-data")
    assert response.status_code == 302
    assert recipes_file.read_text(encoding="utf-8") == before

    follow = client.get("/")
    assert "Choose a JSON file" in follow.get_data(as_text=True)


def test_import_rejects_invalid_json(client, recipes_file: Path):
    before = recipes_file.read_text(encoding="utf-8")
    data = {
        "recipes_file": (io.BytesIO(b"{not-json"), "bad.json")
    }
    response = client.post("/import", data=data, content_type="multipart/form-data")
    assert response.status_code == 302
    assert recipes_file.read_text(encoding="utf-8") == before

    follow = client.get("/")
    assert "not valid JSON" in follow.get_data(as_text=True)


def test_import_rejects_non_utf8(client, recipes_file: Path):
    before = recipes_file.read_text(encoding="utf-8")
    data = {
        "recipes_file": (io.BytesIO(b"\xff\xfe[]"), "binary.json")
    }
    response = client.post("/import", data=data, content_type="multipart/form-data")
    assert response.status_code == 302
    assert recipes_file.read_text(encoding="utf-8") == before

    follow = client.get("/")
    assert "UTF-8" in follow.get_data(as_text=True)


def test_import_rejects_non_array(client, recipes_file: Path):
    before = recipes_file.read_text(encoding="utf-8")
    data = {
        "recipes_file": (io.BytesIO(b'{"title": "nope"}'), "obj.json")
    }
    response = client.post("/import", data=data, content_type="multipart/form-data")
    assert response.status_code == 302
    assert recipes_file.read_text(encoding="utf-8") == before

    follow = client.get("/")
    assert "array of recipes" in follow.get_data(as_text=True)


def test_import_rejects_all_invalid_recipes(client, recipes_file: Path):
    before = recipes_file.read_text(encoding="utf-8")
    data = {
        "recipes_file": (
            io.BytesIO(b'[{"id": "x", "title": "Incomplete"}]'),
            "bad-recipes.json",
        )
    }
    response = client.post("/import", data=data, content_type="multipart/form-data")
    assert response.status_code == 302
    assert recipes_file.read_text(encoding="utf-8") == before

    follow = client.get("/")
    assert "no valid recipes" in follow.get_data(as_text=True)


def test_import_skips_invalid_keeps_valid(client, recipes_file: Path, sample_recipes):
    payload = [sample_recipes[1], {"id": "broken", "title": "Nope"}]
    data = {
        "recipes_file": (
            io.BytesIO(json.dumps(payload).encode("utf-8")),
            "mixed.json",
        )
    }
    response = client.post("/import", data=data, content_type="multipart/form-data")
    assert response.status_code == 302
    saved = json.loads(recipes_file.read_text(encoding="utf-8"))
    assert [r["id"] for r in saved] == ["banana-porridge"]


def test_create_recipe_appends(client, recipes_file: Path):
    response = client.post(
        "/recipes",
        data={
            "title": "New mash",
            "ages": ["around_6_months"],
            "meal_types": ["first_tastes", "lunch"],
            "prep_time": "5 mins",
            "cook_time": "15 mins",
            "portions": "4",
            "ingredients": "1 potato\nA little water",
            "steps": "Steam potato\nMash until soft",
            "notes": "Simple starter",
            "source": "Kitchen notes",
        },
    )
    assert response.status_code == 302
    saved = json.loads(recipes_file.read_text(encoding="utf-8"))
    assert saved[-1]["id"] == "newmash"
    assert saved[-1]["title"] == "New mash"
    assert saved[-1]["prep_time"] == "5 mins"
    assert saved[-1]["cook_time"] == "15 mins"
    assert saved[-1]["portions"] == "4"
    assert saved[-1]["meal_types"] == ["first_tastes", "lunch"]
    assert saved[-1]["ingredients"] == ["1 potato", "A little water"]

    follow = client.get("/")
    html = follow.get_data(as_text=True)
    assert "Added “New mash”" in html


def test_index_shows_timing_fields(client):
    response = client.get("/?meal_type=breakfast")
    html = response.get_data(as_text=True)
    assert "Prep" in html
    assert "5 mins" in html
    assert "Cook" in html
    assert "Portions" in html


def test_create_recipe_rejects_invalid(client, recipes_file: Path):
    before = recipes_file.read_text(encoding="utf-8")
    response = client.post(
        "/recipes",
        data={
            "title": "Incomplete",
            "ingredients": "only ingredient",
            "steps": "only step",
        },
    )
    assert response.status_code == 302
    assert recipes_file.read_text(encoding="utf-8") == before
    follow = client.get("/")
    assert "Could not add recipe" in follow.get_data(as_text=True)


def test_create_recipe_rejects_duplicate_id(client, recipes_file: Path):
    first = client.post(
        "/recipes",
        data={
            "title": "Unique Soup",
            "ages": ["around_6_months"],
            "meal_types": ["lunch"],
            "ingredients": "x",
            "steps": "y",
        },
    )
    assert first.status_code == 302
    before_count = len(json.loads(recipes_file.read_text(encoding="utf-8")))

    response = client.post(
        "/recipes",
        data={
            "title": "Unique Soup",
            "ages": ["around_6_months"],
            "meal_types": ["lunch"],
            "ingredients": "x",
            "steps": "y",
        },
    )
    assert response.status_code == 302
    saved = json.loads(recipes_file.read_text(encoding="utf-8"))
    assert len(saved) == before_count
    follow = client.get("/")
    assert "already exists" in follow.get_data(as_text=True)


def test_create_recipe_ignores_posted_id(client, recipes_file: Path):
    response = client.post(
        "/recipes",
        data={
            "id": "forged-id",
            "title": "Forged Title",
            "ages": ["around_6_months"],
            "meal_types": ["snack"],
            "ingredients": "x",
            "steps": "y",
        },
    )
    assert response.status_code == 302
    saved = json.loads(recipes_file.read_text(encoding="utf-8"))
    assert saved[-1]["id"] == "forgedtitle"


def test_readonly_default_blocks_create_and_import(readonly_client, recipes_file: Path):
    before = recipes_file.read_text(encoding="utf-8")
    create = readonly_client.post(
        "/recipes",
        data={
            "title": "Blocked",
            "ages": ["adult"],
            "meal_types": ["dinner"],
            "ingredients": "x",
            "steps": "y",
        },
    )
    assert create.status_code == 403

    import_response = readonly_client.post(
        "/import",
        data={"recipes_file": (io.BytesIO(b"[]"), "empty.json")},
        content_type="multipart/form-data",
    )
    assert import_response.status_code == 403
    assert recipes_file.read_text(encoding="utf-8") == before


def test_readonly_hides_edit_ui(readonly_client):
    response = readonly_client.get("/")
    html = response.get_data(as_text=True)
    assert "New recipe" in html
    assert 'href="#add-recipe"' not in html
    assert 'href="#import"' not in html
    assert 'id="add-recipe"' not in html
    assert "import.js" not in html


def test_public_edits_flag_allows_create(client, recipes_file: Path):
    response = client.post(
        "/recipes",
        data={
            "title": "Public Soup",
            "ages": ["adult"],
            "meal_types": ["lunch"],
            "ingredients": "stock",
            "steps": "simmer",
        },
    )
    assert response.status_code == 302
    saved = json.loads(recipes_file.read_text(encoding="utf-8"))
    assert saved[-1]["id"] == "publicsoup"


def test_import_write_failure_flashes_error(client, recipes_file: Path, monkeypatch):
    def boom(*_args, **_kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr("app.save_recipes", boom)
    response = client.post(
        "/import",
        data={
            "recipes_file": (io.BytesIO(b"[]"), "empty.json"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 302
    follow = client.get("/")
    assert "could not write recipes file" in follow.get_data(as_text=True)


def test_create_write_failure_flashes_error(client, recipes_file: Path, monkeypatch):
    def boom(*_args, **_kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr("app.add_recipe", boom)
    response = client.post(
        "/recipes",
        data={
            "title": "No Write",
            "ages": ["adult"],
            "meal_types": ["dinner"],
            "ingredients": "x",
            "steps": "y",
        },
    )
    assert response.status_code == 302
    follow = client.get("/")
    assert "Could not save recipe" in follow.get_data(as_text=True)
