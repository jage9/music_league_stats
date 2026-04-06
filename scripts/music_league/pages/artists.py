from __future__ import annotations

from collections import Counter

from ..models import Artist, SiteModel
from ..render import anchor, page_shell, section, stat_grid, table


def render_artists_index(model: SiteModel) -> str:
    rows = [[anchor("artists/index.html", artist.url, artist.name), str(len(artist.submissions)), str(artist.total_points), f"{artist.average_points:.2f}", str(len(artist.submitters)), str(len(artist.leagues))] for artist in sorted(model.artists.values(), key=lambda item: (-len(item.submissions), -item.total_points, item.name.lower()))]
    return page_shell(model, "Artists", table(["Artist", "Appearances", "Points", "Average Points", "Submitters", "Leagues"], rows, sortable={"columns": {0: "text", 1: "number", 2: "number", 3: "number", 4: "number", 5: "number"}, "default_column": 1, "default_direction": "desc"}), model.site_dir / "artists" / "index.html")


def render_artist_page(model: SiteModel, artist: Artist) -> str:
    submitter_counter = Counter(sub.submitter_name for sub in artist.submissions)
    league_counter = Counter(sub.league.name for sub in artist.submissions)
    album_counter = Counter(sub.album_key for sub in artist.submissions if sub.album_key)
    rows = [[anchor(artist.url, sub.url, sub.title), anchor(artist.url, model.players[sub.submitter_key].url, sub.submitter_name), anchor(artist.url, sub.round.url, sub.round.name), anchor(artist.url, sub.league.url, sub.league.name), str(sub.total_points), str(sub.place)] for sub in sorted(artist.submissions, key=lambda item: (-item.total_points, item.title.lower()))]
    submitter_rows = [[anchor(artist.url, model.player_urls_by_name[name], name), str(count)] for name, count in submitter_counter.most_common(12)]
    league_rows = [[anchor(artist.url, model.league_urls_by_name[name], name), str(count)] for name, count in league_counter.most_common()]
    album_rows = [[anchor(artist.url, model.albums[key].url, model.albums[key].name), str(count)] for key, count in album_counter.most_common(12)]
    body = "".join(
        [
            section("Artist Totals", stat_grid([("Appearances", len(artist.submissions)), ("Points", artist.total_points), ("Average Points", artist.average_points), ("Submitters", len(artist.submitters)), ("Leagues", len(artist.leagues))])),
            section("Frequent Submitters", table(["Player", "Appearances"], submitter_rows, sortable={"columns": {0: "text", 1: "number"}, "default_column": 1, "default_direction": "desc"})),
            section("League Spread", table(["League", "Appearances"], league_rows, sortable={"columns": {0: "text", 1: "number"}, "default_column": 1, "default_direction": "desc"})),
            section("Albums", table(["Album", "Appearances"], album_rows, sortable={"columns": {0: "text", 1: "number"}, "default_column": 1, "default_direction": "desc"})),
            section("Appearances", table(["Song", "Submitter", "Round", "League", "Points", "Place"], rows, sortable={"columns": {0: "text", 1: "text", 2: "text", 3: "text", 4: "number", 5: "number"}, "default_column": 4, "default_direction": "desc"})),
        ]
    )
    return page_shell(model, artist.name, body, model.site_dir / artist.url)
