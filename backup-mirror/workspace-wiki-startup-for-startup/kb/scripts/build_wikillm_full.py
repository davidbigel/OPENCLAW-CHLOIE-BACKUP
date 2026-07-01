#!/usr/bin/env python3
"""Build the Startup for Startup WikiLLM corpus product."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


WORKSPACE = Path(__file__).resolve().parents[2]
RAW_DIR = WORKSPACE / "kb" / "sources" / "raw"
LIST_FILE = WORKSPACE / "kb" / "sources" / "lists" / "2026 06 30.md"
OUT_ROOT = WORKSPACE / "kb" / "wikillm"
TODAY = "2026-06-30"


@dataclass
class Segment:
    text: str
    offset: int = 0
    duration: int = 0


@dataclass
class Episode:
    order: int
    video_id: str
    title: str
    url: str
    raw_path: Path
    segments: list[Segment] = field(default_factory=list)
    transcript_text: str = ""
    concepts: list[str] = field(default_factory=list)
    playbooks: list[str] = field(default_factory=list)
    people: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)


CONCEPTS: dict[str, dict[str, object]] = {
    "לוקליזציה-באמצעות-AI": {"name": "לוקליזציה באמצעות AI", "tags": ["AI", "content"], "keywords": ["לוקליזציה", "תרגום", "אנגלית", "שפות", "דיבוב"], "definition": "שימוש ב-AI כדי לקחת תוכן קיים לשפות או קהלים חדשים."},
    "Human-in-the-loop": {"name": "Human in the loop", "tags": ["AI", "quality"], "keywords": ["human in the loop", "לא מושלם", "בקרת איכות"], "definition": "מודל עבודה שבו אדם נשאר אחראי לבקרה ושיפוט לצד AI."},
    "LLM-Wiki": {"name": "LLM Wiki", "tags": ["knowledge-management", "LLM"], "keywords": ["LLM ויקי", "persistent", "קרפטי", "RAG", "retrieval augmented"], "definition": "שכבת ידע מתמשכת שמתחזקת דפי ויקי במקום להסתפק באחזור בזמן שאלה."},
    "קונטקסט-צוותי": {"name": "קונטקסט צוותי", "tags": ["knowledge-management", "team"], "keywords": ["קונטקסט", "מוח צוותי", "צוותי", "decision", "open questions"], "definition": "איסוף והנגשה של ידע עבודה מפוזר לצוות שלם."},
    "AI-agents": {"name": "AI agents", "tags": ["AI", "agents"], "keywords": ["agent", "agents", "אייג", "איג'נט", "סוכן"], "definition": "מערכות AI שמבצעות עבודה, מקבלות משימות ומשתפרות דרך משוב."},
    "ניסוי-מהיר-ב-AI": {"name": "ניסוי מהיר ב-AI", "tags": ["AI", "experimentation"], "keywords": ["לרוץ מהר", "פלייגראונד", "ניסוי", "יוזמות", "משתנה כל שבוע", "קאטינ"], "definition": "סביבת ניסוי מהירה לזיהוי סיגנלים ויוזמות AI בעלות ערך."},
    "אימוץ-AI-בארגון": {"name": "אימוץ AI בארגון", "tags": ["AI", "adoption"], "keywords": ["אימוץ", "דופשן", "הטמעה", "התנגדות", "AI בעבודה"], "definition": "הפער בין יכולות AI לבין שינוי התנהגות אמיתי בארגון."},
    "גיוס-כסף": {"name": "גיוס כסף", "tags": ["fundraising"], "keywords": ["גיוס כסף", "גיוס הון", "משקיעים", "השקעה", "fundraising"], "definition": "תובנות על גיוס הון, משקיעים וניהול תהליך גיוס."},
    "GTM-sales": {"name": "GTM / sales", "tags": ["GTM", "sales"], "keywords": ["go to market", "GTM", "מכירות", "sales", "לידים", "leads"], "definition": "תובנות על מעבר לשוק, מכירות, לידים ולקוחות."},
    "שיווק-ותוכן": {"name": "שיווק ותוכן", "tags": ["marketing", "content"], "keywords": ["שיווק", "מרקטינג", "content", "תוכן", "פודקאסט", "יוטיוב", "קמפיין"], "definition": "תובנות על תוכן, שיווק, הפצה ובניית קהל."},
    "מוצר": {"name": "מוצר", "tags": ["product"], "keywords": ["מוצר", "product", "פיצ", "roadmap", "רודמפ", "משתמש"], "definition": "תובנות על בניית מוצר, שינוי מוצרי ופרקטיקות מוצר."},
    "M&A": {"name": "M&A", "tags": ["M&A", "acquisition"], "keywords": ["רכישה", "רכישת", "M&A", "לקנות סטארטאפ"], "definition": "תובנות על רכישה, מיזוגים, אינטגרציה והחלטות M&A."},
    "יזמות-סולו": {"name": "יזמות סולו", "tags": ["founder", "solo-founder"], "keywords": ["יזם יחיד", "יזמת יחידה", "סולו", "Base44", "מאור שלמה", "לבנות סטארטאפ לבד"], "definition": "תובנות על בניית סטארטאפ לבד או בצוות קטן מאוד."},
    "ברנד": {"name": "ברנד", "tags": ["brand", "marketing"], "keywords": ["ברנד", "brand", "סיפור", "מותג"], "definition": "תובנות על בניית סיפור, מותג ונרטיב."},
    "יוזר-אקוויזישן": {"name": "יוזר אקוויזישן", "tags": ["marketing", "growth"], "keywords": ["יוזר אקוויזישן", "user acquisition", "UA", "קמפיינים"], "definition": "תובנות על רכישת משתמשים, קמפיינים וצמיחה."},
    "סגירת-סטארטאפ": {"name": "סגירת סטארטאפ", "tags": ["shutdown", "failure"], "keywords": ["סגירת", "לסגור", "shutdown", "כישלון"], "definition": "תובנות על סגירת סטארטאפ ומה לומדים מכך."},
    "סטארטאפ-בזמן-מלחמה": {"name": "סטארטאפ בזמן מלחמה", "tags": ["wartime", "crisis"], "keywords": ["מלחמה", "חירום", "שגרת חירום", "איראן"], "definition": "תובנות על קבלת החלטות וניהול סטארטאפ בתקופת חירום."},
    "מדדים": {"name": "מדדים", "tags": ["metrics"], "keywords": ["מדדים", "metric", "metrics", "ARR", "הצלחה", "למדוד"], "definition": "תובנות על מדידה, הצלחה ומדדי ביצוע."},
    "אקוסיסטם-ישראלי": {"name": "אקוסיסטם ישראלי", "tags": ["israel", "ecosystem"], "keywords": ["ישראל", "אקוסיסטם", "תעשייה בארץ", "Startup Nation"], "definition": "תובנות על האקוסיסטם הישראלי והקשרים גלובליים."},
}


PLAYBOOKS: dict[str, dict[str, object]] = {
    "תרגום-תוכן-עם-AI": {"name": "תרגום תוכן עם AI", "concepts": ["לוקליזציה-באמצעות-AI", "Human-in-the-loop"], "keywords": ["לוקליזציה", "תרגום", "דיבוב", "פודקאסט באנגלית"], "when": "כאשר יש נכס תוכן קיים ורוצים להביא אותו לקהל או שפה חדשים."},
    "בניית-מוח-צוותי": {"name": "בניית מוח צוותי", "concepts": ["קונטקסט-צוותי", "LLM-Wiki"], "keywords": ["קונטקסט", "מוח צוותי", "ויקי", "decision"], "when": "כאשר ידע עבודה מפוזר בין פגישות, הודעות, החלטות ושאלות פתוחות."},
    "מעבדת-AI": {"name": "מעבדת AI", "concepts": ["AI-agents", "ניסוי-מהיר-ב-AI", "אימוץ-AI-בארגון"], "keywords": ["agent lab", "פלייגראונד", "לרוץ מהר", "יוזמות"], "when": "כאשר תחום AI זז מהר וצריך לזהות מה שווה אימוץ או מוצר."},
    "רכישת-סטארטאפ": {"name": "רכישת סטארטאפ", "concepts": ["M&A"], "keywords": ["רכישה", "M&A", "לקנות סטארטאפ"], "when": "כאשר בוחנים רכישת סטארטאפ, צוות, מוצר או טכנולוגיה."},
    "אימוץ-AI-בארגון": {"name": "אימוץ AI בארגון", "concepts": ["אימוץ-AI-בארגון"], "keywords": ["אימוץ", "התנגדות", "AI בעבודה", "הטמעה"], "when": "כאשר רוצים להכניס AI לעבודה אמיתית של אנשים וצוותים."},
    "בניית-סטארטאפ-סולו": {"name": "בניית סטארטאפ סולו", "concepts": ["יזמות-סולו"], "keywords": ["יזם יחיד", "יזמת יחידה", "Base44", "מאור שלמה", "לבנות סטארטאפ לבד"], "when": "כאשר מייסד או צוות קטן מנסה להתקדם מהר מאוד עם מעט אנשים."},
    "יוזר-אקוויזישן": {"name": "יוזר אקוויזישן", "concepts": ["יוזר-אקוויזישן", "שיווק-ותוכן"], "keywords": ["יוזר אקוויזישן", "user acquisition"], "when": "כאשר צריך להביא משתמשים בצורה מדידה וחוזרת."},
    "בניית-ברנד": {"name": "בניית ברנד", "concepts": ["ברנד", "שיווק-ותוכן"], "keywords": ["ברנד", "brand", "סיפור"], "when": "כאשר צריך לבנות סיפור מותג שמחזיק יותר ממסר שיווקי רגעי."},
    "התנהלות-בזמן-חירום": {"name": "התנהלות בזמן חירום", "concepts": ["סטארטאפ-בזמן-מלחמה"], "keywords": ["מלחמה", "חירום"], "when": "כאשר חברה צריכה לקבל החלטות עסקיות ואנושיות תחת שגרת חירום."},
}


KNOWN_COMPANIES = {
    # David explicitly asked not to treat the podcast's publishing/source context
    # as a company entity in this KB. Keep original episode titles/quotes intact,
    # but do not generate Monday.com as a navigational company page.
    "Base44": ["Base44"],
    "Gong": ["Gong"],
    "Microsoft": ["Microsoft", "מיקרוסופט"],
    "Nas Daily": ["Nas Daily", "Nuseir Yassin"],
    "Salesforce": ["Salesforce", "סיילספורס", "סלספור"],
    "Zendesk": ["Zendesk", "זנדסק"],
}


KNOWN_PEOPLE = {
    "מאור-שלמה": ["מאור שלמה"],
    "יסמין-לוקץ": ["יסמין לוקץ", "Yasmin"],
    "שירלי-קרליבך": ["שירלי קרליבך"],
    "אודי-לדרגור": ["אודי לדרגור", "Udi Ledergor"],
    "נוסייר-יאסין": ["Nuseir Yassin", "Nas Daily"],
    "עמיחי-אבן-חן": ["Amichai Even Chen", "עמיחי"],
    "ערן-זינמן": ["ערן זינמן", "Eran Zinman"],
    "רועי-מן": ["רועי מן", "Roy Mann"],
    "דניאל-לריה": ["דניאל לריה"],
    "אלירן-גלזר": ["אלירן גלזר"],
    "אסף-אלוביק": ["אסף אלוביק"],
}


def slugify(value: str) -> str:
    value = value.strip().replace("/", "-").replace("|", "-")
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^\w\-\.א-ת׳״]+", "", value, flags=re.UNICODE)
    return value.strip("-") or "unknown"


def parse_playlist(path: Path) -> list[tuple[int, str, str, str]]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"###\s+(\d+)\.\s+(.*?)\n- Video ID: ([A-Za-z0-9_-]{11})\n- Watch URL: (.*?)\n", re.DOTALL)
    return [(int(m.group(1)), m.group(3), m.group(2).strip(), m.group(4).strip()) for m in pattern.finditer(text)]


def load_segments(raw_path: Path) -> tuple[list[Segment], str]:
    text = raw_path.read_text(encoding="utf-8")
    transcript = ""
    if "## Transcript Text" in text:
        after = text.split("## Transcript Text", 1)[1]
        transcript = after.split("## Raw Supadata Result", 1)[0].strip()
    segments: list[Segment] = []
    fence = chr(96) * 3 + "json\n"
    if fence in text:
        raw_json = text.split(fence, 1)[1].rsplit("\n" + chr(96) * 3, 1)[0]
        data = json.loads(raw_json)
        for item in data.get("content", []) or []:
            if isinstance(item, dict) and item.get("text"):
                segments.append(Segment(str(item.get("text", "")).strip(), int(item.get("offset") or 0), int(item.get("duration") or 0)))
    if not segments and transcript:
        for i, line in enumerate(x.strip() for x in transcript.splitlines() if x.strip()):
            segments.append(Segment(line, i * 5000, 5000))
    return segments, transcript


def timecode(ms: int) -> tuple[str, int]:
    seconds = max(0, int(ms // 1000))
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}", seconds


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    low = text.lower()
    return any(str(k).lower() in low for k in keywords)


def classify_episode(ep: Episode) -> None:
    haystack = f"{ep.title}\n{ep.transcript_text[:12000]}".lower()
    for slug, info in CONCEPTS.items():
        if contains_any(haystack, info["keywords"]):
            ep.concepts.append(slug)
    if not ep.concepts:
        ep.concepts.append("מוצר")
    for slug, info in PLAYBOOKS.items():
        if contains_any(haystack, info["keywords"]):
            ep.playbooks.append(slug)
    for company, aliases in KNOWN_COMPANIES.items():
        if contains_any(haystack, aliases):
            ep.companies.append(company)
    for person, aliases in KNOWN_PEOPLE.items():
        if contains_any(haystack, aliases):
            ep.people.append(person)
    for chunk in re.findall(r"\(([^()]{3,80})\)", ep.title):
        if any(x in chunk.lower() for x in ["base44", "gong", "microsoft"]):
            continue
        for part in re.split(r"\s+ו|,| and ", chunk):
            part = part.strip()
            if 2 <= len(part.split()) <= 4:
                ep.people.append(slugify(part))
    ep.concepts = sorted(dict.fromkeys(ep.concepts))
    ep.playbooks = sorted(dict.fromkeys(ep.playbooks))
    ep.people = sorted(dict.fromkeys(ep.people))
    ep.companies = sorted(dict.fromkeys(ep.companies))


def evidence_for_episode(ep: Episode, limit: int = 6) -> list[Segment]:
    keywords: list[str] = []
    for slug in ep.concepts:
        keywords.extend(CONCEPTS.get(slug, {}).get("keywords", []))
    for slug in ep.playbooks:
        keywords.extend(PLAYBOOKS.get(slug, {}).get("keywords", []))
    candidates: list[tuple[int, int, Segment]] = []
    for i, seg in enumerate(ep.segments):
        text = seg.text.strip()
        if len(text) < 22 or text in {"[מוזיקה]", "כן", "אוקיי"}:
            continue
        score = min(len(text), 90)
        if contains_any(text, keywords):
            score += 120
        if i < 80:
            score += 20
        candidates.append((score, i, seg))
    chosen = [seg for _, _, seg in sorted(candidates, key=lambda x: (-x[0], x[1]))[:limit]]
    return sorted(chosen, key=lambda s: s.offset)


def citation(ep: Episode, seg: Segment) -> str:
    stamp, seconds = timecode(seg.offset)
    return f'> "{seg.text}"\n> Source: [[episodes/{ep.video_id}]] | {ep.title} | {ep.video_id} | {stamp} | https://www.youtube.com/watch?v={ep.video_id}&t={seconds}s'


def yaml_list(values: list[str]) -> str:
    return "[" + ", ".join(values) + "]"


def write_if_allowed(path: Path, content: str, *, force: bool = False) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        existing = path.read_text(encoding="utf-8")
        if "generated_by: kb/scripts/build_wikillm_full.py" not in existing:
            return False
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def episode_page(ep: Episode) -> str:
    evidence = evidence_for_episode(ep)
    concept_links = [f"[[concepts/{slug}]]" for slug in ep.concepts]
    people_links = [f"[[people/{p}]]" for p in ep.people]
    company_links = [f"[[companies/{slugify(c)}]]" for c in ep.companies]
    playbook_links = [f"[[playbooks/{p}]]" for p in ep.playbooks]
    topic_names = [str(CONCEPTS[c]["name"]) for c in ep.concepts if c in CONCEPTS]
    topic_sentence = ", ".join(topic_names[:5]) if topic_names else "תובנות סטארטאפ מהקורפוס"
    evidence_md = "\n\n".join(citation(ep, seg) for seg in evidence)
    return f'''---
type: episode
video_id: {ep.video_id}
title: "{ep.title.replace('"', "'")}"
source_url: {ep.url}
transcript_path: kb/sources/raw/{ep.video_id}.md
date_ingested: {TODAY}
tags: {yaml_list([str(CONCEPTS[c]["tags"][0]) for c in ep.concepts if c in CONCEPTS])}
people: {yaml_list(ep.people)}
companies: {yaml_list(ep.companies)}
concepts: {yaml_list(ep.concepts)}
status: draft-auto
generated_by: kb/scripts/build_wikillm_full.py
---

# {ep.title}

## Source

- Video ID: {ep.video_id}
- URL: {ep.url}
- Raw transcript: kb/sources/raw/{ep.video_id}.md

## Executive Summary

- דף זה נוצר כחלק מהרחבת הפיילוט לכל קורפוס 35 הפרקים.
- הפרק מסווג כרגע סביב: {topic_sentence}.
- הסיכום כאן הוא שכבת עבודה ראשונית; יש לשפר אותו בקריאה אנושית/AI עמוקה יותר של הפרק.
- הציטוטים למטה נלקחו מהתמלול הגולמי עם timecode וקישור ישיר לוידאו.

## Key Evidence Items

{evidence_md}

## People

{chr(10).join(f"- {x}" for x in people_links) if people_links else "- טרם זוהו אנשים באופן אמין מעבר למטאדאטה/תמלול."}

## Companies

{chr(10).join(f"- {x}" for x in company_links) if company_links else "- לא זוהתה חברה מרכזית בשכבת המטאדאטה/היוריסטיקה."}

## Concepts

{chr(10).join(f"- {x}" for x in concept_links)}

## Playbooks / Tactics

{chr(10).join(f"- {x}" for x in playbook_links) if playbook_links else "- טרם זוהה פלייבוק מובחן."}

## Snoracle Synthesis

Source type: Snoracle synthesis, based on early automated evidence extraction.

הפרק נוסף לשכבת ה-WikiLLM כדי לאפשר חיפוש, ציטוט וקישוריות. אין להתייחס לדף זה כסיכום סופי; הוא בסיס לעיבוד המשך.

## Open Questions

- אילו טענות מהפרק צריכות להפוך ל-claim עצמאי?
- אילו מושגים חוזרים בפרקים אחרים ומצדיקים הרחבה?
- האם יש בפרק דוגמה מעשית שצריכה להפוך לפלייבוק?

## Related Pages

{chr(10).join(f"- {x}" for x in concept_links + people_links + company_links + playbook_links)}
'''


def concept_page(slug: str, info: dict[str, object], episodes: list[Episode]) -> str:
    ev = []
    for ep in episodes[:6]:
        segs = evidence_for_episode(ep, 3)
        if segs:
            ev.append(citation(ep, segs[0]))
    evidence = "\n\n".join(ev) if ev else "_טרם נבחרו ציטוטים._"
    ep_links = "\n".join(f"- [[episodes/{ep.video_id}]] - {ep.title}" for ep in episodes)
    tags = yaml_list([str(x) for x in info.get("tags", [])])
    return f'''---
type: concept
tags: {tags}
aliases: []
source_count: {len(episodes)}
status: draft-auto
generated_by: kb/scripts/build_wikillm_full.py
---

# {info["name"]}

## Definition

{info["definition"]}

## What The Corpus Says

מושג זה זוהה ב-{len(episodes)} פרקים בקורפוס. הדף הוא בסיס אוטומטי להמשך סינתזה.

## Evidence

{evidence}

## Source Episodes

{ep_links}

## Patterns

- לזהות באילו הקשרים המושג מופיע.
- להפריד בין דוגמאות episode-specific לבין טענה כללית.
- לקדם טענות חוזרות אל [[claims/index]] או אל claim עצמאי.

## Practical Takeaways

דרוש עיבוד המשך כדי להפוך את רשימת המקורות לסינתזה חזקה.

## Related

- [[index]]
'''


def playbook_page(slug: str, info: dict[str, object], episodes: list[Episode]) -> str:
    concepts = [f"[[concepts/{c}]]" for c in info.get("concepts", [])]
    ev = []
    for ep in episodes[:5]:
        segs = evidence_for_episode(ep, 3)
        if segs:
            ev.append(citation(ep, segs[0]))
    evidence = "\n\n".join(ev) if ev else "_טרם נבחרו ציטוטים._"
    return f'''---
type: playbook
tags: []
source_count: {len(episodes)}
confidence: low
status: draft-auto
generated_by: kb/scripts/build_wikillm_full.py
---

# {info["name"]}

## When To Use This

{info["when"]}

## Core Moves

1. לזהות את ההקשר המדויק מתוך הפרקים.
2. לאסוף ציטוטים וטענות מקור.
3. להפוך דוגמאות חוזרות לצעדים פרקטיים.
4. לסמן מגבלות ואיפה הפלייבוק נשבר.

## Evidence

{evidence}

## Risks / Failure Modes

- הכללה רחבה מדי מפרק אחד.
- הפיכת דוגמה ספציפית לעצות גנריות.
- שימוש בפלייבוק בלי לבדוק התאמה לשלב החברה.

## Snoracle Take

Source type: Snoracle synthesis.

זה פלייבוק במצב draft. הוא צריך עוד עיבוד לפני שימוש כהמלצה חזקה.

## Related

{chr(10).join(f"- {c}" for c in concepts) if concepts else "- [[index]]"}
'''


def entity_page(kind: str, display: str, episodes: list[Episode]) -> str:
    ep_links = "\n".join(f"- [[episodes/{ep.video_id}]] - {ep.title}" for ep in episodes)
    label = "person" if kind == "people" else "company"
    body = "חברה שמוזכרת בקורפוס. דף זה אינו מעיד על קשר מועדף לפודקאסט; הוא רק פריט ניווט מקור." if kind == "companies" else "אדם שמוזכר בקורפוס או במטאדאטה של הפרקים. יש לאמת תפקידים ופרטים לפני שימוש חיצוני."
    return f'''---
type: {label}
aliases: []
episodes: {yaml_list([ep.video_id for ep in episodes])}
status: draft-auto
generated_by: kb/scripts/build_wikillm_full.py
---

# {display}

## Corpus Role

{body}

## Episodes

{ep_links}

## Main Ideas / Claims

דורש עיבוד המשך מתוך דפי הפרקים והציטוטים.

## Related Concepts

- [[index]]
'''


def build_index(episodes: list[Episode], concept_eps, playbook_eps, people_eps, company_eps) -> str:
    ep_lines = "\n".join(f"- [[episodes/{ep.video_id}]] - {ep.order}. {ep.title}" for ep in sorted(episodes, key=lambda e: e.order))
    concept_lines = "\n".join(f"- [[concepts/{slug}]] - {CONCEPTS[slug]['name']} ({len(eps)} פרקים)" for slug, eps in sorted(concept_eps.items(), key=lambda x: (-len(x[1]), x[0])))
    people_lines = "\n".join(f"- [[people/{slug}]] - {slug.replace('-', ' ')} ({len(eps)} פרקים)" for slug, eps in sorted(people_eps.items(), key=lambda x: (-len(x[1]), x[0])))
    company_lines = "\n".join(f"- [[companies/{slugify(name)}]] - {name} ({len(eps)} פרקים)" for name, eps in sorted(company_eps.items(), key=lambda x: (-len(x[1]), x[0])))
    playbook_lines = "\n".join(f"- [[playbooks/{slug}]] - {PLAYBOOKS[slug]['name']} ({len(eps)} פרקים)" for slug, eps in sorted(playbook_eps.items(), key=lambda x: (-len(x[1]), x[0])))
    return f'''---
type: index
status: full-corpus-draft
date_updated: {TODAY}
source_prompt: docs/sfs-wikillm.md
product_root: kb/wikillm
generated_by: kb/scripts/build_wikillm_full.py
---

# Startup for Startup WikiLLM

זהו מוצר WikiLLM ראשוני עבור 35 תמלולי Startup for Startup שנשמרו ב-kb/sources/raw.

הבנייה הנוכחית היא full-corpus draft: כל הפרקים מיוצגים, יש ציטוטים עם timecode, ויש שכבות ניווט למושגים, אנשים, חברות שמוזכרות, פלייבוקים וטענות. חלק מהדפים עדיין דורשים סינתזה אנושית/AI עמוקה יותר.

## גבולות מקור

- מקור האמת: תמלולי Supadata ב-kb/sources/raw.
- raw quotes נשמרים כפי שהם, גם אם יש שגיאות תמלול.
- אין העשרה חיצונית ללא בקשה מפורשת.
- חברה שמופיעה בדף חברה היא רק entity שמוזכר בקורפוס, לא עוגן של ה-KB.

## פרקים ({len(episodes)})

{ep_lines}

## מושגים ({len(concept_eps)})

{concept_lines}

## אנשים ({len(people_eps)})

{people_lines or "- טרם זוהו אנשים מעבר לפיילוט/מטאדאטה."}

## חברות שמוזכרות ({len(company_eps)})

{company_lines or "- לא זוהו חברות במטאדאטה/היוריסטיקה."}

## פלייבוקים ({len(playbook_eps)})

{playbook_lines or "- טרם זוהו פלייבוקים."}

## טענות וראיות

- [[claims/index]] - טענות הפיילוט המקוריות.
- [[claims/corpus-evidence-register]] - רשימת ראיות אוטומטית מכל 35 הפרקים.

## שאלות וסינתזות

- [[questions/מה-המודל-הנכון-לפיילוט]]
- [[questions/סטטוס-הרחבת-הקורפוס]]

## Recommended Next Step

לבצע lint איכותי על 5-10 דפי episode אוטומטיים, ואז להחליט אילו concept/playbook pages דורשים סינתזה ידנית עמוקה.
'''


def evidence_register(episodes: list[Episode]) -> str:
    parts = ["---", "type: evidence_register", "status: full-corpus-draft", f"date_updated: {TODAY}", "generated_by: kb/scripts/build_wikillm_full.py", "---", "", "# Corpus Evidence Register", "", "רשימת ראיות אוטומטית מכל 35 הפרקים. זו אינה רשימת claims סופית; זה חומר גלם מצוטט להמשך סינתזה.", ""]
    for ep in sorted(episodes, key=lambda e: e.order):
        parts.append(f"## {ep.order}. [[episodes/{ep.video_id}]] - {ep.title}\n")
        for seg in evidence_for_episode(ep, 3):
            parts.append(citation(ep, seg))
            parts.append("")
    return "\n".join(parts)


def status_question(episodes: list[Episode]) -> str:
    return f'''---
type: question
question: "מה סטטוס הרחבת הקורפוס אחרי המעבר מפיילוט ל-35 פרקים?"
date_answered: {TODAY}
tags: [status, full-corpus, WikiLLM]
sources: []
status: full-corpus-draft
generated_by: kb/scripts/build_wikillm_full.py
---

# סטטוס הרחבת הקורפוס

## Short Answer

ה-WikiLLM הורחב מפיילוט של 3 פרקים לייצוג מלא של {len(episodes)} פרקים. כל פרק קיבל דף episode או נשמר כדף curated קיים, והמערכת כוללת אינדקסים, מושגים, פלייבוקים, entities ורשימת ראיות.

## Evidence

- [[index]] כולל את כל הפרקים.
- [[claims/corpus-evidence-register]] כולל ציטוטים עם timecode מכל פרק.
- [[log]] מתעד את המעבר מפיילוט ל-full-corpus draft.

## Analysis

Source type: Snoracle synthesis.

השלב הזה יוצר כיסוי רוחבי. הוא עדיין לא יוצר סינתזה עמוקה לכל פרק. ההבדל חשוב: עכשיו אפשר לנווט בכל הקורפוס, אבל צריך עוד passes כדי להפוך דפי draft לדפי ידע חזקים.

## Practical Implications

- אפשר להתחיל לשאול שאלות על כל 35 הפרקים, אבל תשובות עמוקות עדיין ידרשו קריאה חזרה ל-raw transcripts.
- concept pages שנוצרו אוטומטית צריכים ליטוש.
- claims סופיים צריכים להתפצל בהמשך לדפים עצמאיים כאשר יש מספיק חזרתיות.

## Follow-Up Questions

- איזה 5 פרקים לעבד ידנית לעומק אחרי הפיילוט?
- האם concept pages צריכים frontmatter עשיר יותר?
- האם לבנות כלי חיפוש/ציטוט אוטומטי מעל kb/wikillm?
'''


def episodes_index(episodes: list[Episode]) -> str:
    lines = [f"- [[episodes/{ep.video_id}]] - {ep.order}. {ep.title}" for ep in sorted(episodes, key=lambda e: e.order)]
    return "---\ntype: episodes_index\nstatus: full-corpus-draft\n---\n\n# Episodes\n\n" + "\n".join(lines) + "\n"


def append_log() -> None:
    log = OUT_ROOT / "log.md"
    marker = "## [2026-06-30] ingest | full corpus draft | 35 episodes"
    text = log.read_text(encoding="utf-8") if log.exists() else "---\ntype: log\nstatus: active\n---\n\n# WikiLLM Log\n"
    if marker in text:
        return
    text = text.rstrip() + f"""

