# essayist

A lightweight static site generator for Markdown blogs, powered by
[Pandoc](https://pandoc.org/) and [Jinja2](https://jinja.palletsprojects.com/).

Convert a directory of Markdown posts (with YAML front matter) into a styled
HTML blog with an index page and an RSS feed.

Both halves of the pipeline are pluggable. Swap the bundled Jinja2 templates for
your own with `template_dir`, and extend the Pandoc step with any
[Pandoc filter](https://pandoc.org/filters.html): drop `*.lua` files into a
`filters/` folder to have them picked up automatically, or name them — bundled
or local — in `filters`.

## Requirements

- Python ≥ 3.10
- [Pandoc](https://pandoc.org/installing.html) available on `PATH`

## Install

```bash
pip install essayist
```

Or install from source:

```bash
git clone https://github.com/ayx-dg/essayist
cd essayist
pip install -e .
```

## Quick start

### 1. Set up your Markdown directory

Create a `markdown/posts/` folder and add `.md` files with YAML front matter:

```markdown
---
title: My First Post
date: 2025-01-15
tags: [intro, welcome]
publish: public
---

# My First Post

Here is the body of my post, written in Markdown.
```

### 2. Create a config file

Save this as `essayist.toml` in your project root:

```toml
markdown_dir = "markdown/posts"
post_dir     = "public/posts"
# template_dir = "templates"        # omit to use the bundled templates
blogname     = "My Blog"
site_url     = "https://example.com"
panargs      = ["--mathml", "--toc", "--shift-heading-level-by=1"]

build_index = true
index_title = "All Posts"
build_rss   = true
home_md      = "markdown/index.md"
home_output  = "public/index.html"
style_css    = "style-note.css"
```

### 3. Build

```bash
essayist build
```

Output will be written to `public/`. Open `public/index.html` in a browser.

## Live demo

A demo blog built with `essayist build` is deployed at
<https://essayist-demo.netlify.app>. It exercises the features described below:
MathML maths, a Pandoc table of contents, the `gallery.lua` image gallery,
`prev`/`next` post navigation, an index page and an RSS feed.

| Page | URL |
|------|-----|
| Home | <https://essayist-demo.netlify.app/> |
| Post index | <https://essayist-demo.netlify.app/posts/> |
| RSS feed | <https://essayist-demo.netlify.app/posts/rss.xml> |

The demo contains one `draft` post (never rendered) and one `unlisted` post
(served in the feed, hidden from the index), so the visibility rules under
[Post front matter](#post-front-matter) can be checked against the live site.

## CLI usage

```
essayist build [--config essayist.toml] [OPTIONS]
essayist version
```

CLI flags override the corresponding config-file values:

| Flag             | Description                        |
|------------------|------------------------------------|
| `-c, --config`   | Path to TOML config (default: `essayist.toml`) |
| `--markdown-dir` | Directory with Markdown posts      |
| `--post-dir`     | Output directory for rendered HTML |
| `--template-dir` | Custom Jinja2 template directory   |
| `--blogname`     | Blog name for page titles          |
| `--site-url`     | Base URL for RSS feeds             |
| `--filter`       | Pandoc filter (repeatable)         |
| `--filter-dir`   | Directory scanned for `*.lua` filters |
| `--gallery`      | Shorthand for `--filter gallery`   |

## Python API

```python
from essayist import Blog, Config, build_site

# High-level: load config and build everything
cfg = Config(
    markdown_dir="markdown/posts",
    post_dir="public/posts",
    blogname="My Blog",
    site_url="https://example.com",
    panargs=["--mathml", "--toc"],
)
build_site(cfg)

# Or use the Blog class directly
blog = Blog(
    markdown_dir="markdown/posts",
    post_dir="public/posts",
    template_dir="path/to/custom/templates",  # None → use bundled defaults
)
blog.update_data()
blog.build_posts()
blog.build_index()
blog.build_rss("public/posts/rss.xml")
```

## Config reference

All keys in `essayist.toml`:

| Key               | Type        | Default           | Description                                        |
|-------------------|-------------|-------------------|----------------------------------------------------|
| `markdown_dir`    | string      | `markdown/posts`  | Directory with `.md` post files                    |
| `post_dir`        | string      | `public/posts`    | Output directory for rendered HTML                 |
| `template_dir`    | string/null | `null` (bundled)  | Jinja2 template directory (`null` = use defaults)  |
| `blogname`        | string      | `""`              | Blog name appended to page titles                  |
| `google_group_id` | string      | `""`              | Enables the email-comment block in posts           |
| `site_url`        | string      | `https://example.com` | Base URL used in RSS `<link>` tags            |
| `panargs`         | array       | `[]`              | Extra flags passed to Pandoc                       |
| `filters`         | array       | `[]`              | Pandoc filters: path, name in `filter_dir`, or bundled name |
| `filter_dir`      | string      | `filters`         | Directory scanned for `*.lua` Pandoc filters       |
| `gallery`         | bool        | `false`           | Shorthand for `filters = ["gallery"]`              |
| `build_index`     | bool        | `true`            | Generate the post-list index page                  |
| `index_title`     | string      | `Index`           | Title for the index page                           |
| `build_rss`       | bool        | `true`            | Generate an RSS 2.0 feed                           |
| `rss_path`        | string/null | `<post_dir>/rss.xml` | Where to write the RSS feed                   |
| `home_md`         | string/null | `null`            | Markdown file for the home page (if any)           |
| `home_template`   | string      | `home.html`       | Template used to render the home page              |
| `home_output`     | string      | `public/index.html` | Output path for the home page                   |
| `style_css`       | string/null | `null`            | CSS file copied next to rendered posts             |
| `data_path`       | string      | `data.json`       | Path for the auto-generated post index             |

## Post front matter

Every Markdown post should start with a YAML front matter block:

```yaml
---
title: Post Title          # required
date: 2025-01-15           # used for ordering in index and RSS
tags: [tag1, tag2]         # optional, passed to templates
publish: public            # public | draft | unlisted
maillist_title: ...        # optional, email comment link
google_group_link: ...     # optional, link to mail thread
---
```

**Visibility rules:**

- `public` — appears in index and RSS
- `draft` — skipped entirely (existing output is cleaned up)
- `unlisted` — appears in RSS but not in the index

## Templates

The package ships with five default templates:

| Template     | Purpose                         |
|-------------|---------------------------------|
| `header.html` | `<head>` block with CSS and RSS link |
| `footer.html` | Footer with RSS link           |
| `post.html`   | Single blog post page          |
| `index.html`  | Post listing (all public posts)|
| `home.html`   | Home / landing page             |

Set `template_dir` in your config (or pass `--template-dir`) to override them:

```toml
template_dir = "templates"
```

```bash
essayist build --template-dir templates
```

The lookup is a **plain replacement, not an overlay**: once `template_dir` is
set the bundled templates are no longer searched, so the directory has to
contain every template the build needs (`post.html`, `index.html`,
`header.html`, `footer.html`, plus `home.html` if you render a home page).
Start by copying the bundled ones:

```bash
python -c "from essayist import Blog; print(Blog._bundled_templates())"
```

The templates use [Jinja2](https://jinja2.palletsprojects.com/) syntax and
receive variables like `heading`, `paragraphs`, `title`, `prev_post`,
`next_post`, etc.

## Pandoc filters

Any [Pandoc filter](https://pandoc.org/filters.html) can be used. Filters are
collected from three sources, deduplicated and applied in this order:

1. `gallery = true` — shorthand for the bundled `gallery` filter
2. `filters = [...]` — explicit entries
3. every `*.lua` file inside `filter_dir`

```toml
filter_dir = "filters"                 # scanned for *.lua, in name order
filters    = ["gallery", "uppercase"]  # path, file in filter_dir, or bundled
```

Each `filters` entry is resolved in turn as:

1. a path (absolute, or relative to the working directory)
2. a file inside `filter_dir`, with or without the `.lua` suffix
3. a filter bundled with essayist

`.lua` files are passed to Pandoc with `--lua-filter`; anything else is treated
as a JSON-filter executable and passed with `--filter`.

On the CLI, `--filter` is repeatable and `--filter-dir` overrides the config:

```bash
essayist build --filter gallery --filter ./filters/uppercase.lua
```

### Bundled filters

| Filter       | Description                              |
|-------------|------------------------------------------|
| `gallery.lua` | Groups images in a paragraph into a responsive flex gallery |

Enable one with `filters = ["gallery"]` (or the `--gallery` / `--filter gallery`
shorthand).

## Development

```bash
pip install -e ".[test]"
pytest
```

## License

MIT
