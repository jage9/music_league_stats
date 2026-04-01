from __future__ import annotations

from ..models import Album, SiteModel
from ..render import anchor, page_shell, section, stat_grid, table


def render_albums_index(model: SiteModel) -> str:
    artist_targets = {artist.name: artist.url for artist in model.artists.values()}
    rows = [
        [
            anchor("albums/index.html", album.url, album.name),
            ", ".join(anchor("albums/index.html", artist_targets[artist], artist) for artist in sorted(album.artists)),
            str(len(album.submissions)),
            str(album.total_points),
            f"{album.average_points:.2f}",
            str(len(album.submitters)),
        ]
        for album in sorted(model.albums.values(), key=lambda item: (-len(item.submissions), -item.total_points, item.name.lower()))
    ]
    return page_shell(model, "Albums", section("Album Stats", table(["Album", "Artist", "Appearances", "Points", "Average Points", "Submitters"], rows)), model.site_dir / "albums" / "index.html")


def render_album_page(model: SiteModel, album: Album) -> str:
    artist_targets = {artist.name: artist.url for artist in model.artists.values()}
    rows = [
        [
            anchor(album.url, sub.url, sub.title),
            ", ".join(anchor(album.url, artist_targets[artist], artist) for artist in sub.artists),
            anchor(album.url, model.players[sub.submitter_key].url, sub.submitter_name),
            anchor(album.url, sub.round.url, sub.round.name),
            anchor(album.url, sub.league.url, sub.league.name),
            str(sub.total_points),
        ]
        for sub in sorted(album.submissions, key=lambda item: (-item.total_points, item.title.lower()))
    ]
    body = "".join(
        [
            section("Album Totals", stat_grid([("Appearances", len(album.submissions)), ("Points", album.total_points), ("Average Points", album.average_points), ("Submitters", len(album.submitters)), ("Leagues", len(album.leagues))])),
            section("Songs", table(["Song", "Artist", "Submitter", "Round", "League", "Points"], rows)),
        ]
    )
    return page_shell(model, album.name, body, model.site_dir / album.url)
