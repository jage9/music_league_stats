from __future__ import annotations

import html
import os
import shutil
from datetime import datetime
from pathlib import Path

from .models import SiteModel


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def fmt_num(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return f"{value:,}"
    number = float(value)
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.2f}"


def fmt_dt(value: datetime) -> str:
    return value.strftime("%B %d, %Y")


def fmt_generated_dt(value: datetime) -> str:
    formatted = value.strftime("%Y-%m-%d %H:%M:%S %Z")
    return formatted.replace("Eastern Daylight Time", "EDT").replace("Eastern Standard Time", "EST")


def rel_link(from_dir: Path, to_path: Path) -> str:
    return os.path.relpath(to_path, from_dir).replace("\\", "/")


def page_rel(current_url: str, target_url: str) -> str:
    return os.path.relpath(target_url, Path(current_url).parent).replace("\\", "/")


def anchor(current_url: str, target_url: str, label: str) -> str:
    return f'<a href="{esc(page_rel(current_url, target_url))}">{esc(label)}</a>'


def spotify_track_url(uri: str) -> str | None:
    if not uri.startswith("spotify:track:"):
        return None
    return "https://open.spotify.com/track/" + uri.split(":")[-1]


def section(title: str, body: str) -> str:
    return f"<section><h2>{esc(title)}</h2>{body}</section>"


def stat_grid(items: list[tuple[str, object]]) -> str:
    cards = "".join(f'<div class="stat-card"><p class="stat-label">{esc(label)}</p><p>{esc(fmt_num(value))}</p></div>' for label, value in items)
    return f'<div class="stat-grid">{cards}</div>'


def stat_grid_html(items: list[tuple[str, str]]) -> str:
    cards = "".join(f'<div class="stat-card"><p class="stat-label">{esc(label)}</p><p>{value}</p></div>' for label, value in items)
    return f'<div class="stat-grid">{cards}</div>'


def link_list(items: list[tuple[str, str, str | None]]) -> str:
    rows = []
    for label, href, meta in items:
        meta_html = f'<span class="meta">{esc(meta)}</span>' if meta else ""
        rows.append(f'<li><a href="{esc(href)}">{esc(label)}</a>{meta_html}</li>')
    return f"<ul class=\"link-list\">{''.join(rows)}</ul>"


def tagged_links(items: list[tuple[str, str]]) -> str:
    return "<p class=\"tag-list\">" + "".join(f'<a class="tag" href="{esc(href)}">{esc(label)}</a>' for label, href in items) + "</p>"


def table(headers: list[str], rows: list[list[str]], sortable: dict[str, object] | None = None) -> str:
    column_types = sortable.get("columns", {}) if sortable else {}
    sortable_columns = set(column_types.keys()) if sortable else set()
    default_column = int(sortable.get("default_column", 0)) if sortable else 0
    default_direction = str(sortable.get("default_direction", "asc")) if sortable else "asc"
    table_attrs = ""
    if sortable:
        table_attrs = (
            ' class="sortable-table"'
            + f' data-default-sort-column="{default_column}"'
            + f' data-default-sort-direction="{esc(default_direction)}"'
        )
    head_parts = []
    for index, header in enumerate(headers):
        if index in sortable_columns:
            aria_sort = ("descending" if default_direction == "desc" else "ascending") if index == default_column else "none"
            head_parts.append(
                f'<th scope="col" aria-sort="{esc(aria_sort)}">'
                f'<button type="button" class="sort-button" data-column="{index}" data-sort-type="{esc(str(column_types.get(index, "text")))}" data-direction="{esc(default_direction if index == default_column else "asc")}">'
                f'<span class="sort-label">{esc(header)}</span>'
                f"</button></th>"
            )
        else:
            head_parts.append(f'<th scope="col">{esc(header)}</th>')
    head = "".join(head_parts)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table{table_attrs}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


SORTER_SCRIPT = """
<script>
(function () {
  function parseValue(text, type) {
    const normalized = text.trim();
    if (type === "number") {
      const value = Number.parseFloat(normalized.replace(/,/g, "").replace(/%/g, ""));
      return Number.isNaN(value) ? Number.NEGATIVE_INFINITY : value;
    }
    if (type === "date") {
      const value = Date.parse(normalized);
      return Number.isNaN(value) ? Number.NEGATIVE_INFINITY : value;
    }
    return normalized.toLocaleLowerCase();
  }

  function updateHeaderState(table, columnIndex, direction) {
    const headers = Array.from(table.querySelectorAll("thead th"));
    headers.forEach((header, index) => {
      const button = header.querySelector(".sort-button");
      if (!button) {
        return;
      }
      const active = index === columnIndex;
      header.setAttribute("aria-sort", active ? (direction === "asc" ? "ascending" : "descending") : "none");
      button.dataset.direction = active && direction === "asc" ? "desc" : "asc";
      const label = button.querySelector(".sort-label");
      if (label) {
        const baseLabel = button.dataset.baseLabel || label.textContent || "column";
        button.dataset.baseLabel = baseLabel;
        label.textContent = active ? `${baseLabel}, ${direction === "asc" ? "ascending" : "descending"}` : baseLabel;
      }
    });
  }

  document.querySelectorAll("table.sortable-table").forEach((table) => {
    const tbody = table.tBodies[0];
    if (!tbody) {
      return;
    }
    const rows = Array.from(tbody.rows);
    const defaultColumn = Number.parseInt(table.dataset.defaultSortColumn || "0", 10);
    const defaultDirection = table.dataset.defaultSortDirection === "desc" ? "desc" : "asc";
    const buttons = table.querySelectorAll(".sort-button");

    function sortRows(columnIndex, direction) {
      const button = table.querySelector(`.sort-button[data-column="${columnIndex}"]`);
      const type = button?.dataset.sortType || "text";
      rows.sort((leftRow, rightRow) => {
        const leftText = leftRow.cells[columnIndex]?.textContent || "";
        const rightText = rightRow.cells[columnIndex]?.textContent || "";
        const leftValue = parseValue(leftText, type);
        const rightValue = parseValue(rightText, type);
        if (leftValue < rightValue) {
          return direction === "asc" ? -1 : 1;
        }
        if (leftValue > rightValue) {
          return direction === "asc" ? 1 : -1;
        }
        return 0;
      });
      tbody.replaceChildren(...rows);
      updateHeaderState(table, columnIndex, direction);
    }

    buttons.forEach((button) => {
      button.addEventListener("click", function () {
        const columnIndex = Number.parseInt(button.dataset.column || "0", 10);
        const direction = button.dataset.direction === "desc" ? "desc" : "asc";
        sortRows(columnIndex, direction);
      });
    });

    sortRows(defaultColumn, defaultDirection);
  });
}());
</script>
"""


