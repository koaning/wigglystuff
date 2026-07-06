---
name: explain-diff-html
description: Use when the user asks for a rich explanation of a code change, diff, branch, or PR and wants an interactive HTML document as output
---

# Explain Diff (HTML)

Produce a self-contained HTML file that explains a code change — a diff, a branch, or a PR — with the clarity and flow of Martin Kleppmann. The reader should come away with genuine understanding, not just a summary.

## Output Format

Write a single self-contained HTML file (no external dependencies) to `/tmp/` with a filename starting with today's date: `/tmp/YYYY-MM-DD-explanation-<slug>.html`.

The file must include embedded CSS and JavaScript for interactive features. No external stylesheets or scripts.

## Required Sections

The HTML page is one long page with a table of contents at the top.

### 1. Background

Two parts:

**Deep background (skippable).** Explain the existing system broadly. Assume a capable engineer who may not know this particular codebase. Context from surrounding modules, the problem domain, and relevant history.

**Narrow background.** Focus on the specific area the change touches. What was the state of the code before this diff? What pain points or limitations existed?

### 2. Intuition

The core idea of the change, explained with concrete examples and toy data. Use HTML-based diagrams throughout — never ASCII art.

Good diagram types:
- Simplified UI mockups (use HTML/CSS elements)
- System / data-flow diagrams showing how data moves between components
- Before/after comparisons (use a two-column grid)
- Annotated code snippets that highlight what changes

Use **callout boxes** for key concepts, definitions, and important edge cases. Mark them visually distinct from the main text.

### 3. Code Walkthrough

Group changes in a logical order (not file-by-file or line-by-line). For each group:
- What was the problem / motivation
- What the new code does
- How it connects to the rest of the change

Use `<pre>` tags for code blocks. Every `<pre>` element must have `white-space: pre-wrap` or `white-space: pre` in its CSS — scan the output to confirm this before saving.

### 4. Quiz

Five interactive multiple-choice questions that test genuine understanding of the diff. Each question:
- Has 4 options (A/B/C/D)
- Shows correct/incorrect feedback on click (use JavaScript)
- Includes an explanation of the correct answer
- Is tough enough that you need to understand the substance to answer, but not a gotcha

## Styling Rules

- Responsive design — works on phone and desktop
- Light + dark theme support via `prefers-color-scheme`
- Use system font stack: `system-ui, -apple-system, sans-serif`
- Callout boxes for definitions, edge cases, and "why this matters"
- Smooth scroll between sections
- Table of contents with anchor links
- Use `white-space: pre-wrap` on all `<pre>` code blocks (verify before saving)
- No emoji

## Tone

Write in **classic style** — as if you are showing the reader something they can see for themselves. Be direct, concrete, and confident. Use the flow and clarity of Martin Kleppmann: start with what the reader already knows, bridge to what's new, and make each step feel inevitable.

## Workflow

1. Explore the diff/branch/PR thoroughly — `git diff`, `git log`, surrounding files, related tests
2. Understand the motivation — what bug or feature drove this?
3. Plan the explanation — what background is needed? What's the core intuition? How to group the code changes?
4. Draft the HTML in one shot — all four sections, with real content
5. Scan for code blocks and confirm `white-space` is set on every `<pre>`
6. Open the file in browser to verify it renders correctly and all JavaScript works
7. Tell the user the file path

## Red Flags

- No ASCII diagrams — always use HTML/CSS
- No external dependencies — everything in one file
- Don't describe every line of the diff — group by concept
- Don't skip the quiz — it's the most important section for verifying understanding
- Don't use emoji in the output HTML
