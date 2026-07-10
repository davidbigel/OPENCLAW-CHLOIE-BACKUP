import asyncio
import pathlib
import re

import edge_tts

SOURCE = pathlib.Path("/root/.openclaw/workspace-Chloe-Speaker/DAVID/OKF_OS/PR/PR1.md")
TARGET = pathlib.Path("/root/.openclaw/workspace-Chloe-Speaker/DAVID/OKF_OS/PR/PR1.mp3")

def clean_markdown(text: str) -> str:
    text = re.sub(r"^#\\s*", "", text, flags=re.M)
    text = text.replace("## ", "\\n\\n").replace("### ", "\\n\\n")
    text = text.replace("`", "")
    text = text.replace("->", "עד")
    text = re.sub(r"\\n{3,}", "\\n\\n", text)
    return text

async def main() -> None:
    text = clean_markdown(SOURCE.read_text(encoding="utf-8"))
    communicate = edge_tts.Communicate(
        text,
        voice="he-IL-HilaNeural",
        rate="+0%",
        pitch="+0Hz",
    )
    await communicate.save(str(TARGET))

if __name__ == "__main__":
    asyncio.run(main())
