# essayist

essayist turns Markdown files into a blog.

- [Pandoc](https://pandoc.org/) reads the Markdown.
- A template writes the HTML page.

## Install

You need:

- Python 3.10 or newer
- Pandoc on your `PATH` — see <https://pandoc.org/installing.html>

```bash
pip install essayist
```

## Use

```python
from essayist import Blog

posts = Blog(source="markdown/posts", output="public/posts")
posts.build()
```

`build()` reads every `.md` file in `markdown/posts`. It writes
`public/posts/1.html`, `public/posts/2.html`, and so on.

Files are numbered by date. The oldest post is `1.html`.

## Two Blog objects

One Blog object does one job. It reads one source and writes one output.

The normal setup is two objects:

| Object | Reads | Writes |
|--------|-------|--------|
| posts | `markdown/posts/` | `public/posts/1.html`, `2.html`, ... |
| home | `markdown/index.md` | `public/index.html` |

```python
from essayist import Blog, Jinja2Template

# 1. the posts
posts = Blog(
    source="markdown/posts",
    output="public/posts",
    name="My Blog",
    url="https://example.com",
    pandoc_args=["--mathml", "--toc"],
)
posts.build()
posts.build_index(title="All Posts")
posts.build_rss()

# 2. the home page
home = Blog(
    source="markdown/index.md",
    output="public/index.html",
    template=Jinja2Template("home.html"),
)
home.build()
```

Give a **folder** as `source` to build many pages. Give a **file** to build one
page.

A full example is in [`example.py`](example.py).

## Blog settings

| Setting | Default | What it does |
|---------|---------|--------------|
| `source` | — | Markdown file or folder to read |
| `output` | — | HTML file or folder to write |
| `template` | `post.html` | Template that writes the page |
| `filters` | `[]` | Pandoc filters |
| `filter_dir` | none | Folder scanned for `*.lua` filters |
| `pandoc_args` | `[]` | Extra Pandoc flags, like `["--mathml"]` |
| `name` | `""` | Blog name, added to page titles |
| `url` | `https://example.com` | Site address used in the feed |
| `group_id` | `""` | Google group name for mail comments |
| `css` | none | CSS file, copied next to the pages |

## Blog methods

| Call | What it writes |
|------|----------------|
| `blog.build()` | one page per source file |
| `blog.build_index()` | `index.html` — a list of public posts |
| `blog.build_rss()` | `rss.xml` — the feed |
| `blog.scan()` | reads the source files and returns the list |

`build_index()` and `build_rss()` have options:

```python
blog.build_index(path="public/posts/index.html", title="All Posts")
blog.build_rss(path="public/posts/rss.xml")
```

## Command line

```bash
essayist build markdown/posts public/posts
essayist version
```

A folder source also writes `index.html` and `rss.xml`.

| Flag | What it does |
|------|--------------|
| `--template` | Jinja2 template file name |
| `--template-dir` | Folder with your Jinja2 templates |
| `--filter` | Pandoc filter. Repeatable |
| `--filter-dir` | Folder scanned for `*.lua` filters |
| `--name` | Blog name |
| `--url` | Site address |
| `--group-id` | Google group for mail comments |
| `--css` | CSS file to copy |
| `--pandoc-arg` | Extra Pandoc flag, like `--pandoc-arg=--mathml`. Repeatable |
| `--no-index` | Do not write `index.html` |
| `--no-rss` | Do not write `rss.xml` |

## Markdown files

Every file starts with a `---` block:

```yaml
---
title: My Post        # needed
date: 2025-01-15      # sets the order
tags: [a, b]          # optional
publish: public       # public | draft | unlisted
maillist_title: ...   # optional, mail comment link
google_group_link: .. # optional, link to the mail thread
---
```

| `publish` | Page written | In the list | In the feed |
|-----------|--------------|-------------|-------------|
| `public` | yes | yes | yes |
| `draft` | no | no | no |
| `unlisted` | yes | no | yes |

## Templates

A template turns data into one page. essayist has two kinds.

| Class | Reads | Use it for |
|-------|-------|-----------|
| `Jinja2Template` | a Jinja2 file | normal pages |
| `PandocTemplate` | a Pandoc template file | pages built by Pandoc |

Both answer the same call:

```python
html = template.render(title="Hi", body="text")
```

```python
from essayist import Jinja2Template, PandocTemplate

Jinja2Template("post.html")                    # file inside essayist
Jinja2Template("post.html", dir="templates")   # your own file
PandocTemplate()                               # Pandoc default template
PandocTemplate(path="page.html")               # your Pandoc template
```

With `PandocTemplate`, `body` is the Markdown. Every other key becomes a Pandoc
variable (`-V key:value`).

These Jinja2 files ship with essayist:

| File | Use |
|------|-----|
| `header.html` | the `<head>` block |
| `footer.html` | the page footer |
| `post.html` | one post |
| `index.html` | the list page |
| `home.html` | the home page |

To use your own files, set `template=` **and** copy all five files. essayist
does not fall back to the ones it comes with. Find them with:

```bash
python -c "from essayist.core import templates_folder; print(templates_folder())"
```

## Pandoc filters

A filter changes the page while Pandoc reads it.

```python
Blog(..., filters=["gallery"], filter_dir="filters")
```

Three ways to name one:

| Way | Example | Means |
|-----|---------|-------|
| path | `filters/up.lua` | that file |
| name in `filter_dir` | `up` | `filters/up.lua` |
| name with no `.lua` | `gallery` | a filter that comes with essayist |

essayist comes with its own filters. You write their names with no `.lua`
ending. To see them:

```bash
python -c "from essayist import filters; print(filters.included())"
# ['gallery.lua']
```

| Filter that comes with essayist | What it does |
|---------------------------------|--------------|
| `gallery` | puts the images of one paragraph in a row |

Every `*.lua` file in `filter_dir` is used too, in name order.

`.lua` files run inside Pandoc (`--lua-filter`). Other files run as a program
(`--filter`). `filter_dir` only picks up `*.lua` files.

To add a filter to essayist itself, put a `*.lua` file in
`src/essayist/filters/`.

## Live demo

A demo blog is at <https://essayist-demo.netlify.app>.

| Page | Address |
|------|---------|
| Home | <https://essayist-demo.netlify.app/> |
| Post list | <https://essayist-demo.netlify.app/posts/> |
| Feed | <https://essayist-demo.netlify.app/posts/rss.xml> |

It has one `draft` post and one `unlisted` post, so you can check the table
above on a real site.

## Development

```bash
pip install -e ".[test]"
pytest
```

## License

MIT
