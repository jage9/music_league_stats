from __future__ import annotations

from ..models import Player, SiteModel
from ..render import anchor, fmt_dt, page_shell, section, stat_grid, table


def render_players_index(model: SiteModel) -> str:
    rows = [[anchor("players/index.html", player.url, player.name), str(len(player.leagues)), str(len(player.submissions)), str(player.total_points), f"{player.average_points:.2f}", f"{player.average_finish_percentile * 100:.1f}%", str(player.round_wins)] for player in sorted(model.players.values(), key=lambda item: (-item.total_points, item.name.lower()))]
    return page_shell(model, "Players", section("Players", table(["Player", "Leagues", "Submissions", "Points", "Average Points", "Avg Finish Percentile", "Wins"], rows)), model.site_dir / "players" / "index.html")


def render_player_page(model: SiteModel, player: Player) -> str:
    per_league = [[anchor(player.url, model.league_urls_by_name[league], league), str(sum(1 for sub in player.submissions if sub.league.name == league)), str(sum(sub.total_points for sub in player.submissions if sub.league.name == league)), f"{sum(sub.total_points for sub in player.submissions if sub.league.name == league) / sum(1 for sub in player.submissions if sub.league.name == league):.2f}"] for league in sorted(player.leagues)]
    best = player.best_submission
    worst = player.worst_submission
    placement_rows = [[fmt_dt(sub.round.created_at), anchor(player.url, sub.round.url, sub.round.name), anchor(player.url, sub.url, sub.title), str(sub.place), str(sub.total_points), f"{sub.finish_percentile * 100:.1f}%"] for sub in player.placement_history]
    signature_rows = [[anchor(player.url, model.artist_urls_by_name[name], name), str(count), str(points)] for name, count, points in player.signature_artists]
    similar_rows = [[anchor(player.url, model.players[item.other_key].url, model.players[item.other_key].name), str(item.overlap), f"{item.similarity_score * 100:.1f}%", f"{item.average_gap:.2f}"] for item in player.similar_voters]
    best_points = best.total_points if best else None
    worst_points = worst.total_points if worst else None
    best_rows = [[ "Best", anchor(player.url, sub.url, sub.title), anchor(player.url, sub.round.url, sub.round.name), str(sub.place), str(sub.total_points)] for sub in player.submissions if best_points is not None and sub.total_points == best_points]
    worst_rows = [[ "Worst", anchor(player.url, sub.url, sub.title), anchor(player.url, sub.round.url, sub.round.name), str(sub.place), str(sub.total_points)] for sub in player.submissions if worst_points is not None and sub.total_points == worst_points]
    body = "".join(
        [
            section("Career Totals", stat_grid([("Leagues", len(player.leagues)), ("Submissions", len(player.submissions)), ("Points", player.total_points), ("Average Points", player.average_points), ("Average Finish", player.average_finish), ("Avg Finish Percentile", f"{player.average_finish_percentile * 100:.1f}%"), ("Round Wins", player.round_wins)])),
            section("Per-League Splits", table(["League", "Submissions", "Points", "Average Points"], per_league)),
            section("Best And Worst Finishes", table(["Type", "Song", "Round", "Place", "Points"], best_rows + worst_rows if best and worst else [])),
            section("Placement History", table(["Date", "Round", "Song", "Place", "Points", "Finish Percentile"], placement_rows)),
            section("Signature Artists", table(["Artist", "Appearances", "Points"], signature_rows)),
            section("Most Similar Voters", "<p>This compares only songs that both players voted on and measures how close their point assignments were.</p>" + (table(["Player", "Shared Votes", "Similarity", "Average Gap"], similar_rows) if similar_rows else "<p>Not enough overlapping votes to compute similarity.</p>")),
        ]
    )
    return page_shell(model, player.name, body, model.site_dir / player.url)
