from __future__ import annotations

from collections import defaultdict

from ..models import SiteModel
from ..render import fmt_dt, page_shell


def render_playlists_page(model: SiteModel) -> str:
    grouped = defaultdict(list)
    for round_obj in model.playlists:
        grouped[round_obj.league.name].append(round_obj)
    sections = ['<p>Prompts and links to Spotify playlists for all Music League rounds.</p>']
    for league_name, rounds in grouped.items():
        items = "".join(
            "<article class=\"panel\">"
            + f"<h3>{round_obj.name} ({len(round_obj.submissions)})</h3>"
            + f"<p>{round_obj.description or 'No prompt description provided.'}</p>"
            + (
                f'<p><a href="{round_obj.playlist_url}" target="_blank" rel="noopener noreferrer">{round_obj.playlist_url}</a><span class="meta">{fmt_dt(round_obj.created_at)}</span></p>'
                if round_obj.playlist_url
                else f'<p><span class="meta">{fmt_dt(round_obj.created_at)}</span></p>'
            )
            + "</article>"
            for round_obj in rounds
        )
        sections.append(f"<section><h2>{league_name}</h2>{items}</section>")
    body = "".join(sections)
    return page_shell(model, "Prompts and Playlists", body, model.site_dir / "playlists" / "index.html")
