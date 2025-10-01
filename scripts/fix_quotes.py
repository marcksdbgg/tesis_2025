"""Normalize quotation marks in .tex files to LaTeX conventions.

This script finds straight ASCII double quotes and common Unicode “smart”
quotes and replaces them with LaTeX-style opening `` and closing '' marks.
It operates on .tex files under the given root (default: repository root).
Backups are written with a .bak extension next to each modified file.

Usage: python scripts/fix_quotes.py [--root ROOT]
"""
from pathlib import Path
import re
import argparse


REPLACEMENTS = [
    # Common Unicode smart quotes to ASCII double quote
    (re.compile(r'[\u201C\u201D\u201E\u201F]'), '"'),
    # Left single smart quote and right single smart quote -> ASCII '
    (re.compile(r"[\u2018\u2019\u201A\u201B]"), "'")
]

DOUBLE_QUOTE_PATTERN = re.compile(r'"(.*?)"', flags=re.DOTALL)


def normalize_text(text: str) -> str:
    # First normalize smart quotes to ASCII equivalents
    for pat, repl in REPLACEMENTS:
        text = pat.sub(repl, text)

    # Then convert ASCII double-quoted segments to LaTeX quotes
    def repl(m: re.Match) -> str:
        inner = m.group(1)
        return '``' + inner + "''"

    return DOUBLE_QUOTE_PATTERN.sub(repl, text)


def process_file(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    new = normalize_text(text)
    if new != text:
        bak = path.with_suffix(path.suffix + '.bak')
        bak.write_text(text, encoding='utf-8')
        path.write_text(new, encoding='utf-8')
        return True
    return False


def find_tex_files(root: Path):
    for p in root.rglob('*.tex'):
        yield p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.', help='Repository root path')
    args = parser.parse_args()
    root = Path(args.root).resolve()

    modified = []
    for f in find_tex_files(root):
        try:
            if process_file(f):
                modified.append(str(f.relative_to(root)))
        except Exception as e:
            print(f"Error processing {f}: {e}")

    if modified:
        print('Modified files:')
        for m in modified:
            print(' -', m)
    else:
        print('No changes made.')


if __name__ == '__main__':
    main()
