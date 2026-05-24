import re
import os

daily_dir = r"D:\Obsidian Brain\Brain\00_Meta\daily"

error_files = [
    "2026-04-25.md", "2026-04-26.md", "2026-04-28.md", "2026-04-29.md",
    "2026-04-30.md", "2026-05-01.md", "2026-05-03.md", "2026-05-04.md",
    "2026-05-05.md", "2026-05-06.md", "2026-05-07.md", "2026-05-08.md",
    "2026-05-12.md", "2026-05-13.md", "2026-05-22.md", "2026-05-23.md",
    "2026-05-24.md"
]

error_pattern = re.compile(
    r'## \[SessionEnd\] \d{2}:\d{2}\s*\n\s*\n⚠️ (?:ANTHROPIC_API_KEY not set[^\n]*|Extraction failed:[^\n]*)(\n|$)',
    re.MULTILINE
)

for fname in error_files:
    fpath = os.path.join(daily_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    cleaned = error_pattern.sub('', content)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()

    removed = len(content) - len(cleaned)
    print(f"{fname}: removed {removed} chars, kept {len(cleaned)} chars")

    with open(fpath, 'w', encoding='utf-8') as f:
        if cleaned:
            f.write(cleaned + '\n')

print("\nDone.")
