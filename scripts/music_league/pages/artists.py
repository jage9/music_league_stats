from __future__ import annotations

from collections import Counter

from ..models import Artist, SiteModel
from ..render import anchor, page_shell, section, stat_grid, table


def render_artists_index(model: SiteModel) -> str:
    rows = [[anchor("artists/index.html", artist.url, artist.name), str(len(artist.submissions)), str(artist.total_points), f"{artist.average_points:.2f}", str(len(artist.submitters)), str(len(artist.leagues))] for artist in sorted(model.artists.values(), key=lambda item: (-item.total_points, item.name.lower()))]
    return page_shell(model, "Artists", section("Artists", table(["Artist", "Appearances", "Points", "Average Points", "Submitters", "Leagues"], rows)), model.site_dir / "artists" / "index.html")


def render_artist_page(model: SiteModel, artist: Artist) -> str:
    submitter_counter = Counter(sub.submitter_name for sub in artist.submissions)
    league_counter = Counter(sub.league.name for sub in artist.submissions)
    album_counter = Counter(sub.album for sub in artist.submissions)
    rows = [[anchor(artist.url, sub.url, sub.title), anchor(artist.url, model.players[sub.submitter_key].url, sub.submitter_name), anchor(artist.url, sub.round.url, sub.round.name), anchor(artist.url, sub.league.url, sub.league.name), str(sub.total_points), str(sub.place)] for sub in sorted(artist.submissions, key=lambda item: (-item.total_points, item.title.lower()))]
    submitter_rows = [[anchor(artist.url, model.players[next(key for key, value in model.players.items() if value.name == name)].url, name), str(count)] for name, count in submitter_counter.most_common(12)]
    league_rows = [[anchor(artist.url, next(league.url for league in model.leagues if league.name == name), name), str(count)] for name, count in league_counter.most_common()]
    album_rows = [[anchor(artist.url, model.albums[next(key for key, value in model.albums.items() if value.name == name)].url, name), str(count)] for name, count in album_counter.most_common(12)]
    body = "".join(
        [
            section("Artist Totals", stat_grid([("Appearances", len(artist.submissions)), ("Points", artist.total_points), ("Average Points", artist.average_points), ("Submitters", len(artist.submitters)), ("Leagues", len(artist.leagues))])),
            section("Frequent Submitters", table(["Player", "Appearances"], submitter_rows)),
            section("League Spread", table(["League", "Appearances"], league_rows)),
            section("Albums", table(["Album", "Appearances"], album_rows)),
            section("Appearances", table(["Song", "Submitter", "Round", "League", "Points", "Place"], rows)),
        ]
    )
    return page_shell(model, artist.name, body, model.site_dir / artist.url)
