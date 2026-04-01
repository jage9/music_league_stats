from __future__ import annotations

import statistics
from collections import Counter

from ..models import League, SiteModel
from ..render import anchor, fmt_dt, page_shell, section, stat_grid, table


def _round_winner_submission(round_obj):
    if not round_obj.submissions:
        return None
    return sorted(
        round_obj.submissions,
        key=lambda item: (-item.total_points, -item.vote_count, item.title.lower(), item.submitter_name.lower()),
    )[0]


def render_leagues_index(model: SiteModel) -> str:
    cards = "".join(
        f'<article class="panel"><h3>{anchor("leagues/index.html", league.url, league.name)}</h3><p>{fmt_dt(league.first_round_at)} to {fmt_dt(league.last_round_at)}</p><p>{len(league.rounds)} rounds, {len(league.player_names)} players, {league.total_submissions} submissions, {league.total_votes} votes.</p></article>'
        for league in model.latest_leagues
    )
    return page_shell(model, "Leagues", section("League Directory", cards), model.site_dir / "leagues" / "index.html")


def render_league_page(model: SiteModel, league: League) -> str:
    league_winners = {rnd.key: model.round_winners.get(rnd.key) or _round_winner_submission(rnd) for rnd in league.rounds}
    rounds_rows = []
    for rnd in sorted(league.rounds, key=lambda item: item.created_at, reverse=True):
        winner = league_winners.get(rnd.key)
        winner_html = (
            f"{anchor(league.url, winner.url, winner.title)} by {anchor(league.url, model.players[winner.submitter_key].url, winner.submitter_name)}"
            if winner
            else ""
        )
        rounds_rows.append(
            [
                anchor(league.url, rnd.url, rnd.name),
                fmt_dt(rnd.created_at),
                winner_html,
                str(len(rnd.submissions)),
                f"{rnd.average_points_per_song:.2f}",
                f'<a href="{rnd.playlist_url}" target="_blank" rel="noopener noreferrer">Spotify playlist</a>' if rnd.playlist_url else "",
            ]
        )
    players = [player for player in model.players.values() if league.name in player.leagues]
    player_win_counts = Counter(
        winner.submitter_key
        for winner in league_winners.values()
        if winner is not None
    )
    player_rows = [
        [
            anchor(league.url, player.url, player.name),
            str(sum(1 for sub in player.submissions if sub.league.name == league.name)),
            str(sum(sub.total_points for sub in player.submissions if sub.league.name == league.name)),
            f"{statistics.mean(sub.total_points for sub in player.submissions if sub.league.name == league.name):.2f}",
            str(player_win_counts[player.key]),
        ]
        for player in sorted(players, key=lambda item: (-sum(sub.total_points for sub in item.submissions if sub.league.name == league.name), item.name.lower()))[:15]
        if any(sub.league.name == league.name for sub in player.submissions)
    ]
    artist_counter = Counter()
    artist_points = Counter()
    for sub in model.submissions:
        if sub.league.name == league.name:
            for artist in sub.artists:
                artist_counter[artist] += 1
                artist_points[artist] += sub.total_points
    artist_rows = [[anchor(league.url, model.artists[key].url, model.artists[key].name), str(len(model.artists[key].submissions)), str(model.artists[key].total_points)] for key in sorted(model.artists, key=lambda k: (-artist_points[model.artists[k].name], model.artists[k].name.lower()))[:15] if model.artists[key].name in artist_counter]
    songs = [sub for sub in model.submissions if sub.league.name == league.name]
    song_rows = [[anchor(league.url, sub.url, sub.title), sub.artist_display, anchor(league.url, model.players[sub.submitter_key].url, sub.submitter_name), str(sub.total_points), anchor(league.url, sub.round.url, sub.round.name)] for sub in sorted(songs, key=lambda item: (-item.total_points, -item.vote_count, item.title.lower()))[:20]]
    body = "".join(
        [
            section("Overview", stat_grid([("Rounds", len(league.rounds)), ("Players", len(league.player_names)), ("Submissions", league.total_submissions), ("Votes", league.total_votes), ("Points Awarded", league.total_points)])),
            section("Chronology", f"<p>{fmt_dt(league.first_round_at)} to {fmt_dt(league.last_round_at)}</p>"),
            section("Rounds", table(["Round", "Created", "Winner", "Submissions", "Avg Points Per Song", "Playlist"], rounds_rows)),
            section("Leaderboard", table(["Player", "Submissions", "Points", "Average Points", "Wins"], player_rows)),
            section("Standout Artists", table(["Artist", "Appearances", "Points"], artist_rows)),
            section("Notable Songs", table(["Song", "Artist", "Submitter", "Points", "Round"], song_rows)),
        ]
    )
    return page_shell(model, league.name, body, model.site_dir / league.url)
