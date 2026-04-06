from __future__ import annotations

from ..models import Player, SiteModel
from ..render import anchor, fmt_dt, page_shell, section, stat_grid, table


def render_players_index(model: SiteModel) -> str:
    rows = [[anchor("players/index.html", player.url, player.name), str(len(player.leagues)), str(len(player.submissions)), str(player.total_points), f"{player.average_points:.2f}", f"{player.average_finish_percentile * 100:.1f}%", str(player.round_wins)] for player in sorted(model.players.values(), key=lambda item: (-item.total_points, item.name.lower()))]
    recent_rounds = sorted(model.rounds, key=lambda item: item.created_at, reverse=True)[:5]
    recent_round_keys = {round_obj.key for round_obj in recent_rounds}
    trending_rows = [
        [
            anchor("players/index.html", player.url, player.name),
            str(sum(1 for sub in player.submissions if sub.round.key in recent_round_keys)),
            str(sum(sub.total_points for sub in player.submissions if sub.round.key in recent_round_keys)),
            f"{sum(sub.total_points for sub in player.submissions if sub.round.key in recent_round_keys) / sum(1 for sub in player.submissions if sub.round.key in recent_round_keys):.2f}",
            str(sum(1 for winner in model.round_winners.values() if winner.submitter_key == player.key and winner.round.key in recent_round_keys)),
        ]
        for player in model.trending_players
    ]
    body = "".join(
        [
            '<section id="career-leaderboard"><h2>Career Leaderboard</h2>'
            + table(["Player", "Leagues", "Submissions", "Points", "Average Points", "Avg Finish Percentile", "Wins"], rows, sortable={"columns": {0: "text", 1: "number", 2: "number", 3: "number", 4: "number", 5: "number", 6: "number"}, "default_column": 3, "default_direction": "desc"})
            + "</section>",
            '<section id="trending-last-5-rounds"><h2>Trending (Last 5 Rounds)</h2><p>Based on the most recent 5 rounds across all leagues.</p>'
            + table(["Player", "Submissions", "Points", "Average Points", "Wins"], trending_rows, sortable={"columns": {0: "text", 1: "number", 2: "number", 3: "number", 4: "number"}, "default_column": 2, "default_direction": "desc"})
            + "</section>",
        ]
    )
    return page_shell(model, "Players", body, model.site_dir / "players" / "index.html")


def render_player_page(model: SiteModel, player: Player) -> str:
    per_league = [[anchor(player.url, model.league_urls_by_name[league], league), str(sum(1 for sub in player.submissions if sub.league.name == league)), str(sum(sub.total_points for sub in player.submissions if sub.league.name == league)), f"{sum(sub.total_points for sub in player.submissions if sub.league.name == league) / sum(1 for sub in player.submissions if sub.league.name == league):.2f}"] for league in sorted(player.leagues)]
    best = player.best_submission
    worst = player.worst_submission
    placement_rows = [[fmt_dt(sub.round.created_at), anchor(player.url, sub.round.url, sub.round.name), anchor(player.url, sub.url, sub.title), str(sub.place), str(sub.total_points), f"{sub.finish_percentile * 100:.1f}%"] for sub in player.placement_history]
    signature_rows = [[anchor(player.url, model.artist_urls_by_name[name], name), str(count), str(points)] for name, count, points in player.signature_artists]
    similar_rows = [[anchor(player.url, model.players[item.other_key].url, model.players[item.other_key].name), str(item.overlap), f"{item.similarity_score * 100:.1f}%", f"{item.average_gap:.2f}"] for item in player.similar_voters]
    best_place = best.place if best else None
    worst_place = worst.place if worst else None
    best_rows = [["Best", anchor(player.url, sub.url, sub.title), anchor(player.url, sub.round.url, sub.round.name), str(sub.place), str(sub.total_points)] for sub in player.submissions if best_place is not None and sub.place == best_place]
    worst_rows = [["Worst", anchor(player.url, sub.url, sub.title), anchor(player.url, sub.round.url, sub.round.name), str(sub.place), str(sub.total_points)] for sub in player.submissions if worst_place is not None and sub.place == worst_place]
    body = "".join(
        [
            section("Career Totals", stat_grid([("Leagues", len(player.leagues)), ("Submissions", len(player.submissions)), ("Points", player.total_points), ("Average Points", player.average_points), ("Average Finish", player.average_finish), ("Avg Finish Percentile", f"{player.average_finish_percentile * 100:.1f}%"), ("Round Wins", player.round_wins)])),
            section("Per-League Splits", table(["League", "Submissions", "Points", "Average Points"], per_league, sortable={"columns": {0: "text", 1: "number", 2: "number", 3: "number"}, "default_column": 2, "default_direction": "desc"})),
            section("Best And Worst Finishes", table(["Type", "Song", "Round", "Place", "Points"], best_rows + worst_rows if best and worst else [], sortable={"columns": {0: "text", 1: "text", 2: "text", 3: "number", 4: "number"}, "default_column": 3, "default_direction": "asc"})),
            section("Placement History", table(["Date", "Round", "Song", "Place", "Points", "Finish Percentile"], placement_rows, sortable={"columns": {0: "date", 1: "text", 2: "text", 3: "number", 4: "number", 5: "number"}, "default_column": 0, "default_direction": "asc"})),
            section("Signature Artists", table(["Artist", "Appearances", "Points"], signature_rows, sortable={"columns": {0: "text", 1: "number", 2: "number"}, "default_column": 1, "default_direction": "desc"})),
            section("Most Similar Voters", "<p>This compares only songs that both players voted on and measures how close their point assignments were.</p>" + (table(["Player", "Shared Votes", "Similarity", "Average Gap"], similar_rows, sortable={"columns": {0: "text", 1: "number", 2: "number", 3: "number"}, "default_column": 1, "default_direction": "desc"}) if similar_rows else "<p>Not enough overlapping votes to compute similarity.</p>")),
        ]
    )
    return page_shell(model, player.name, body, model.site_dir / player.url)
