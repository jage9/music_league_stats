from __future__ import annotations

from ..models import SiteModel, Submission
from ..render import anchor, page_shell, section, spotify_track_url, stat_grid_html, table


def render_songs_index(model: SiteModel) -> str:
    rows = [[anchor("songs/index.html", sub.url, sub.title), sub.artist_display, anchor("songs/index.html", model.players[sub.submitter_key].url, sub.submitter_name), anchor("songs/index.html", sub.round.url, sub.round.name), anchor("songs/index.html", sub.league.url, sub.league.name), str(sub.total_points), str(sub.vote_count)] for sub in sorted(model.submissions, key=lambda item: (-item.total_points, item.title.lower()))]
    return page_shell(model, "Songs", section("Songs", table(["Song", "Artist", "Submitter", "Round", "League", "Points", "Voters"], rows)), model.site_dir / "songs" / "index.html")


def render_song_page(model: SiteModel, submission: Submission) -> str:
    related_submissions = [item for item in model.submissions if item.spotify_uri == submission.spotify_uri]
    artist_targets = {artist.name: artist.url for artist in model.artists.values()}
    album_target = next((album.url for album in model.albums.values() if album.name == submission.album), None)
    summary_cards = [
        (
            "Artist",
            ", ".join(anchor(submission.url, artist_targets[name], name) for name in submission.artists),
        ),
        (
            "Album",
            anchor(submission.url, album_target, submission.album) if album_target else submission.album,
        ),
        (
            "Uses",
            str(len(related_submissions)),
        ),
        (
            "Track Link",
            f'<a href="{spotify_track_url(submission.spotify_uri)}" target="_blank" rel="noopener noreferrer">{spotify_track_url(submission.spotify_uri)}</a>'
            if spotify_track_url(submission.spotify_uri)
            else "No Spotify track URL could be derived from this URI.",
        ),
    ]
    usage_sections: list[str] = []
    for item in sorted(related_submissions, key=lambda entry: (entry.round.created_at, entry.round.name.lower(), entry.submitter_name.lower())):
        vote_rows = [
            [
                anchor(item.url, model.players[vote.voter_key].url, vote.voter_name) if vote.voter_key in model.players else vote.voter_name,
                str(vote.points),
                vote.comment,
            ]
            for vote in sorted(item.votes, key=lambda row: (-row.points, row.voter_name.lower()))
        ]
        usage_sections.append(
            "".join(
                [
                    f"<section><h2>{anchor(item.url, item.round.url, item.round.name)}</h2>",
                    stat_grid_html(
                        [
                            ("League", anchor(item.url, item.league.url, item.league.name)),
                            ("Submitter", anchor(item.url, model.players[item.submitter_key].url, item.submitter_name)),
                            ("Created", item.created_at.strftime("%B %d, %Y")),
                            ("Points", str(item.total_points)),
                            ("Voters", str(item.vote_count)),
                            ("Average Vote", f"{item.average_vote:.2f}"),
                            ("Vote Std Dev", f"{item.vote_stddev:.2f}"),
                            ("Place", str(item.place)),
                        ]
                    ),
                    f"<section><h3>Submission Comment</h3><p>{item.comment or 'No submission comment provided.'}</p></section>",
                    f"<section><h3>Vote Breakdown</h3>{table(['Voter', 'Points', 'Comment'], vote_rows)}</section>",
                    "</section>",
                ]
            )
        )
    body = "".join(
        [
            section("Song Summary", stat_grid_html(summary_cards)),
            "".join(usage_sections),
        ]
    )
    browser_title = f"{submission.title} by {submission.artist_display}"
    return page_shell(model, submission.title, body, model.site_dir / submission.url, browser_title=browser_title)
