from __future__ import annotations

from ..models import SiteModel
from ..render import anchor, page_shell, section


def render_changelog_page(model: SiteModel) -> str:
    body = "".join(
        [
            "<p>Notable updates to the generated site.</p>",
            section(
                model.site_version,
                "".join(
                    [
                        "<p>April 5, 2026</p>",
                        "<ul>",
                        "<li>Added sortable columns on many pages</li>",
                        "<li>Added prompt descriptions to the prompts and playlist page</li>",
                        "<li>Added a trending section to show stats over the last 5 rounds</li>",
                        "<li>Fix: Placement calculation for best/worst display</li>",
                        "</ul>",
                    ]
                ),
            ),
            f"<p>{anchor('changelog/index.html', 'index.html', 'Back to home')}</p>",
        ]
    )
    return page_shell(model, "Change Log", body, model.site_dir / "changelog" / "index.html")
