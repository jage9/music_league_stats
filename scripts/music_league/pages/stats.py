from __future__ import annotations

from ..models import SiteModel
from ..render import anchor, page_shell, section, table


def render_stats_index(model: SiteModel) -> str:
    finish_rows = [[anchor("stats/index.html", player.url, player.name), str(len(player.submissions)), f"{player.average_finish_percentile * 100:.1f}%", str(player.round_wins)] for player in model.best_average_finish_players[:15]]
    similarity_rows = [[left, right, str(overlap), f"{similarity * 100:.1f}%", f"{gap:.2f}"] for left, right, overlap, similarity, gap in model.top_similarity_pairs[:20]]
    zero_rows = [[anchor("stats/index.html", sub.url, sub.title), sub.artist_display, anchor("stats/index.html", model.players[sub.submitter_key].url, sub.submitter_name), anchor("stats/index.html", sub.round.url, sub.round.name), anchor("stats/index.html", sub.league.url, sub.league.name)] for sub in model.zero_point_songs]
    body = "".join(
        [
            section("Best Average Finish", table(["Player", "Submissions", "Finish Percentile", "Wins"], finish_rows)),
            section("Voting Similarity", "<p>Similarity is based on how closely two players scored the same songs when both voted on them. Smaller average gap means more alignment.</p>" + table(["Player A", "Player B", "Shared Votes", "Similarity", "Average Gap"], similarity_rows)),
            section("Zero-Point List", table(["Song", "Artist", "Submitter", "Round", "League"], zero_rows)),
        ]
    )
    return page_shell(model, "Stats Extras", body, model.site_dir / "stats" / "index.html")
