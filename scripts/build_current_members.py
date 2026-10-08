"""Populate the "Current members" section of docs/team.html.

Reads docs/lab_members/current/<Last_First>/ (one .txt with Role, Years,
Description fields and one .jpg/.jpeg image) and rewrites the block between
the CURRENT-MEMBERS markers in team.html.

Usage: python scripts/build_current_members.py
"""

import html
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
CURRENT_DIR = DOCS / "lab_members" / "current"
TEAM_PAGE = DOCS / "team.html"

ROLE_ORDER = [
    "Visiting scientist",
    "Lab technician",
    "Post-doc",
    "Ph.D. student",
    "M.S. student",
    "Undergraduate researcher",
]
FIELD_RE = re.compile(r"^(Role|Years|Description)\s*:\s*(.*)$", re.IGNORECASE)
BLOCK_RE = re.compile(
    r"(<!-- CURRENT-MEMBERS-START -->).*?(<!-- CURRENT-MEMBERS-END -->)",
    re.DOTALL,
)


def parse_txt(path):
    """Parse 'Field: value' lines; a field continues until the next field."""
    fields, current = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = FIELD_RE.match(line.strip())
        if match:
            current = match.group(1).capitalize()
            fields[current] = match.group(2).strip()
        elif current and line.strip():
            fields[current] += " " + line.strip()
    return fields


def role_rank(role):
    role = role.strip().lower()
    for i, name in enumerate(ROLE_ORDER):
        if name.lower() == role:
            return i
    return len(ROLE_ORDER)


def year_value(years):
    found = re.findall(r"\d{4}", years)
    return max(int(y) for y in found) if found else 0


def load_members():
    members = []
    for folder in sorted(p for p in CURRENT_DIR.iterdir() if p.is_dir()):
        txts = list(folder.glob("*.txt"))
        imgs = [p for p in folder.iterdir() if p.suffix.lower() in (".jpg", ".jpeg")]
        if not txts:
            print(f"Skipping {folder.name}: no .txt file")
            continue
        info = parse_txt(txts[0])
        last, _, first = folder.name.partition("_")
        members.append(
            {
                "name": f"{first.replace('_', ' ')} {last}".strip(),
                "role": info.get("Role", ""),
                "years": info.get("Years", ""),
                "description": info.get("Description", ""),
                "image": imgs[0].relative_to(DOCS).as_posix() if imgs else None,
            }
        )
    # Years descending, then role priority, then name
    members.sort(key=lambda m: (-year_value(m["years"]), role_rank(m["role"]), m["name"]))
    return members


def card(m):
    e = html.escape
    img = (
        f'<img class="current-member-image" src="{e(m["image"], quote=True)}" '
        f'alt="Photo of {e(m["name"], quote=True)}" loading="lazy" decoding="async">'
        if m["image"]
        else ""
    )
    return f"""        <article class="current-member">
          {img}
          <h3>{e(m["name"])}</h3>
          <p class="current-member-meta">{e(m["role"])} &middot; {e(m["years"])}</p>
          <p>{e(m["description"])}</p>
        </article>"""


def main():
    members = load_members()
    if members:
        body = '\n        '.join(
            ['<div class="current-members-grid">']
            + [card(m) for m in members]
            + ["</div>"]
        )
    else:
        body = "<!-- no current members found -->"
    page = TEAM_PAGE.read_text(encoding="utf-8")
    if not BLOCK_RE.search(page):
        raise SystemExit("CURRENT-MEMBERS markers not found in team.html")
    page = BLOCK_RE.sub(lambda m: f"{m.group(1)}\n        {body}\n        {m.group(2)}", page)
    TEAM_PAGE.write_text(page, encoding="utf-8")
    print(f"Wrote {len(members)} member(s) to {TEAM_PAGE}")


if __name__ == "__main__":
    main()
