# AGENTS.md

## Project

Python package: Pandoc + Jinja2 static site generator for Markdown blogs.
Source lives in `src/essayist/`. Tests in `tests/`.

## Quick commands

```bash
pip install -e ".[test]"   # install with test deps
pytest                      # run all tests
pytest tests/test_blog.py   # run blog tests only
```

## External dependency

**Pandoc must be on `PATH`**. Tests will fail without it. CI installs it via `pandoc/actions/setup@v1`.

## Package structure

- `config.py` — `Config` dataclass, path resolution (`resolve()` makes relative paths absolute)
- `core.py` — `Blog` class: metadata parsing, pandoc rendering, post/index/RSS building
- `builder.py` — `build_site()` orchestrator, entry point for full builds
- `cli.py` — CLI entry point (`essayist build` / `essayist version`)
- `templates/*.html` — bundled Jinja2 templates (post, index, home, header, footer)
- `filters/*.lua` — pandoc Lua filters (gallery)

## Templates

essayist supports two template engines:

- **Jinja2Template** — for post pages (`{{ variable }}`, `{% for %}`, `{% include %}`)
- **PandocTemplate** — for index/home pages (`$variable$`, `$for()$...$endfor$`, `$partial()$`)

Pandoc templates use `$name()$` syntax for partials (not `${ name() }$`). Partials
are files in the same directory as the main template. Built-in pandoc partials
like `$styles.html()$` are also available.

`PandocTemplate.render()` accepts both `body` and `paragraphs` as the content variable.
Complex data (lists, dicts) is passed via `--metadata-file` as YAML.

## Testing

- Fixtures live in `tests/sample/markdown/`. The `site` fixture copies them to `tmp_path`.
- All output goes to pytest temp dirs — safe to run repeatedly.
- `test_blog.py` has full end-to-end build tests that exercise pandoc.
- Tests are synchronous, no services needed beyond pandoc.

## Config quirks

- Config file is TOML. Accepts `[tool.essayist]` table or bare top-level keys.
- `Config.resolve(base)` makes relative paths absolute — call it when loading from a file.
- CLI flags override config-file values.
- `gallery = true` auto-injects `--lua-filter=<bundled gallery.lua>` into panargs.
- Post visibility: `public` (index+RSS), `unlisted` (RSS only), `draft` (skipped, old output cleaned).

## Style

- No linter/formatter configured. CI only runs pytest.
- Python ≥ 3.10. Uses `from __future__ import annotations` throughout.
- Type hints are present but not strict (no mypy in CI).

## CI

- `ci.yml`: pytest on Python 3.10/3.11/3.12, ubuntu-latest, pandoc installed.
- `essayist.yml`: publish to PyPI on `v*` tags via trusted publishing.
