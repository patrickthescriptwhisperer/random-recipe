# Random Recipe

A small Flask app that shows one random recipe from a local JSON list. Filter by age (including adult) and meal type. Designed to run in Docker on a homelab (Caddy/SWAG in front).

Recipe **content** is yours. This repository ships an empty recipe list plus an example file — do not commit recipes copied from books you do not have rights to redistribute.

## Usage

You can run from the published image or build locally. Copy `.env.example` to `.env` and set a real `SECRET_KEY` before production use.

### docker-compose (recommended)

```yaml
services:
  random-recipe:
    image: ghcr.io/patrickthescriptwhisperer/random-recipe:latest
    container_name: random-recipe
    environment:
      - PUID=1000
      - PGID=1000
      - SECRET_KEY=replace-with-a-long-random-string
      - ALLOW_PUBLIC_RECIPE_EDITS=false
    volumes:
      - /path/to/random-recipe/data:/app/data
    ports:
      - 8000:8000
    restart: unless-stopped
```

This repository’s `docker-compose.yml` is equivalent and also supports `build: .` for local images. After the first successful publish workflow run:

```bash
cp .env.example .env
# edit SECRET_KEY, PUID, PGID as needed
docker compose pull
docker compose up -d
```

Image name:

```text
ghcr.io/patrickthescriptwhisperer/random-recipe:latest
```

Packages are private by default on first push. To let others pull: GitHub → Packages → the image → Package settings → Change visibility → Public.

### docker cli

```bash
docker run -d \
  --name=random-recipe \
  -e PUID=1000 \
  -e PGID=1000 \
  -e SECRET_KEY=replace-with-a-long-random-string \
  -e ALLOW_PUBLIC_RECIPE_EDITS=false \
  -p 8000:8000 \
  -v /path/to/random-recipe/data:/app/data \
  --restart unless-stopped \
  ghcr.io/patrickthescriptwhisperer/random-recipe:latest
```

## Parameters

| Parameter | Function |
|-----------|----------|
| `-e PUID=1000` | User id for `/app/data` ownership — see below |
| `-e PGID=1000` | Group id for `/app/data` ownership — see below |
| `-e SECRET_KEY=` | Flask session key for flash messages (set a real value in production) |
| `-e ALLOW_PUBLIC_RECIPE_EDITS=false` | `true`/`1`/`yes`/`on` enables Add/Import for everyone. Default: `false` (readonly) |
| `-p 8000` | Application HTTP port |
| `-v /app/data` | Persistent recipe data (`recipes.json`; created as `[]` if missing) |

Optional compose `user: "${PUID}:${PGID}"` runs as that uid/gid directly and skips entrypoint remapping/chown — host ownership of the data folder must already allow writes. See the commented line in `docker-compose.yml`.

## User / group identifiers

When using volumes, permission mismatches between host and container are common. Set `PUID` and `PGID` to the owner of your host data folder.

The image starts as root, remaps `appuser` to those ids, chowns `/app/data`, then drops privileges.

```bash
id your_user
```

Example output:

```text
uid=1000(your_user) gid=1000(your_user) groups=1000(your_user)
```

In that case use `PUID=1000` and `PGID=1000`. On macOS these are often your `id -u` / `id -g`.

## Application setup

### Volume layout

| Container path | Purpose |
|----------------|---------|
| `/app/data/recipes.json` | Live recipe list (gitignored on the host bind mount; auto-created as `[]`) |
| `/app/data/recipes.example.json` | Example shape shipped in the image (optional reference) |

Bind-mount a host directory to `/app/data` (for example `/path/to/random-recipe/data:/app/data`). Edits to `recipes.json` on the host are picked up on the next page load (no rebuild).

### Adding recipes

With a mounted data directory you can:

1. **Add in the UI** — with `ALLOW_PUBLIC_RECIPE_EDITS=true`, use **Add a recipe** (multi-select ages and meal types; ingredients/steps one per line). The server derives an id from the title.
2. **Import in the UI** — with edits enabled, use **Import recipes** to upload a JSON array; it **replaces** the current file.
3. **Edit the file** — copy the shape from `recipes.example.json` into `recipes.json` on the host.

```json
{
  "id": "banana-porridge",
  "title": "Banana porridge",
  "ages": ["around_6_months", "7_to_9_months"],
  "meal_types": ["breakfast"],
  "prep_time": "5 mins",
  "cook_time": "10 mins",
  "portions": "2 portions",
  "ingredients": ["1 banana", "2 tbsp oats"],
  "steps": ["Cook oats", "Mash banana and stir in"],
  "notes": "Optional tip",
  "source": "My weaning book, p.42"
}
```

**Ages:** `around_6_months`, `7_to_9_months`, `10_to_12_months`, `12_months_or_older`, `adult`

**Meal types:** `breakfast`, `lunch`, `dinner`, `snack`, `finger_foods`, `first_tastes`

A recipe can list multiple ages and meal types. Invalid entries are skipped when the file is loaded. An import must be a JSON array; if the array has items but none are valid, the import is rejected and the existing file is left unchanged.

### Recipe editing access

Browse/filter from anywhere. **Add** and **Import** are **disabled by default** (readonly).

Set `ALLOW_PUBLIC_RECIPE_EDITS=true` only if you intentionally want visitors to change recipes. Prefer leaving it off on the public internet and editing `recipes.json` on the host instead.

**Warning:** enabling public edits lets anyone who can reach the app change your recipes.

### Reverse proxy example (Caddy)

```caddy
recipes.example.com {
  reverse_proxy random-recipe:8000
}
```

Prefer keeping port `8000` off the public internet and putting Caddy/SWAG in front.

## Quick start (build locally)

```bash
cp .env.example .env
docker compose up -d --build
```

Open [http://localhost:8000](http://localhost:8000).

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python app.py
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest --cov=app --cov=recipes --cov-report=term-missing --cov-fail-under=80
```

CI runs the same suite on pushes and pull requests to `main`.

## Keep screen awake

On supported mobile browsers, use **Keep screen awake** in the sticky top bar so the phone does not dim while you cook. The preference is remembered in the browser for the next visit. Requires a secure context (HTTPS or localhost).

The top bar also has **Dark mode** (on by default; preference saved in the browser), **New recipe**, **Add**, and **Import** when editing is enabled.

## Publishing images (GHCR)

GitHub Actions (`.github/workflows/publish.yml`) runs tests, then builds and pushes multi-arch images (`linux/amd64`, `linux/arm64`) to GHCR on:

- every push to `main` → `:latest` and a short SHA tag
- version tags like `v1.0.0` → semver tags

Publish is gated on the workflow’s test job. No extra secrets are required: the workflow uses `GITHUB_TOKEN` with `packages: write`.

## Health check

`GET /health` returns plain text `ok` (used by the Docker healthcheck).

## Security

See [SECURITY.md](SECURITY.md) for how to report vulnerabilities.

## License

MIT — see [LICENSE](LICENSE). Recipe text you add remains yours; only the application code is licensed here.