{marker}

- Expanded WikiLLM from 3-episode pilot to full-corpus draft.
- Generated missing episode pages under kb/wikillm/episodes.
- Rebuilt kb/wikillm/index.md to include all 35 episodes.
- Created/updated auto-generated concept, people, company, playbook, and evidence-register pages.
- Excluded Monday.com from generated company entities per project boundary; original source titles/quotes remain unchanged.
- Preserved curated pilot pages unless absent.
"""
    log.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated pages.")
    args = parser.parse_args()

    for dirname in ["episodes", "concepts", "people", "companies", "playbooks", "claims", "questions"]:
        (OUT_ROOT / dirname).mkdir(parents=True, exist_ok=True)

    episodes: list[Episode] = []
    for order, video_id, title, url in parse_playlist(LIST_FILE):
        raw = RAW_DIR / f"{video_id}.md"
        if not raw.exists():
            continue
        segments, transcript = load_segments(raw)
        ep = Episode(order=order, video_id=video_id, title=title, url=url, raw_path=raw, segments=segments, transcript_text=transcript)
        classify_episode(ep)
        episodes.append(ep)

    concept_eps: dict[str, list[Episode]] = defaultdict(list)
    playbook_eps: dict[str, list[Episode]] = defaultdict(list)
    people_eps: dict[str, list[Episode]] = defaultdict(list)
    company_eps: dict[str, list[Episode]] = defaultdict(list)

    written = 0
    skipped = 0
    for ep in episodes:
        for c in ep.concepts:
            concept_eps[c].append(ep)
        for p in ep.playbooks:
            playbook_eps[p].append(ep)
        for p in ep.people:
            people_eps[p].append(ep)
        for c in ep.companies:
            company_eps[c].append(ep)
        ok = write_if_allowed(OUT_ROOT / "episodes" / f"{ep.video_id}.md", episode_page(ep), force=args.force)
        written += int(ok)
        skipped += int(not ok)

    for slug, eps in concept_eps.items():
        ok = write_if_allowed(OUT_ROOT / "concepts" / f"{slug}.md", concept_page(slug, CONCEPTS[slug], eps), force=args.force)
        written += int(ok)
        skipped += int(not ok)

    for slug, eps in playbook_eps.items():
        ok = write_if_allowed(OUT_ROOT / "playbooks" / f"{slug}.md", playbook_page(slug, PLAYBOOKS[slug], eps), force=args.force)
        written += int(ok)
        skipped += int(not ok)

    for slug, eps in people_eps.items():
        ok = write_if_allowed(OUT_ROOT / "people" / f"{slug}.md", entity_page("people", slug.replace("-", " "), eps), force=args.force)
        written += int(ok)
        skipped += int(not ok)

    for name, eps in company_eps.items():
        ok = write_if_allowed(OUT_ROOT / "companies" / f"{slugify(name)}.md", entity_page("companies", name, eps), force=args.force)
        written += int(ok)
        skipped += int(not ok)

    (OUT_ROOT / "index.md").write_text(build_index(episodes, concept_eps, playbook_eps, people_eps, company_eps), encoding="utf-8")
    (OUT_ROOT / "episodes" / "index.md").write_text(episodes_index(episodes), encoding="utf-8")
    (OUT_ROOT / "claims" / "corpus-evidence-register.md").write_text(evidence_register(episodes), encoding="utf-8")
    (OUT_ROOT / "questions" / "סטטוס-הרחבת-הקורפוס.md").write_text(status_question(episodes), encoding="utf-8")
    append_log()

    print(f"episodes={len(episodes)} written={written} skipped_existing={skipped}")
    print(f"concepts={len(concept_eps)} playbooks={len(playbook_eps)} people={len(people_eps)} companies={len(company_eps)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
