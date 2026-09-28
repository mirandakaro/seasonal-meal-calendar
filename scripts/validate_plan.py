#!/usr/bin/env python3
"""Validate a seasonal meal plan JSON before building the web page.

Usage:
    python3 scripts/validate_plan.py path/to/plan.json

Exit code 0 = no errors (warnings may exist), 1 = errors found.
Standard library only.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

MEALS = ("breakfast", "lunch", "dinner")
MEAL_CN = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}
# Words that turn a step into something checkable: time, heat, or a doneness cue.
TIME_RE = re.compile(r"\d+\s*(秒|分钟|小时)|[一二三四五六七八九十两半]+\s*(秒|分钟|小时)")
HEAT_RE = re.compile(r"大火|中火|小火|中小火|中大火|五成热|六成热|℃|度|蒸|焖|烤箱|微波")
CUE_RE = re.compile(r"至|即|直到|看到|能|变|熟|软|透|开口|出香|收浓|不流动|无阻力")


def norm(name: str) -> str:
    """Normalize a dish name for duplicate detection."""
    name = re.sub(r"[（(].*?[)）]", "", name)
    name = re.sub(r"[\s·・,，、+＋]|版|改良|升级|第.+天", "", name)
    return name


def main(path: str) -> int:
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    errors: list[str] = []
    warns: list[str] = []

    meta, phases, dishes, days = plan["meta"], plan["phases"], plan["dishes"], plan["days"]
    total = meta["totalDays"]

    # 1. structure
    day_nums = [d["day"] for d in days]
    if day_nums != list(range(1, total + 1)):
        errors.append(f"天数不连续或数量不符：期望 1..{total}，实际 {day_nums[:5]}…（共 {len(day_nums)} 天）")
    for d in days:
        for m in MEALS:
            for did in d["meals"].get(m, []):
                if did not in dishes:
                    errors.append(f"第 {d['day']} 天{MEAL_CN[m]}引用了不存在的菜 id：{did}")
        feat = d.get("featured")
        if feat and not any(feat in d["meals"][m] for m in MEALS):
            errors.append(f"第 {d['day']} 天的 featured「{feat}」不在当天三餐里")

    # 2. recipe completeness
    for did, dish in dishes.items():
        if len(dish["steps"]) < 3:
            errors.append(f"「{dish['name']}」步骤少于 3 步")
        weak = [i + 1 for i, s in enumerate(dish["steps"])
                if not (TIME_RE.search(s) or HEAT_RE.search(s) or CUE_RE.search(s))]
        if len(weak) > len(dish["steps"]) // 2:
            warns.append(f"「{dish['name']}」第 {weak} 步缺少时长/火候/熟度提示，可能不够好照做")
        for ing in dish["ingredients"]:
            if ing["qty"] <= 0:
                errors.append(f"「{dish['name']}」的 {ing['item']} 用量为 0")

    # 3. exclusion scan: names, ingredients, steps, tips, summaries, meta copy
    blob_by_dish = {
        did: " ".join([dish["name"], dish.get("summary", ""), dish.get("tip", ""),
                       *[i["item"] for i in dish["ingredients"]], *dish["steps"]])
        for did, dish in dishes.items()
    }
    meta_blob = " ".join([meta.get("title", ""), meta.get("dailyExtras", ""),
                          *[p.get("note", "") for p in phases], *[d.get("flavor", "") for d in days]])
    for word in meta.get("exclusions", []):
        for did, blob in blob_by_dish.items():
            if word in blob:
                errors.append(f"忌口「{word}」出现在「{dishes[did]['name']}」里（含名称/食材/步骤/贴士）")
        if word in meta_blob:
            errors.append(f"忌口「{word}」出现在计划文案里")

    # 4. repetition audit
    menus = Counter(tuple(tuple(d["meals"][m]) for m in MEALS) for d in days)
    for menu, n in menus.items():
        if n > 1:
            errors.append(f"有 {n} 天的三餐组合完全相同")
    names = Counter(norm(d["name"]) for d in dishes.values())
    for n, c in names.items():
        if c > 1:
            errors.append(f"菜谱库里有 {c} 道菜名归一化后相同：{n}（换汤不换药也算重复）")
    for a, b in zip(days, days[1:]):
        mains_a = {x for m in ("lunch", "dinner") for x in a["meals"][m] if dishes[x].get("role") == "main"}
        mains_b = {x for m in ("lunch", "dinner") for x in b["meals"][m] if dishes[x].get("role") == "main"}
        same = mains_a & mains_b
        if same:
            warns.append(f"第 {a['day']}、{b['day']} 天连续吃同一道主菜：{[dishes[x]['name'] for x in same]}")
    used = {x for d in days for m in MEALS for x in d["meals"][m]}
    for did in set(dishes) - used:
        warns.append(f"菜谱库里的「{dishes[did]['name']}」没有被任何一天用到")

    # 5. phases & calendar
    covered = Counter()
    for p in phases:
        if p["fromDay"] > p["toDay"]:
            errors.append(f"阶段「{p['name']}」起止天颠倒")
        for i in range(p["fromDay"], p["toDay"] + 1):
            covered[i] += 1
    for i in range(1, total + 1):
        if covered[i] != 1:
            errors.append(f"第 {i} 天被 {covered[i]} 个阶段覆盖（应为 1 个）")
    start = date.fromisoformat(meta["startDate"])
    end = start + timedelta(days=total - 1)

    # 6. kcal summary
    per_day = []
    for d in days:
        k = sum(dishes[x]["kcalPerServing"] for m in MEALS for x in d["meals"][m])
        per_day.append(k)
        if k < 900 or k > 2600:
            warns.append(f"第 {d['day']} 天三餐估算 {k} 千卡/人，偏离常见范围，请复核")

    # report
    print(f"计划：{meta['title']}  ·  {total} 天  ·  {meta['servings']} 人份")
    print(f"日期：{start} → {end}（网页里可改开始日期）")
    print(f"菜谱库：{len(dishes)} 道  ·  实际用到 {len(used)} 道  ·  三餐共 {sum(len(d['meals'][m]) for d in days for m in MEALS)} 次")
    print(f"每日估算：{min(per_day)}–{max(per_day)} 千卡/人（不含加餐）")
    print(f"忌口：{meta.get('exclusions') or '无'}")
    for w in warns:
        print("  ⚠️ ", w)
    for e in errors:
        print("  ❌ ", e)
    print("结果：", "通过" if not errors else f"{len(errors)} 个错误", f"· {len(warns)} 个提醒")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
