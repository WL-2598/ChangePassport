"""Output renderers. Rendering never re-fetches or changes facts."""

from changepassport.renderers.json import dump_json
from changepassport.renderers.markdown import render_markdown

__all__ = ["dump_json", "render_markdown"]
