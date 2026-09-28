---
name: seasonal-meal-calendar
description: Use when a user wants a multi-day seasonal meal plan as a web page (季候编辑部 / 三伏食历 / 节气食谱 / 7–60 天家常菜单). Generates a validated plan.json, then builds an offline mobile-first page with calendar, recipes, cook mode, shopping list, favorites and meal log.
license: MIT
compatibility: Needs filesystem access and Python 3.9+ (standard library only). A browser automation tool is recommended for QA. An image model is optional for dish photos.
---

# Seasonal Meal Calendar · 季候编辑部

Turn "给家里做个三伏 40 天的食谱" into a real page family members can open on a phone: today's three meals, exact recipes, a cook-along mode, a shopping card for the next 1/3/7 days, favorites, and a meal log.

Two deliverables, always in this order:

1. `plan.json` — the data, validated by `scripts/validate_plan.py`.
2. `site/index.html` — one offline file built by `scripts/build_site.py` from `templates/app.html`.

Never hand-write the HTML page. Change the data, then rebuild.

## Workflow

### 1. Collect constraints (ask before generating)

- Season or occasion, number of days, start date, servings.
- Exclusions (dislikes, allergies) — these become a zero-tolerance list.
- Health notes (e.g. low fat, low salt). Treat them as general home-cooking guidance, not medical advice.
- Cooking reality: who cooks, time per meal, equipment, regional taste.
- Photos wanted? (generate with an image model, use the user's own, or keep the built-in color placeholders).

If the user gives only part of this, propose sensible defaults and confirm in one short message.

### 2. Design the phase calendar

Split the plan into phases (`phases[]`), e.g. 初伏 / 中伏 / 末伏, or 立秋 / 处暑. Every day must belong to exactly one phase. Give each day a `flavor` so the week feels varied.

### 3. Build the dish library first, then the days

- Write each dish once in `dishes{}` with its own ingredients (numeric qty + unit) and 3–6 specific steps.
- Every step that cooks something needs time, heat, or a doneness cue ("中火 3 分钟至变白", "筷子能轻松戳穿").
- A dish name maps to its own method. Never paste a generic "stir-fry" paragraph under unrelated dishes.
- Mark pantry items `"shop": false` (salt, oil, water) so they stay off the shopping card.
- Then fill `days[]`, referencing dish ids. Rotate proteins, vegetables, methods and flavors. Staples may repeat; mains must not repeat on consecutive days.

Schema: `templates/plan.schema.json`. Worked example: `examples/liqiu-3days/plan.json`.

### 4. Validate

```bash
python3 scripts/validate_plan.py plan.json
```

It checks day count, meal slots, broken dish ids, exclusion hits in names/ingredients/steps/tips, phase coverage, exact-menu duplicates, consecutive-day main repeats, vague steps, and daily kcal range. Fix every ❌ before moving on. Read every ⚠️ and fix or justify it.

Also run the manual gates in `references/quality-gates.md` (culinary sanity, tenderness technique for lean proteins, honest completion language).

### 5. Photos (optional)

Put images next to plan.json and set `dish.image` to the relative path. Missing images fall back to designed color placeholders, so the page never shows broken images. Generated photos must match the dish actually described in the recipe.

### 6. Build and QA

```bash
python3 scripts/build_site.py plan.json          # → site/index.html
```

Open the page on a ~430px mobile viewport and a desktop viewport and actually exercise: previous/next day, changing the start date (check month/year rollover), opening a recipe, cook mode next/previous/close, favorite, meal check-in, search, shopping range 1/3/7 days, and the four tabs. Check the console for errors. An empty panel is a failure even if the build succeeded.

### 7. Deliver

- Give the user the `index.html` path and a phone screenshot.
- For family sharing, suggest a static host they control. Favorites, check-ins and the start date live in each device's localStorage; nothing is uploaded.
- Report separately: generated, machine-validated, browser-tested, and what was NOT reviewed (e.g. calories are estimates; not reviewed by a dietitian).

## Hard rules

- Exclusions are global: zero hits in names, ingredients, steps, tips and shopping list. "香菜替代" still counts as a hit.
- Do not invent medical benefits. Add the built-in disclaimer and keep it.
- Do not publish the user's personal plan, family details or private site address unless they explicitly ask.

## Files

- `templates/plan.schema.json` — data contract.
- `templates/app.html` — page template (edit styles here, not in the built file).
- `scripts/validate_plan.py`, `scripts/build_site.py` — standard-library Python.
- `references/quality-gates.md` — full checklist.
- `examples/liqiu-3days/` — fictional 3-day example and its built page.
- `evals/evals.json` — behavior tests for a new agent install.
