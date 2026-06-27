"""Offer domain logic: CTC breakdown and offer-letter rendering.

The salary breakdown follows a conventional Indian CTC structure. The letter is
rendered from a Jinja2 template body into a self-contained printable HTML
document; a PDF is produced via WeasyPrint *if* it is installed (it needs native
GTK libraries), otherwise callers fall back to browser print-to-PDF.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from jinja2 import Environment, select_autoescape

# Proportions of annual CTC used to derive the components.
_BASIC_PCT = 0.40
_HRA_OF_BASIC = 0.50
_EMPLOYER_PF_OF_BASIC = 0.12
_GRATUITY_OF_BASIC = 0.0481

_env = Environment(autoescape=select_autoescape(["html", "xml"]))

EMPLOYER_NAME = "SHAI Health"

DEFAULT_TEMPLATE_BODY = """\
Dear {{ candidate_name }},

We are delighted to offer you the position of **{{ designation }}** at {{ employer }}.

Your annual cost to company (CTC) will be **₹{{ "{:,}".format(annual_ctc) }}**, with a
proposed date of joining of **{{ joining_date }}**.

A detailed breakdown of your compensation is enclosed. This offer is contingent on
successful completion of background verification and submission of the required
documents.

We look forward to welcoming you to the team.

Warm regards,
Talent Acquisition, {{ employer }}
"""


def compute_breakdown(annual_ctc: int) -> list[dict[str, Any]]:
    """Return the salary components for ``annual_ctc`` (rupees per year)."""
    basic = round(annual_ctc * _BASIC_PCT)
    hra = round(basic * _HRA_OF_BASIC)
    employer_pf = round(basic * _EMPLOYER_PF_OF_BASIC)
    gratuity = round(basic * _GRATUITY_OF_BASIC)
    special = annual_ctc - (basic + hra + employer_pf + gratuity)

    rows = [
        ("Basic", basic),
        ("House Rent Allowance", hra),
        ("Special Allowance", special),
        ("Employer PF Contribution", employer_pf),
        ("Gratuity", gratuity),
    ]
    components = [
        {"label": label, "annual": annual, "monthly": round(annual / 12)}
        for label, annual in rows
    ]
    components.append(
        {"label": "Total CTC", "annual": annual_ctc, "monthly": round(annual_ctc / 12)}
    )
    return components


def dump_components(components: list[dict[str, Any]]) -> str:
    return json.dumps(components)


def load_components(raw: str) -> list[dict[str, Any]]:
    return list(json.loads(raw))


def render_letter_body(
    body_md: str,
    *,
    candidate_name: str,
    designation: str,
    annual_ctc: int,
    joining_date: date,
) -> str:
    """Render the template body with the offer context (returns text/markdown)."""
    template = _env.from_string(body_md)
    return template.render(
        candidate_name=candidate_name,
        designation=designation,
        annual_ctc=annual_ctc,
        joining_date=joining_date.isoformat(),
        employer=EMPLOYER_NAME,
    )


def render_letter_html(
    *,
    subject: str,
    body: str,
    components: list[dict[str, Any]],
) -> str:
    """Wrap a rendered body + salary table into a printable HTML document."""
    paragraphs = "".join(
        f"<p>{line.strip()}</p>" for line in body.split("\n\n") if line.strip()
    )
    rows = "".join(
        f"<tr><td>{c['label']}</td>"
        f"<td style='text-align:right'>₹{c['annual']:,}</td>"
        f"<td style='text-align:right'>₹{c['monthly']:,}</td></tr>"
        for c in components
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{subject}</title>
<style>
  body {{ font-family: Georgia, serif; color: #1a1a1a; max-width: 720px; margin: 2rem auto; line-height: 1.5; }}
  h1 {{ font-size: 1.25rem; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; font-family: Arial, sans-serif; font-size: 0.9rem; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; }}
  th {{ background: #f3f0fa; text-align: left; }}
  tr:last-child td {{ font-weight: bold; }}
</style></head>
<body>
  <h1>{subject}</h1>
  {paragraphs}
  <h2 style="font-size:1rem">Compensation breakdown</h2>
  <table>
    <thead><tr><th>Component</th><th style="text-align:right">Annual (₹)</th><th style="text-align:right">Monthly (₹)</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body></html>"""


def html_to_pdf(html: str) -> bytes | None:
    """Render HTML to PDF bytes via WeasyPrint, or ``None`` if unavailable."""
    try:
        from weasyprint import HTML
    except (ImportError, OSError):
        return None
    return bytes(HTML(string=html).write_pdf())  # pragma: no cover  — needs native libs
