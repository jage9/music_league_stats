from __future__ import annotations

from ..models import SiteModel
from ..render import anchor, fmt_dt, page_shell, section, stat_grid, table


def render_home(model: SiteModel) -> str:
    intro = f"<p>{model.site_description}</p>" if model.site_description else "<p>This archive combines every Music League export found in the local <code>leagues/</code> directory and turns it into a browseable set of static pages.</p>"
    totals = stat_grid(
        [
            ("Leagues", model.stats["league_count"]),
            ("Rounds", model.stats["round_count"]),
            ("Players", model.stats["player_count"]),
            ("Artists", model.stats["artist_count"]),
            ("Albums", model.stats["album_count"]),
            ("Songs", model.stats["submission_count"]),
            ("Votes", model.stats["vote_count"]),
            ("Zero-Point Songs", model.stats["zero_point_count"]),
        ]
    )
    latest_rows = [
        [
            anchor("index.html", league.url, league.name),
            fmt_dt(league.first_round_at),
            fmt_dt(league.last_round_at),
            str(len(league.rounds)),
            str(len(league.player_names)),
        ]
        for league in model.latest_leagues
    ]
    leaderboard_rows = [
        [anchor("index.html", player.url, player.name), str(player.total_points), str(len(player.submissions)), f"{player.average_points:.2f}", str(player.round_wins)]
        for player in model.top_players[:12]
    ]
    submission_rows = [
        [anchor("index.html", sub.url, sub.title), sub.artist_display, anchor("index.html", sub.round.url, sub.round.name), anchor("index.html", model.players[sub.submitter_key].url, sub.submitter_name), str(sub.total_points)]
        for sub in model.top_submissions[:12]
    ]
    artist_rows = [
        [anchor("index.html", artist.url, artist.name), str(len(artist.submissions)), str(artist.total_points), f"{artist.average_points:.2f}"]
        for artist in sorted([artist for artist in model.artists.values() if len(artist.submissions) >= 3], key=lambda item: (-item.average_points, -item.total_points, item.name.lower()))[:12]
    ]
    album_rows = [
        [anchor("index.html", album.url, album.name), str(len(album.submissions)), str(album.total_points), f"{album.average_points:.2f}"]
        for album in model.top_albums_by_points[:10]
    ]
    popular_round_rows = [
        [anchor("index.html", rnd.url, rnd.name), anchor("index.html", rnd.league.url, rnd.league.name), str(len(rnd.submissions)), f"{rnd.average_points_per_song:.2f}"]
        for rnd in model.hall_of_fame_rounds[:10]
    ]
    linked = lambda href, title: f'<section><h2><a href="{href}">{title}</a></h2>'
    body = "".join(
        [
            intro,
            section("Global Totals", totals),
            section("League Timeline", table(["League", "First Round", "Last Round", "Rounds", "Players"], latest_rows)),
            linked("players/index.html", "Career Leaderboard") + table(["Player", "Points", "Submissions", "Average Points", "Round Wins"], leaderboard_rows) + "</section>",
            linked("songs/index.html", "Best Single Submissions") + table(["Song", "Artist", "Round", "Submitter", "Points"], submission_rows) + "</section>",
            linked("artists/index.html", "Most Successful Artists (min. 3 submissions)") + table(["Artist", "Submissions", "Points", "Average Points"], artist_rows) + "</section>",
            linked("albums/index.html", "Top Albums") + table(["Album", "Appearances", "Points", "Average Points"], album_rows) + "</section>",
            "<section><h2>Most Popular Rounds</h2><p>These are the rounds that combined strong participation and strong average scoring.</p>" + table(["Round", "League", "Submissions", "Avg Points Per Song"], popular_round_rows) + "</section>",
        ]
    )
    return page_shell(model, model.site_title, body, model.site_dir / "index.html")