def page_shell(model: SiteModel, title: str, body: str, page_path: Path, browser_title: str | None = None) -> str:
    css_href = rel_link(page_path.parent, model.site_assets_dir / "style.css")
    full_title = browser_title or title
    if full_title != model.site_title:
        full_title = f"{full_title} | {model.site_title}"
    nav_items = [
        ("Home", model.site_dir / "index.html"),
        ("Leagues", model.site_dir / "leagues" / "index.html"),
        ("Players", model.site_dir / "players" / "index.html"),
        ("Artists", model.site_dir / "artists" / "index.html"),
        ("Albums", model.site_dir / "albums" / "index.html"),
        ("Songs", model.site_dir / "songs" / "index.html"),
        ("Playlists", model.site_dir / "playlists" / "index.html"),
        ("Stats", model.site_dir / "stats" / "index.html"),
    ]
    nav_html = "".join(f'<a href="{esc(rel_link(page_path.parent, target))}">{esc(label)}</a>' for label, target in nav_items)
    github_href = "https://www.github.com/jage9/music_league_stats"
    changelog_href = rel_link(page_path.parent, model.site_dir / "changelog" / "index.html")
    footer = (
        f'<footer class="site-footer"><p>Generated {esc(fmt_generated_dt(model.generated_at))} '
        f'in {esc(f"{model.generation_seconds:.3f}")} seconds.</p>'
        f'<p>Another AI experiment from Jage. <a href="{esc(github_href)}" target="_blank" rel="noopener noreferrer">Github link</a></p>'
        f'<p>{esc(model.site_version)} <a href="{esc(changelog_href)}">View Changelog</a></p></footer>'
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(full_title)}</title>
  <link rel="stylesheet" href="{esc(css_href)}">
</head>
<body>
  <header class="site-header">
    <nav class="site-nav">{nav_html}</nav>
    <h1>{esc(title)}</h1>
  </header>
  <main class="page">{body}</main>
  {footer}
  {SORTER_SCRIPT}
</body>
</html>
"""


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_page(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")


def write_robots_txt(model: SiteModel) -> None:
    content = "\n".join(
        [
            "User-agent: *",
            "Disallow: /",
            "",
        ]
    )
    write_page(model.site_dir / "robots.txt", content)


def build_site(model: SiteModel) -> None:
    from .pages.changelog import render_changelog_page
    from .pages.albums import render_album_page, render_albums_index
    from .pages.artists import render_artist_page, render_artists_index
    from .pages.home import render_home
    from .pages.leagues import render_league_page, render_leagues_index
    from .pages.players import render_player_page, render_players_index
    from .pages.playlists import render_playlists_page
    from .pages.rounds import render_round_page
    from .pages.songs import render_song_page, render_songs_index
    from .pages.stats import render_stats_index

    if model.site_dir.exists():
        shutil.rmtree(model.site_dir)
    model.site_dir.mkdir(parents=True, exist_ok=True)
    model.site_assets_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(model.assets_dir / "style.css", model.site_assets_dir / "style.css")
    write_robots_txt(model)

    write_page(model.site_dir / "index.html", render_home(model))
    write_page(model.site_dir / "leagues" / "index.html", render_leagues_index(model))
    write_page(model.site_dir / "players" / "index.html", render_players_index(model))
    write_page(model.site_dir / "artists" / "index.html", render_artists_index(model))
    write_page(model.site_dir / "albums" / "index.html", render_albums_index(model))
    write_page(model.site_dir / "songs" / "index.html", render_songs_index(model))
    write_page(model.site_dir / "playlists" / "index.html", render_playlists_page(model))
    write_page(model.site_dir / "stats" / "index.html", render_stats_index(model))
    write_page(model.site_dir / "changelog" / "index.html", render_changelog_page(model))

    for league in model.leagues:
        write_page(model.site_dir / league.url, render_league_page(model, league))
    for round_obj in model.rounds:
        write_page(model.site_dir / round_obj.url, render_round_page(model, round_obj))
    for player in model.players.values():
        write_page(model.site_dir / player.url, render_player_page(model, player))
    for artist in model.artists.values():
        write_page(model.site_dir / artist.url, render_artist_page(model, artist))
    for album in model.albums.values():
        write_page(model.site_dir / album.url, render_album_page(model, album))
    written_song_urls: set[str] = set()
    for submission in model.submissions:
        if submission.url in written_song_urls:
            continue
        write_page(model.site_dir / submission.url, render_song_page(model, submission))
        written_song_urls.add(submission.url)
