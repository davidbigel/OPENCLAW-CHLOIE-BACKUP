import asyncio
import pathlib
import re
import tempfile
import subprocess

import edge_tts

SOURCE = pathlib.Path("/root/.openclaw/workspace-Chloe-Speaker/DAVID/OKF_OS/PR/PR1.md")
TARGET = pathlib.Path("/root/.openclaw/workspace-Chloe-Speaker/DAVID/OKF_OS/PR/PR1.mp3")

def clean_markdown(text: str) -> str:
    text = text.replace("`", "")
    text = text.replace("->", "עד")
    text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def split_sections(text: str):
    parts = re.split(r"\n(?=## )", text)
    return [p.strip() for p in parts if p.strip()]

async def synthesize(text: str, out: pathlib.Path) -> None:
    comm = edge_tts.Communicate(
        text,
        voice="he-IL-HilaNeural",
        rate="+0%",
        pitch="+0Hz",
    )
    await comm.save(str(out))

async def main() -> None:
    source_text = SOURCE.read_text(encoding="utf-8")
    sections = split_sections(source_text)

    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        chunk_files = []
        for i, section in enumerate(sections, start=1):
            cleaned = clean_markdown(section)
            chunk = td / f"chunk_{i:02d}.mp3"
            await synthesize(cleaned, chunk)
            chunk_files.append(chunk)

        concat_list = td / "concat.txt"
        concat_list.write_text("".join(f"file '{p.as_posix()}'\n" for p in chunk_files), encoding="utf-8")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(TARGET)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

if __name__ == "__main__":
    asyncio.run(main())
