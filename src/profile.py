"""
Load a candidate profile.json (JSON Resume format + job preferences),
validate it against profile_schema.json, and render it as plain text for the AI.
Contact details and other personal fields are never sent.
"""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

_SCHEMA = json.loads((Path(__file__).parent / "profile_schema.json").read_text())


def _dates(item: dict, start: str = "startDate", end: str = "endDate") -> str:
    s, e = item.get(start), item.get(end)
    if not s and not e:
        return ""
    return f" ({s or '?'} – {e or 'Present'})"


def _bullets(items: list[str], indent: str = "  ") -> list[str]:
    return [f"{indent}- {x}" for x in items]


def _render(p: dict) -> str:
    out: list[str] = []

    b = p.get("basics", {})
    if b.get("name"):
        out.append(f"Name: {b['name']}")
    if b.get("label"):
        out.append(f"Title: {b['label']}")
    loc = b.get("location", {})
    place = ", ".join(x for x in (loc.get("city"), loc.get("region"), loc.get("countryCode")) if x)
    if place:
        out.append(f"Location: {place}")
    if b.get("summary"):
        out += ["", "SUMMARY", b["summary"]]

    prefs = p.get("profile", {}).get("jobPreferences", {})
    if prefs:
        out += ["", "JOB PREFERENCES"]
        if "yearsExperience" in prefs:
            out.append(f"  Years of experience: {prefs['yearsExperience']}")
        if "noticePeriod" in prefs:
            out.append(f"  Notice period (days): {prefs['noticePeriod']}")
        for key, label in [
            ("preferredRole", "Preferred roles"), ("preferredLocations", "Preferred locations"),
            ("employmentType", "Employment type"), ("jobType", "Job type"),
            ("shiftPreference", "Shift preference"),
        ]:
            if prefs.get(key):
                out.append(f"  {label}: {', '.join(prefs[key])}")

    if p.get("work"):
        out += ["", "WORK EXPERIENCE"]
        for w in p["work"]:
            where = f", {w['location']}" if w.get("location") else ""
            out.append(f"{w.get('position', '')} at {w.get('name', '')}{where}{_dates(w)}")
            if w.get("summary"):
                out.append(f"  {w['summary']}")
            out += _bullets(w.get("highlights", []))

    if p.get("projects"):
        out += ["", "PROJECTS"]
        for pr in p["projects"]:
            roles = f" — {', '.join(pr['roles'])}" if pr.get("roles") else ""
            out.append(f"{pr.get('name', '')}{roles}{_dates(pr)}")
            if pr.get("description"):
                out.append(f"  {pr['description']}")
            out += _bullets(pr.get("highlights", []))
            if pr.get("keywords"):
                out.append(f"  Keywords: {', '.join(pr['keywords'])}")

    if p.get("skills"):
        out += ["", "SKILLS"]
        for s in p["skills"]:
            level = f" ({s['level']})" if s.get("level") else ""
            out.append(f"  {s.get('name', '')}{level}: {', '.join(s.get('keywords', []))}")

    if p.get("education"):
        out += ["", "EDUCATION"]
        for e in p["education"]:
            degree = " in ".join(x for x in (e.get("studyType"), e.get("area")) if x)
            score = f", score {e['score']}" if e.get("score") else ""
            out.append(f"  {degree} — {e.get('institution', '')}{_dates(e)}{score}")
            if e.get("courses"):
                out.append(f"    Courses: {', '.join(e['courses'])}")

    if p.get("volunteer"):
        out += ["", "VOLUNTEER"]
        for v in p["volunteer"]:
            out.append(f"{v.get('position', '')} at {v.get('organization', '')}{_dates(v)}")
            if v.get("summary"):
                out.append(f"  {v['summary']}")
            out += _bullets(v.get("highlights", []))

    if p.get("certificates"):
        out += ["", "CERTIFICATES"]
        for c in p["certificates"]:
            by = f" — {c['issuer']}" if c.get("issuer") else ""
            when = f" ({c['date']})" if c.get("date") else ""
            out.append(f"  {c.get('name', '')}{by}{when}")

    if p.get("awards"):
        out += ["", "AWARDS"]
        for a in p["awards"]:
            by = f" — {a['awarder']}" if a.get("awarder") else ""
            out.append(f"  {a.get('title', '')}{by}" + (f": {a['summary']}" if a.get("summary") else ""))

    if p.get("publications"):
        out += ["", "PUBLICATIONS"]
        for pub in p["publications"]:
            out.append(f"  {pub.get('name', '')}" + (f" ({pub['publisher']})" if pub.get("publisher") else ""))

    if p.get("languages"):
        out += ["", "LANGUAGES"]
        out += [f"  {l.get('language', '')}" + (f" ({l['fluency']})" if l.get("fluency") else "") for l in p["languages"]]

    if p.get("interests"):
        out += ["", "INTERESTS"]
        out += [f"  {i.get('name', '')}" + (f": {', '.join(i['keywords'])}" if i.get("keywords") else "") for i in p["interests"]]

    # Deliberately omitted: email, phone, image, address, postal code, profile links,
    # date of birth, gender, CTC and references.
    return "\n".join(out).strip()


def load_profile(path: Path) -> str:
    """Validate profile.json and return interview-ready text. Raises ValueError on schema errors."""
    data = json.loads(path.read_text())
    errors = sorted(Draft202012Validator(_SCHEMA).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        msgs = [f"  {'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in errors]
        raise ValueError("profile.json does not match the schema:\n" + "\n".join(msgs))
    return _render(data)
