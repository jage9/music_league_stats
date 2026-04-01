from __future__ import annotations

from collections import defaultdict

from ..models import SiteModel
from ..render import fmt_dt, page_shell


def render_playlists_page(model: SiteModel) -> str:
    grouped = defaultdict(list)
    for round_obj in model.playlists:
        grouped[round_obj.league.name].append(round_obj)
    sections = ['<section><h2>Spotify Playlists</h2><p>Links to Spotify playlists for all Music League rounds.</p></section>']
    for league_name, rounds in grouped.items():
        items = "".join(
            f'<li><a href="{round_obj.playlist_url}" target="_blank" rel="noopener noreferrer">{round_obj.name} ({len(round_obj.submissions)})</a><span class="meta">{fmt_dt(round_obj.created_at)}</span></li>'
            for round_obj in rounds
        )
        sections.append(f"<section><h2>{league_name}</h2><ul class=\"link-list\">{items}</ul></section>")
    body = "".join(sections)
    return page_shell(model, "Playlists", body, model.site_dir / "playlists" / "index.html")
