"""Render Jinja2 templates with a BundleSpec.

Templates are shipped as package data under `casmd/bundle/templates/`.
"""
from __future__ import annotations
from dataclasses import asdict
from importlib import resources
from typing import Any

from jinja2 import Environment, BaseLoader, TemplateNotFound

from casmd.bundle.spec import BundleSpec


_TEMPLATE_NAMES = (
    "step1_minimization.mdp",
    "step2_nvt.mdp",
    "step3_npt.mdp",
    "step4_production.mdp",
    "submit.sh",
    "run_md.sh",
    "analyze.py",
    "README.md",
)


class _PackageLoader(BaseLoader):
    """Load Jinja2 templates from casmd.bundle.templates package data."""

    def get_source(self, environment, template: str):
        try:
            res = resources.files("casmd.bundle.templates").joinpath(f"{template}.j2")
            text = res.read_text(encoding="utf-8")
        except (FileNotFoundError, ModuleNotFoundError):
            raise TemplateNotFound(template)
        return text, None, lambda: True


_ENV = Environment(loader=_PackageLoader(), keep_trailing_newline=True)


def list_template_names() -> list[str]:
    return list(_TEMPLATE_NAMES)


def render(name: str, spec: BundleSpec, *, extra: dict[str, Any] | None = None) -> str:
    """Render template `name` using a BundleSpec (plus optional extra context)."""
    if name not in _TEMPLATE_NAMES:
        raise KeyError(f"unknown template {name!r}; known: {_TEMPLATE_NAMES}")
    ctx: dict[str, Any] = asdict(spec)
    # Add derived ints from spec properties
    ctx["production_steps"] = spec.production_steps
    ctx["nvt_steps"] = spec.nvt_steps
    ctx["npt_steps"] = spec.npt_steps
    ctx["output_every_steps"] = spec.output_every_steps
    if extra:
        ctx.update(extra)
    template = _ENV.get_template(name)
    return template.render(**ctx)
