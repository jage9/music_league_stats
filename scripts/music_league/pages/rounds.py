from __future__ import annotations

from ..models import Round, SiteModel
from ..render import anchor, fmt_dt, link_list, page_rel, page_shell, section, stat_grid, table


def render_rounds_index(model: SiteModel) -> str:
    row_html = []
    for rnd in sorted(model.rounds, key=lambda item: item.created_at, reverse=True):
        row_html.append(
            "<tr "
            + f'data-league="{rnd.league.name}" '
            + f'data-date="{rnd.created_at.date().isoformat()}" '
            + f'data-name="{rnd.name.lower()}" '
            + f'data-avg="{rnd.average_points_per_song:.2f}">'
            + f"<td>{anchor('rounds/index.html', rnd.url, rnd.name)}</td>"
            + f"<td>{anchor('rounds/index.html', rnd.league.url, rnd.league.name)}</td>"
            + f"<td>{fmt_dt(rnd.created_at)}</td>"
            + f"<td>{len(rnd.submissions)}</td>"
            + f"<td>{rnd.average_points_per_song:.2f}</td>"
            + "</tr>"
        )
    round_table = (
        '<div class="table-wrap"><table><thead><tr>'
        '<th>Round</th><th>League</th><th>Created</th><th>Submissions</th><th>Avg Points Per Song</th>'
        f"</tr></thead><tbody>{''.join(row_html)}</tbody></table></div>"
    )
    controls = """
    <div class="controls">
      <label>League<select id="league-filter"><option value="">All leagues</option></select></label>
      <label>Sort<select id="round-sort"><option value="date-desc">Newest first</option><option value="date-asc">Oldest first</option><option value="name-asc">Name</option><option value="avg-desc">Highest average score</option></select></label>
    </div>
    <script>
    (function () {
      const table = document.querySelector("tbody");
      const leagueSelect = document.getElementById("league-filter");
      const sortSelect = document.getElementById("round-sort");
      const rows = Array.from(table.querySelectorAll("tr"));
      const getLeagueKey = (row) => row.dataset.league || "";
      const getDateKey = (row) => row.dataset.date || "";
      const getNameKey = (row) => row.dataset.name || "";
      const getAvgKey = (row) => Number(row.dataset.avg || "0");
      [...new Set(rows.map((row) => getLeagueKey(row)).filter(Boolean))].sort((a, b) => a.localeCompare(b)).forEach((league) => {
        const option = document.createElement("option"); option.value = league; option.textContent = league; leagueSelect.appendChild(option);
      });
      const parseDate = (text) => new Date(text + "T00:00:00").getTime();
      function render() {
        const league = leagueSelect.value;
        const mode = sortSelect.value;
        const nextRows = rows.filter((row) => !league || getLeagueKey(row) === league);
        nextRows.sort((a, b) => {
          if (mode === "date-desc") return parseDate(getDateKey(b)) - parseDate(getDateKey(a));
          if (mode === "date-asc") return parseDate(getDateKey(a)) - parseDate(getDateKey(b));
          if (mode === "name-asc") return getNameKey(a).localeCompare(getNameKey(b));
          if (mode === "avg-desc") return getAvgKey(b) - getAvgKey(a);
          return 0;
        });
        table.replaceChildren(...nextRows);
      }
      leagueSelect.addEventListener("change", render); sortSelect.addEventListener("change", render); render();
    }());
    </script>
    """
    body = section("All Rounds", "<p>This index supports client-side filtering by league and sorting by date or score.</p>" + controls + round_table)
    return page_shell(model, "Rounds", body, model.site_dir / "rounds" / "index.html")


def render_round_page(model: SiteModel, round_obj: Round) -> str:
    artist_targets = {artist.name: artist.url for artist in model.artists.values()}
    results = [
        [
            str(sub.place),
            anchor(round_obj.url, sub.url, sub.title),
            ", ".join(anchor(round_obj.url, artist_targets[artist], artist) for artist in sub.artists),
            anchor(round_obj.url, model.players[sub.submitter_key].url, sub.submitter_name),
            str(sub.total_points),
            str(sub.vote_count),
            f"{sub.average_vote:.2f}",
        ]
        for sub in sorted(round_obj.submissions, key=lambda item: (item.place, item.title.lower()))
    ]
    comment_groups = []
    for sub in sorted(round_obj.submissions, key=lambda item: (item.place, item.title.lower())):
        song_comments = [
            (vote.voter_name, page_rel(round_obj.url, sub.url), vote.comment)
            for vote in sorted(sub.votes, key=lambda item: (-item.points, item.voter_name.lower()))
            if vote.comment
        ]
        if song_comments:
            comment_groups.append(
                "<article class=\"panel\">"
                + f"<h3>{anchor(round_obj.url, sub.url, sub.title)}</h3>"
                + f"<p>{', '.join(anchor(round_obj.url, artist_targets[artist], artist) for artist in sub.artists)}. "
                + f"{anchor(round_obj.url, model.players[sub.submitter_key].url, sub.submitter_name)}.</p>"
                + link_list(song_comments)
                + "</article>"
            )
    submission_notes = "<ul>" + "".join(f"<li><strong>{sub.title}</strong> by {sub.artist_display}. {sub.comment}</li>" for sub in round_obj.submissions if sub.comment) + "</ul>" if any(sub.comment for sub in round_obj.submissions) else "<p>No submission comments were captured for this round.</p>"
    body = "".join(
        [
            section("Round Summary", stat_grid([("Created", fmt_dt(round_obj.created_at)), ("Submissions", len(round_obj.submissions)), ("Votes", len(round_obj.votes)), ("Total Points", round_obj.total_points), ("Avg Points Per Song", round_obj.average_points_per_song)])),
            section("Prompt", f"<p>{round_obj.description or 'No description provided.'}</p>"),
            section("Spotify Playlist", f'<p><a href="{round_obj.playlist_url}" target="_blank" rel="noopener noreferrer">{round_obj.playlist_url}</a></p>' if round_obj.playlist_url else "<p>No playlist URL was available.</p>"),
            section("Results", table(["Place", "Song", "Artist", "Submitter", "Points", "Voters", "Average Vote"], results)),
            section("Submission Notes", submission_notes),
            section("Vote Comments", "<p>No vote comments were captured for this round.</p>" if not comment_groups else "".join(comment_groups)),
        ]
    )
    return page_shell(model, round_obj.name, body, model.site_dir / round_obj.url)
