"""Build a blog with two Blog objects.

Run it from your project folder:

    python example.py
"""

from essayist import Blog, Jinja2Template

# 1. The posts. One Blog object for one folder.
posts = Blog(
    source="markdown/posts",
    output="public/posts",
    name="My Blog",
    url="https://example.com",
    filters=["gallery"],  # a filter that comes with essayist
    filter_dir="filters",  # your own *.lua filters are found here
    pandoc_args=["--mathml", "--toc", "--shift-heading-level-by=1"],
    css="style-note.css",
)
posts.build()
posts.build_index(title="All Posts")
posts.build_rss()

# 2. The home page. One Blog object for one file.
home = Blog(
    source="markdown/index.md",
    output="public/index.html",
    template=Jinja2Template("home.html"),
    pandoc_args=["--mathml"],
)
home.build()
