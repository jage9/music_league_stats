from __future__ import annotations

from ..models import SiteModel
from ..render import anchor, page_shell, section
from ..site_meta import CHANGELOG_ENTRIES


def render_changelog_page(model: SiteModel) -> str:
    sections = []
    for entry in CHANGELOG_ENTRIES:
        items = "".join(f"<li>{item}</li>" for item in entry["items"])
        sections.append(section(entry["version"], f"<p>{entry['date']}</p><ul>{items}</ul>"))
    body = "".join(
        [
            "<p>Notable updates to the generated site.</p>",
            "".join(sections),
            f"<p>{anchor('changelog/index.html', 'index.html', 'Back to home')}</p>",
        ]
    )
    return page_shell(model, "Change Log", body, model.site_dir / "changelog" / "index.html")
