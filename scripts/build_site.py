#!/usr/bin/env python3
"""Build a single-file offline web page from a validated plan.json.

Usage:
    python3 scripts/build_site.py path/to/plan.json [out_dir]

Writes out_dir/index.html (default: <plan dir>/site/). Images referenced by
dish.image are copied from <plan dir>/ into out_dir/ when they exist.
Runs validate_plan.py first and refuses to build if validation fails.
Standard library only.
"""
from __future__ import annotations

import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "templates" / "app.html"


def main(plan_path: str, out: str | None) -> int:
    plan_file = Path(plan_path).resolve()
    check = subprocess.run([sys.executable, str(HERE / "validate_plan.py"), str(plan_file)])
    if check.returncode != 0:
        print("校验未通过，已停止生成网页。先修正上面的错误。")
        return 1

    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    out_dir = Path(out).resolve() if out else plan_file.parent / "site"
    out_dir.mkdir(parents=True, exist_ok=True)

    missing = []
    for dish in plan["dishes"].values():
        rel = dish.get("image")
        if not rel:
            continue
        src = plan_file.parent / rel
        if src.exists():
            dst = out_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        else:
            missing.append(rel)
            dish.pop("image")

    # Embed JSON safely inside <script type="application/json">.
    data = json.dumps(plan, ensure_ascii=False).replace("</", "<\\/")
    page = TEMPLATE.read_text(encoding="utf-8")
    page = page.replace("__TITLE__", html.escape(plan["meta"]["title"]))
    page = page.replace("__PLAN_JSON__", data)
    (out_dir / "index.html").write_text(page, encoding="utf-8")

    print(f"已生成：{out_dir / 'index.html'}")
    if missing:
        print(f"  ⚠️  {len(missing)} 张成品图不存在，页面会显示占位：{missing[:5]}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None))
