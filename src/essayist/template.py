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
    ``Jinja2Template("./template")`` uses the directory as template folder with default post.html.
    """

    def __init__(self, name: str, dir: str | None = None) -> None:
        from jinja2 import Environment, FileSystemLoader
        import os

        # Resolve relative paths against CWD so that
        # Jinja2Template("./template/home.html") works from the project root.
        resolved = os.path.abspath(name)

        if os.path.isdir(resolved):
            self.dir = resolved
            self.name = "post.html"
        elif os.path.isfile(resolved):
            self.dir = os.path.dirname(resolved)
            self.name = os.path.basename(resolved)
        else:
            # Bare template name like "post.html" — look in explicit dir or bundled defaults
            self.name = name
            self.dir = os.path.abspath(dir) if dir else templates_folder()

        self.env = Environment(loader=FileSystemLoader(self.dir))

    def render(self, **data) -> str:
        return self.env.get_template(self.name).render(**data)


class PandocTemplate(Template):
    """A Pandoc template file.

    ``body`` is the Markdown text. Every other key becomes a Pandoc variable.
    Simple values (str/int/bool) use ``-V key:value``.
    Complex values (list/dict) use ``--metadata-file`` so pandoc can iterate
    over them in ``$for(...)$$`` template loops.
    With no file, Pandoc uses its own default template.
    """

    def __init__(self, path: str | None = None, pandoc_args: list[str] | None = None) -> None:
        self.path = path
        self.pandoc_args = list(pandoc_args or [])

    def render(self, **data) -> str:
        import os
        import tempfile

        import yaml

        data = dict(data)
        body = data.pop("body", "")
        flags = list(self.pandoc_args)

        simple: dict[str, str] = {}
        complex_data: dict = {}
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, (str, int, float, bool)):
                simple[key] = str(value)
            else:
                complex_data[key] = value

        for key, value in simple.items():
            flags += ["-V", f"{key}:{value}"]

        meta_file = None
        if complex_data:
            meta_file = tempfile.NamedTemporaryFile(
                "w", suffix=".yaml", delete=False, encoding="utf-8"
            )
            yaml.dump(complex_data, meta_file, allow_unicode=True, default_flow_style=False)
            meta_file.close()
            flags.append(f"--metadata-file={meta_file.name}")

        if self.path:
            flags.append(f"--template={self.path}")

        try:
            return pandoc(body, flags)
        finally:
            if meta_file:
                os.remove(meta_file.name)
