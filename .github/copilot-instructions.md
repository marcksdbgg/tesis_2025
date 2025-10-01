Overview

This repository is a LaTeX thesis template/project (UCSP thesis). The root document is `Tesis.tex` which pulls front matter from `frontmatter/`, chapters from `chapters/`, styles from `sty/`, figures from `figs/`, and bibliography from `bibliography/Bibliog.bib`.

What an AI coding agent should know (concise, actionable)

- Build target: produce a final PDF from `Tesis.tex`. Use a LaTeX engine that writes auxiliary files alongside the main document (this project expects standard pdflatex/xelatex workflows).
  - Typical developer command: run latexmk or (pdflatex -> bibtex -> pdflatex -> pdflatex). The repo already contains many auxiliary files in the root (`.aux`, `.bbl`, `.blg`, `.fdb_latexmk`, `.fls`, etc.), so run in the repository root to keep paths consistent.

- Key files and purpose:
  - `Tesis.tex` — main document and composition order. Edit this to add/remove `\input{...}` chapter includes.
  - `sty/tesis.sty` — custom macros and formatting (title page, advisor, dedications, headers). When changing document metadata, prefer editing `Tesis.tex` preamble commands (`\title{}`, `\author{}`, `\advisor{}`, `\dedicado{}`, `\date{}`) rather than changing the style file unless fixing styling bugs.
  - `frontmatter/` — contains `Abstract.tex`, `Agradecimientos.tex`, `Resumen.tex`, `abreviaturas.tex`. These are included in `Tesis.tex` with `\input{frontmatter/...}`.
  - `chapters/` — each chapter (e.g., `Cap_1.tex`, `Cap_2.tex`) is a standalone TeX fragment. Follow the existing labeling, figure, and citation patterns (label figures with `\label{Fig:...}` and cite with `\cite{...}`).
  - `bibliography/Bibliog.bib` — BibTeX file. The document sets `\bibliographystyle{apalike}` and uses `\bibliography{bibliography/Bibliog}`.
  - `figs/` — image assets referenced by `\includegraphics{...}`; style assumes `figs/UCSP_black.pdf` exists for cover. Maintain relative paths.

- Conventions and patterns discovered in codebase (explicit)
  - Document class: `book` with `a4paper,openany,12pt` set by `Tesis.tex`.
  - Preamble macro usage: metadata are provided via custom commands defined in `sty/tesis.sty` (e.g., `\advisor{...}` becomes `\@orientador` in the style). Do not remove these macros in `Tesis.tex` — supply values instead.
  - Frontmatter inclusion: `\input{frontmatter/...}` is used rather than `\include{...}` so auxiliary files are written into the same build directory. Respect this inclusion pattern when adding new frontmatter pieces.
  - Bibliography workflow: BibTeX + apalike style; run bibtex (or let latexmk handle it).
  - Figure placeholders in template: chapters contain `\fbox{\parbox...}` placeholders — replace them with actual `\includegraphics` and keep `\label{Fig:...}` and `\caption{}` patterns.

- Safe edit rules (to avoid breaking builds)
  - Preserve `\input{...}` order in `Tesis.tex` — changing order changes page numbering and table of contents.
  - Don't rename `sty/tesis.sty` or `sty/fancyhdr.sty` without updating `Tesis.tex` preamble; prefer editing style content only for formatting fixes.
  - Keep `\bibliographystyle{apalike}` unless the user asks to change citation style; changing bib style may require updating `.bib` entries.
  - When adding images, place them under `figs/` and reference with relative path `figs/...`.

- Example tasks and how to perform them (concrete)
  - Add a new chapter file: create `chapters/Cap_5.tex` with `\chapter{Title}\label{chap:...}` and `\input{chapters/Cap_5}` into `Tesis.tex` before the bibliography.
  - Fix a broken figure: open chapter with placeholder, replace placeholder box with:

    \begin{figure}[ht]
    \centering
    \includegraphics[width=0.8\textwidth]{figs/myfigure.pdf}
    \caption{Caption text}
    \label{Fig:MyFigure}
    \end{figure}

  - Add an advisor or change metadata: edit `Tesis.tex` preamble and set `\advisor{Dr. Name}` and `\date{Arequipa, Octubre 2025}`.
  - Update bibliography entry: edit `bibliography/Bibliog.bib`, then re-run the full LaTeX build sequence.

- Debugging hints
  - Common LaTeX errors in this repo derive from missing figures under `figs/`, missing `\title`/`\author`/`\dedicado` values (the style file raises ClassError), or stray `\usepackage{}` left empty (note `Tesis.tex` comments about an empty package that caused an error previously). Check the .log and .blg files in root.
  - If auxiliary files are stale, clean the root (remove `.aux`, `.toc`, `.bbl`, `.blg`, `.fdb_latexmk`, `.fls`, `.lof`, `.lot`) and re-run latexmk or the sequence (pdflatex -> bibtex -> pdflatex -> pdflatex).

- Integration and external tools
  - Supported build tools: pdflatex, xelatex, latexmk, bibtex. The repository shows artifacts from latexmk (e.g., `.fdb_latexmk`).
  - No CI configuration found — if creating automated builds, run latexmk in the repository root and commit only source files; ignore compiled artifacts.

- Files to reference when coding or generating content
  - `Tesis.tex`, `sty/tesis.sty`, `frontmatter/_README.txt`, `frontmatter/abreviaturas.tex`, `chapters/Cap_2.tex` (example of structure), `bibliography/Bibliog.bib`.

If anything here is unclear or you'd like me to include build commands for Windows PowerShell (latexmk/pdflatex sequences), tell me and I'll add them. Please review this draft and point out any missing repo-specific conventions to include.