---
type: episode
video_id: pRtCeFZFm1M
title: "353: איך בנינו ״מוח צוותי״ שמתעדכן לבד"
source_url: https://www.youtube.com/watch?v=pRtCeFZFm1M
transcript_path: kb/sources/raw/pRtCeFZFm1M.md
date_ingested: 2026-06-30
tags: [LLM-Wiki, RAG, team-context, knowledge-management, AI]
people: [רוני ארניב, שחר ארבל]
companies: []
concepts: [LLM Wiki, קונטקסט צוותי, RAG, ידע מתמשך]
status: pilot
---

# 353: איך בנינו ״מוח צוותי״ שמתעדכן לבד

## Source

- Video ID: pRtCeFZFm1M
- URL: https://www.youtube.com/watch?v=pRtCeFZFm1M
- Raw transcript: kb/sources/raw/pRtCeFZFm1M.md

## Executive Summary

- הפרק מסביר איך לבנות "מוח צוותי" שמרכז קונטקסט, החלטות, שאלות פתוחות ופעולות.
- נקודת הכאב: ידע צוותי מפוזר בפגישות, Slack, WhatsApp, מסמכים ושיחות מסדרון.
- ניסיון ראשון עם קבצים פשוטים עובד בהתחלה, אבל נשבר כשהקונטקסט גדל והופך למפלצת.
- הפרק מציג את רעיון ה-LLM Wiki של Karpathy כחלופה ל-RAG בלבד.
- ההבדל המרכזי: הוויקי מתעדכן ומצטבר, במקום לחפש מחדש בכל שאלה.
- זה פרק בסיסי לקורפוס שלנו כי הוא כמעט מתאר את המוצר שאנחנו בונים כאן.

## Key Evidence Items

### הבעיה: קונטקסט צוותי מפוזר

> "בונים קונטקסט ציוותי שיטיס את העבודה"
> Source: [[episodes/pRtCeFZFm1M]] | 353: איך בנינו ״מוח צוותי״ שמתעדכן לבד | pRtCeFZFm1M | 00:00:04 | https://www.youtube.com/watch?v=pRtCeFZFm1M&t=4s

> "א שמייצג את כל הארגון, את כל הבילדרים,"
> Source: [[episodes/pRtCeFZFm1M]] | 353: איך בנינו ״מוח צוותי״ שמתעדכן לבד | pRtCeFZFm1M | 00:01:58 | https://www.youtube.com/watch?v=pRtCeFZFm1M&t=118s

סינתזה: המוח הצוותי לא אמור להיות "עוד סיכום". הוא אמור לייצג את הארגון בצורה שימושית לכל תפקיד.

### ניסיון ראשון: קבצים פשוטים שמצטברים

> "חמוד בגיטאב עם שלושה קבצים באמת סופר"
> Source: [[episodes/pRtCeFZFm1M]] | 353: איך בנינו ״מוח צוותי״ שמתעדכן לבד | pRtCeFZFm1M | 00:04:17 | https://www.youtube.com/watch?v=pRtCeFZFm1M&t=257s

> "תמים decision אtion items וopen"
> Source: [[episodes/pRtCeFZFm1M]] | 353: איך בנינו ״מוח צוותי״ שמתעדכן לבד | pRtCeFZFm1M | 00:04:19 | https://www.youtube.com/watch?v=pRtCeFZFm1M&t=259s

סינתזה: התחלה קטנה עם decisions/action items/open questions היא נכונה, אבל היא לא מספיקה בלי מבנה שמתמודד עם גדילה.

### נקודת שבירה: הקונטקסט הופך למפלצת

> "הקונטקסט גדל בטירוף כל הזמן אז הקבצים"
> Source: [[episodes/pRtCeFZFm1M]] | 353: איך בנינו ״מוח צוותי״ שמתעדכן לבד | pRtCeFZFm1M | 00:04:39 | https://www.youtube.com/watch?v=pRtCeFZFm1M&t=279s

> "האלה ניים מפלצות ואז כבר קשה רגע להשתלט"
> Source: [[episodes/pRtCeFZFm1M]] | 353: איך בנינו ״מוח צוותי״ שמתעדכן לבד | pRtCeFZFm1M | 00:04:42 | https://www.youtube.com/watch?v=pRtCeFZFm1M&t=282s

סינתזה: אם אין שכבת ויקי שמפרקת ידע לדפים, קישורים ומושגים, קובץ אחד גדול הופך לבעיה חדשה.

### LLM Wiki כוויקי מתמשך

> "שלו זה שהוא בעצם קרא לזה persistent"
> Source: [[episodes/pRtCeFZFm1M]] | 353: איך בנינו ״מוח צוותי״ שמתעדכן לבד | pRtCeFZFm1M | 00:08:20 | https://www.youtube.com/watch?v=pRtCeFZFm1M&t=500s

> "ויקי. זאת אומרת זה גם ויקי שכל הזמן"
> Source: [[episodes/pRtCeFZFm1M]] | 353: איך בנינו ״מוח צוותי״ שמתעדכן לבד | pRtCeFZFm1M | 00:08:23 | https://www.youtube.com/watch?v=pRtCeFZFm1M&t=503s

> "מתעתקנת"
> Source: [[episodes/pRtCeFZFm1M]] | 353: איך בנינו ״מוח צוותי״ שמתעדכן לבד | pRtCeFZFm1M | 00:08:25 | https://www.youtube.com/watch?v=pRtCeFZFm1M&t=505s

סינתזה: זה הלב של ה-WikiLLM שלנו: ידע שלא נשלף רק בזמן שאלה, אלא מתעדכן כארטיפקט.

## People

- [[people/רוני-ארניב]]
- [[people/שחר-ארבל]]

## Concepts

- [[concepts/LLM-Wiki]]
- [[concepts/קונטקסט-צוותי]]

## Playbooks / Tactics

- [[playbooks/בניית-מוח-צוותי]]

## Snoracle Synthesis

Source type: Snoracle synthesis, based on cited podcast evidence.

הפרק נותן אזהרה חשובה: "בוא נשים הכל בקובץ" מרגיש זריז, אבל נשבר מהר. אם רוצים ידע שמשרת צוות, צריך לעבור מוקדם יחסית ממסמך מצטבר למבנה ויקי: דפי מקור, דפי מושגים, טענות, שאלות פתוחות, וקישורים. זה בדיוק ההבדל בין מחברת לבין מערכת ידע.

## Open Questions

- מה המבנה המינימלי שמספיק לפני שמייצרים יותר מדי דפים?
- איך מונעים מוויקי צוותי להפוך לעוד מקור שצריך לתחזק ידנית?
- האם claims צריכים להיות דפים נפרדים או בלוקים מובנים?

## Related Pages

- [[concepts/LLM-Wiki]]
- [[concepts/קונטקסט-צוותי]]
- [[playbooks/בניית-מוח-צוותי]]
- [[claims/index]]
