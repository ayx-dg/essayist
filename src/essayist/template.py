"""Page templates.

A template turns data into one finished page. essayist ships two kinds:

- :class:`Jinja2Template` fills in a Jinja2 file like ``post.html``
- :class:`PandocTemplate` runs Markdown through Pandoc with a Pandoc
  template file

Both answer to the same call: ``template.render(**data)``.
"""

from __future__ import annotations

from .core import pandoc, templates_folder


class Template:
    """Base class for every template. Subclasses write :meth:`render`."""

    def render(self, **data) -> str:
        """Turn ``data`` into one page and return it as text."""
        raise NotImplementedError


class Jinja2Template(Template):
    """A Jinja2 file inside a template folder.

    ``Jinja2Template("post.html")`` uses the file that ships with essayist.
    ``Jinja2Template("post.html", dir="templates")`` uses your own folder.
    """

    def __init__(self, name: str, dir: str | None = None) -> None:
        from jinja2 import Environment, FileSystemLoader

        self.name = name
        self.dir = dir or templates_folder()
        self.env = Environment(loader=FileSystemLoader(self.dir))

    def render(self, **data) -> str:
        return self.env.get_template(self.name).render(**data)


class PandocTemplate(Template):
    """A Pandoc template file.

    ``body`` is the Markdown text. Every other key becomes a Pandoc variable
    (``-V key:value``). With no file, Pandoc uses its own default template.
    """

    def __init__(self, path: str | None = None, pandoc_args: list[str] | None = None) -> None:
        self.path = path
        self.pandoc_args = list(pandoc_args or [])

    def render(self, **data) -> str:
        data = dict(data)
        body = data.pop("body", "")
        flags = list(self.pandoc_args)
        for key, value in data.items():
            if value is not None:
                flags += ["-V", f"{key}:{value}"]
        if self.path:
            flags.append(f"--template={self.path}")
        return pandoc(body, flags)
