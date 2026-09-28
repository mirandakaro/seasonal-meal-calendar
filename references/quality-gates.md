# Meal-plan quality gates

Run these gates before saying a multi-day plan is complete.

## 1. Structural integrity

- Expected day count matches actual day count.
- Every day has the promised meal slots.
- Every meal has at least one dish and an estimated energy range if calories are promised.
- Every dish record has non-empty name, ingredients, and steps.
- Step numbering is parseable by cooking mode.

Recommended assertions:

```text
len(days) == promised_days
all(meal_types(day) == expected_meals for day in days)
all(dish.ingredients and dish.steps for every dish)
```

## 2. Exclusion scan

Build a normalized forbidden-term list including synonyms and substrings. Search:

- dish names
- ingredient records
- recipe steps
- shopping-list source data
- hero/stat copy

Do not accept a label such as “cilantro replacement” because it still contains and surfaces the excluded term.

## 3. Repetition audit

Check at three levels:

1. Exact meal-menu duplicates.
2. Normalized dish-name duplicates (remove punctuation, serving-size suffixes, decorative flavor labels, and day numbers).
3. Semantic duplicates: same principal ingredients and same technique with only cosmetic renaming.

Report all three counts. “Unique strings” alone is not proof of menu variety.

Substantive variation should change at least two dimensions among:

- principal ingredient
- cooking technique
- flavor base
- vegetable pairing
- texture/form

## 4. Recipe-to-name alignment

For every dish, verify named elements appear in ingredients and steps. Flag cases such as:

- “steamed tofu” with stir-fry instructions
- “fish soup” with dry-pan instructions
- “chicken breast stir-fry” with long boiling
- “cold dressed vegetable” with hot-oil frying unless explicitly intended

Each recipe must include quantities, preparation, heat, time, order, and doneness cue.

## 5. Palatability checks

- Lean meat has a moisture-preserving treatment.
- Fish has odor-control and overcooking prevention.
- Watery vegetables account for drainage and heat.
- Soups distinguish ingredients that need long cooking from proteins added near the end.
- Low-oil does not mean flavorless: use aromatics, acidity, mushrooms, tomato, citrus, herbs, or light fermented seasoning as appropriate.

## 6. Calendar checks

After choosing the start date:

- Day 1 equals the selected date.
- Day N equals start date plus N−1 days.
- Phase labels and phase date ranges use the same offsets.
- Month/year rollover is correct.
- Refresh preserves the selected start date.
- UI shows both plan day and calendar date.

Test at least one ordinary date, one month-end date, and one year-end date.

## 7. Shopping-list checks

- Derive items from ingredient records, not dish names.
- Aggregate compatible units.
- Preserve separate quantities when units cannot be safely combined.
- Respect the selected day range.
- Excluded ingredients yield zero hits.

## 8. Browser checks

Exercise with Playwright or an equivalent browser tool:

- load and console/page errors
- date picker change
- previous/next day
- phase boundary navigation
- recipe detail opening
- cooking-mode next/previous/close
- search/filter
- shopping ranges and checkboxes
- mobile and desktop screenshots

A successful syntax check is necessary but not sufficient. A rendered shell with empty panels is a failure.

## 9. Honest completion language

Separate these claims:

- mechanically generated
- machine-validated
- browser-tested
- individually reviewed for culinary accuracy
- nutritionally estimated
- medically reviewed

Never collapse them into “fully verified.”
