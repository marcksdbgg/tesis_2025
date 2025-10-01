#!/usr/bin/env python3
"""Generate a Markdown file that documents the repository tree and file contents.

The script discovers files via `git ls-files --exclude-standard --others --cached`
so anything covered by .gitignore is skipped automatically. The resulting
Markdown includes a directory tree and the complete text content for each file.
Binary files are detected heuristically and noted instead of being dumped.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List


def get_repo_root(script_path: Path) -> Path:
    """Return the repository root, falling back to the script directory."""
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
        )
        return Path(output.decode().strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return script_path.parent


def gather_repo_files(root: Path) -> List[Path]:
    """Return repo files that are not ignored according to git."""
    try:
        output = subprocess.check_output(
            ["git", "ls-files", "--exclude-standard", "--others", "--cached"],
            cwd=root,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        # If git is not available or fails, fall back to walking the filesystem.
        sys.stderr.write(f"Notice: git unavailable or failed ({exc}). Falling back to filesystem walk.\n")
        return gather_files_by_walk(root)
    raw_paths = [line.strip() for line in output.decode().splitlines() if line.strip()]
    resolved = []
    missing = []
    for p in raw_paths:
        full = root / p
        if full.exists():
            resolved.append(full)
        else:
            missing.append(p)
    if missing:
        # Don't fail; just warn the user which git-tracked paths were not found on disk.
        sys.stderr.write(
            "Warning: git reported paths that do not exist on disk. They will be skipped:\n"
        )
        for m in missing[:20]:
            sys.stderr.write(f"  - {m}\n")
        if len(missing) > 20:
            sys.stderr.write(f"  ...and {len(missing)-20} more\n")
    return resolved


def load_gitignore_patterns(root: Path) -> List[str]:
    """Return simple glob patterns from .gitignore in repo root (fallback).

    This is intentionally small: it ignores comments/blank lines and returns
    raw patterns. This is not a fully correct .gitignore parser but works for
    common cases (simple globs, directory patterns ending with '/').
    """
    patterns: List[str] = []
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return patterns
    try:
        for line in gitignore.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            patterns.append(s)
    except Exception:
        pass
    return patterns


def gather_files_by_walk(root: Path) -> List[Path]:
    """Collect files by walking the filesystem, excluding simple .gitignore patterns.

    This fallback keeps the script dependency-free while being reasonably
    accurate for common ignore patterns.
    """
    patterns = load_gitignore_patterns(root)
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            skip = False
            for pat in patterns:
                # directory pattern
                if pat.endswith("/"):
                    if rel.startswith(pat.rstrip("/")):
                        skip = True
                        break
                else:
                    # use simple fnmatch on posix path
                    from fnmatch import fnmatch

                    if fnmatch(rel, pat) or fnmatch(p.name, pat):
                        skip = True
                        break
            if not skip:
                files.append(p)
    return files


def build_tree(paths: Iterable[Path], root: Path) -> Dict[str, dict]:
    """Construct a nested dict representing the directory tree."""
    tree: Dict[str, dict] = {}
    for path in paths:
        relative_parts = list(path.relative_to(root).parts)
        cursor = tree
        for part in relative_parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor.setdefault("__files__", []).append(relative_parts[-1])
    return tree


def render_tree(tree: Dict[str, dict], prefix: str = "") -> List[str]:
    """Render the nested dict into a list of tree lines."""
    lines: List[str] = []
    entries = []
    directories = sorted([k for k in tree.keys() if k != "__files__"])
    for directory in directories:
        entries.append((directory, True))
    files = tree.get("__files__", [])
    for filename in sorted(files):
        entries.append((filename, False))

    for index, (name, is_dir) in enumerate(entries):
        connector = "└──" if index == len(entries) - 1 else "├──"
        lines.append(f"{prefix}{connector} {name}")
        if is_dir:
            next_prefix = f"{prefix}    " if index == len(entries) - 1 else f"{prefix}│   "
            sub_tree = tree[name]
            lines.extend(render_tree(sub_tree, next_prefix))
    return lines


def detect_binary(data: bytes) -> bool:
    """Heuristic to determine whether a byte payload is binary."""
    if not data:
        return False
    if b"\0" in data:
        return True
    printable = {7, 8, 9, 10, 12, 13, 27}
    printable.update(range(0x20, 0x7F))
    printable_count = sum(1 for byte in data if byte in printable)
    ratio = printable_count / len(data)
    return ratio < 0.7


def read_file_for_markdown(path: Path) -> str:
    """Return Markdown-safe representation of the file contents."""
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return "[missing file: skipped]"
    except OSError as e:
        return f"[error reading file: {e}]"
    if detect_binary(data):
        size = len(data)
        return f"[binary file omitted – {size} bytes]"
    text = data.decode("utf-8", errors="replace")
    return text.rstrip() + "\n"


def create_markdown(root: Path, files: List[Path], output_path: Path) -> str:
    header = [f"# {root.name}", "", "Generated by generate_repo_markdown.py.", ""]
    # Force-include .github/copilot-instructions.md in the tree when present on disk,
    # but do NOT include its full text in the "Contenido de archivos" section.
    ci = root / ".github" / "copilot-instructions.md"
    files_for_tree = list(files)
    if ci.exists() and ci not in files_for_tree:
        files_for_tree = files_for_tree + [ci]
    # Exclude the output file itself from both lists
    files_for_tree = [f for f in files_for_tree if f.resolve() != output_path.resolve()]
    # For content, exclude the copilot instructions file explicitly
    files_for_content = [f for f in files_for_tree if f.resolve() != ci.resolve()]
    tree = build_tree(files_for_tree, root)
    tree_lines = ["## Estructura", "", "```", "."]
    tree_lines.extend(render_tree(tree))
    tree_lines.append("```")
    tree_lines.append("")

    content_sections: List[str] = ["## Contenido de archivos", ""]
    for file_path in sorted(files_for_content):
        relative = file_path.relative_to(root).as_posix()
        # Explicitly skip the copilot instructions file from content embedding
        if relative == ".github/copilot-instructions.md":
            continue
        content_sections.append(f"### `{relative}`")
        content_sections.append("")
        body = read_file_for_markdown(file_path)
        fence_lang = relative.split(".")[-1] if "." in relative else "text"
        content_sections.append(f"```{fence_lang}")
        content_sections.append(body)
        if not body.endswith("\n"):
            content_sections.append("")
        content_sections.append("```")
        content_sections.append("")

    return "\n".join(header + tree_lines + content_sections)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate repository Markdown dump")
    parser.add_argument(
        "--output",
        default="codebase.md",
        help="Relative path (from repo root) for the generated Markdown file.",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Optional path to repository root (fallback when git fails).",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> None:
    script_path = Path(__file__).resolve()
    args = parse_args(argv)
    if args.root:
        root = Path(args.root).resolve()
        sys.stderr.write(f"Using provided root: {root}\n")
    else:
        root = get_repo_root(script_path)
    output_path = (root / args.output).resolve()
    # gather files (git-based primary, filesystem fallback handled inside)
    files = gather_repo_files(root)
    markdown = create_markdown(root, files, output_path)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Markdown written to {output_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
