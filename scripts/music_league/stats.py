from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone

from .data_loader import canonical_key, slugify
from .models import Album, Artist, Player, PlayerSimilarity, SiteModel


def _round_winner_submission(round_obj) -> object | None:
    if not round_obj.submissions:
        return None
    return sorted(
        round_obj.submissions,
        key=lambda item: (-item.total_points, -item.vote_count, item.title.lower(), item.submitter_name.lower()),
    )[0]


def _album_key(submission) -> str:
    album_name = submission.album or "Unknown Album"
    artist_part = "||".join(canonical_key(artist) for artist in sorted(set(submission.artists)))
    return canonical_key(f"{album_name}||{artist_part}")


def enrich_model(model: SiteModel) -> None:
    player_map: dict[str, Player] = {}
    artist_map: dict[str, Artist] = {}
    album_map: dict[str, Album] = {}
    vote_vectors: dict[str, dict[str, int]] = defaultdict(dict)

    for submission in model.submissions:
        points = [vote.points for vote in submission.votes]
        submission.total_points = sum(points)
        submission.vote_count = len(points)
        submission.average_vote = submission.total_points / submission.vote_count if submission.vote_count else 0.0
        submission.vote_stddev = statistics.pstdev(points) if len(points) > 1 else 0.0
        submission.vote_range = max(points) - min(points) if points else 0
        submission.league.total_points += submission.total_points

        player = player_map.setdefault(
            submission.submitter_key,
            Player(key=submission.submitter_key, name=submission.submitter_name, slug=slugify(submission.submitter_name)),
        )
        player.submissions.append(submission)
        player.leagues.add(submission.league.name)

        for vote in submission.votes:
            voter = player_map.setdefault(vote.voter_key, Player(key=vote.voter_key, name=vote.voter_name, slug=slugify(vote.voter_name)))
            voter.votes_cast.append(vote)
            vote_vectors[vote.voter_key][submission.key] = vote.points

        for artist_name in submission.artists:
            artist = artist_map.setdefault(canonical_key(artist_name), Artist(key=canonical_key(artist_name), name=artist_name, slug=slugify(artist_name)))
            artist.submissions.append(submission)
            artist.leagues.add(submission.league.name)
            artist.submitters.add(submission.submitter_name)

        album_name = submission.album or "Unknown Album"
        album_key = _album_key(submission)
        album = album_map.setdefault(album_key, Album(key=album_key, name=album_name, slug=slugify(album_name)))
        album.submissions.append(submission)
        album.artists.update(submission.artists)
        album.submitters.add(submission.submitter_name)
        album.leagues.add(submission.league.name)

    for round_obj in model.rounds:
        ranked = sorted(round_obj.submissions, key=lambda item: (-item.total_points, item.title.lower(), item.submitter_name.lower()))
        round_obj.total_points = sum(item.total_points for item in round_obj.submissions)
        round_obj.average_points_per_song = round_obj.total_points / len(round_obj.submissions) if round_obj.submissions else 0.0
        round_obj.comments_count = sum(1 for vote in round_obj.votes if vote.comment)
        last_points = None
        current_place = 0
        for index, submission in enumerate(ranked, start=1):
            if submission.total_points != last_points:
                current_place = index
                last_points = submission.total_points
            submission.place = current_place
            field_size = len(ranked)
            submission.finish_percentile = 1.0 if field_size <= 1 else 1.0 - ((current_place - 1) / (field_size - 1))
        round_obj.hall_of_fame_score = round_obj.average_points_per_song * math.log2(len(round_obj.submissions) + 1) + (round_obj.comments_count * 0.15)

    for player in player_map.values():
        player.placement_history = sorted(player.submissions, key=lambda item: item.round.created_at)
        player.total_points = sum(sub.total_points for sub in player.submissions)
        player.average_points = player.total_points / len(player.submissions) if player.submissions else 0.0
        player.average_finish = sum(sub.place for sub in player.submissions) / len(player.submissions) if player.submissions else 0.0
        player.average_finish_percentile = sum(sub.finish_percentile for sub in player.submissions) / len(player.submissions) if player.submissions else 0.0
        player.round_wins = sum(1 for round_obj in model.rounds if (_round_winner_submission(round_obj) and _round_winner_submission(round_obj).submitter_key == player.key))
        player.best_submission = max(player.submissions, key=lambda item: (item.total_points, item.finish_percentile), default=None)
        player.worst_submission = min(player.submissions, key=lambda item: (item.total_points, item.finish_percentile), default=None)

        artist_counter = Counter()
        artist_points = Counter()
        round_counter = Counter()
        round_points = Counter()
        for sub in player.submissions:
            round_counter[(sub.league.name, sub.round.name)] += 1
            round_points[(sub.league.name, sub.round.name)] += sub.total_points
            for artist_name in sub.artists:
                artist_counter[artist_name] += 1
                artist_points[artist_name] += sub.total_points
        player.signature_artists = sorted(
            [(name, count, artist_points[name]) for name, count in artist_counter.items()],
            key=lambda item: (-item[1], -item[2], item[0].lower()),
        )[:8]
        player.best_rounds = sorted(
            [(f"{league} / {round_name}", round_counter[(league, round_name)], round_points[(league, round_name)]) for league, round_name in round_counter],
            key=lambda item: (-item[2], -item[1], item[0].lower()),
        )[:8]

    similarity_pairs: list[tuple[str, str, int, float, float]] = []
    player_keys = sorted(vote_vectors)
    for idx, left_key in enumerate(player_keys):
        for right_key in player_keys[idx + 1 :]:
            left_votes = vote_vectors[left_key]
            right_votes = vote_vectors[right_key]
            shared = sorted(set(left_votes) & set(right_votes))
            if len(shared) < 5:
                continue
            gaps = [abs(left_votes[key] - right_votes[key]) for key in shared]
            average_gap = sum(gaps) / len(gaps)
            similarity = max(0.0, 1.0 - (average_gap / 6.0))
            similarity_pairs.append((left_key, right_key, len(shared), similarity, average_gap))
            player_map[left_key].similar_voters.append(PlayerSimilarity(other_key=right_key, overlap=len(shared), similarity_score=similarity, average_gap=average_gap))
            player_map[right_key].similar_voters.append(PlayerSimilarity(other_key=left_key, overlap=len(shared), similarity_score=similarity, average_gap=average_gap))

    for player in player_map.values():
        player.similar_voters.sort(key=lambda item: (-item.overlap, -item.similarity_score, item.average_gap, item.other_key))
        player.similar_voters = player.similar_voters[:8]

    for artist in artist_map.values():
        artist.total_points = sum(sub.total_points for sub in artist.submissions)
        artist.average_points = artist.total_points / len(artist.submissions) if artist.submissions else 0.0

    for album in album_map.values():
        album.total_points = sum(sub.total_points for sub in album.submissions)
        album.average_points = album.total_points / len(album.submissions) if album.submissions else 0.0

    model.players = _assign_urls(
        dict(sorted(player_map.items(), key=lambda item: item[1].name.lower())),
        "players",
    )
    model.artists = _assign_urls(
        dict(sorted(artist_map.items(), key=lambda item: item[1].name.lower())),
        "artists",
    )
    model.albums = _assign_urls(
        dict(sorted(album_map.items(), key=lambda item: item[1].name.lower())),
        "albums",
    )

    for league in model.leagues:
        league.url = f"leagues/{league.slug}/index.html"
    for round_obj in model.rounds:
        round_obj.url = f"rounds/{round_obj.slug}/index.html"
    _assign_submission_urls(model)

    model.playlists = sorted([round_obj for round_obj in model.rounds if round_obj.playlist_url], key=lambda item: item.created_at, reverse=True)
    model.latest_leagues = sorted([league for league in model.leagues if league.last_round_at], key=lambda item: item.last_round_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    model.top_submissions = sorted(model.submissions, key=lambda item: (-item.total_points, -item.vote_count, item.title.lower()))[:30]
    model.top_players = sorted(model.players.values(), key=lambda item: (-item.total_points, -item.average_points, item.name.lower()))[:30]
    model.best_average_finish_players = sorted([item for item in model.players.values() if len(item.submissions) >= 5], key=lambda item: (-item.average_finish_percentile, -item.average_points, item.name.lower()))[:30]
    model.top_artists_by_points = sorted(model.artists.values(), key=lambda item: (-item.total_points, -len(item.submissions), item.name.lower()))[:30]
    model.top_artists_by_appearances = sorted(model.artists.values(), key=lambda item: (-len(item.submissions), -item.total_points, item.name.lower()))[:30]
    model.cross_league_artists = sorted([item for item in model.artists.values() if len(item.leagues) > 1], key=lambda item: (-len(item.leagues), -len(item.submissions), item.name.lower()))[:30]
    model.top_albums_by_points = sorted(model.albums.values(), key=lambda item: (-item.total_points, -len(item.submissions), item.name.lower()))[:30]
    model.top_albums_by_appearances = sorted(model.albums.values(), key=lambda item: (-len(item.submissions), -item.total_points, item.name.lower()))[:30]
    model.best_rounds = sorted(model.rounds, key=lambda item: (-item.average_points_per_song, -len(item.submissions), item.name.lower()))[:30]
    model.hall_of_fame_rounds = sorted(
        model.rounds,
        key=lambda item: (-len(item.submissions), -item.average_points_per_song, -(item.created_at.timestamp()), item.name.lower()),
    )[:30]
    model.most_polarizing_songs = sorted([item for item in model.submissions if item.vote_count >= 5], key=lambda item: (-item.vote_stddev, -item.vote_range, -item.total_points, item.title.lower()))[:30]
    model.zero_point_songs = sorted([item for item in model.submissions if item.total_points == 0], key=lambda item: (item.round.created_at, item.title.lower()))
    model.top_similarity_pairs = [
        (
            model.players[left].name,
            model.players[right].name,
            overlap,
            similarity,
            gap,
        )
        for left, right, overlap, similarity, gap in sorted(similarity_pairs, key=lambda item: (-item[2], -item[3], item[4], item[0], item[1]))[:30]
    ]
    model.stats = {
        "league_count": len(model.leagues),
        "round_count": len(model.rounds),
        "submission_count": len(model.submissions),
        "vote_count": len(model.votes),
        "player_count": len(model.players),
        "artist_count": len(model.artists),
        "album_count": len(model.albums),
        "playlist_count": len(model.playlists),
        "zero_point_count": len(model.zero_point_songs),
    }


def _assign_urls(items: dict[str, object], folder: str) -> dict[str, object]:
    used: Counter[str] = Counter()
    for item in items.values():
        used[item.slug] += 1
        if used[item.slug] > 1:
            item.slug = f"{item.slug}-{used[item.slug]}"
        item.url = f"{folder}/{item.slug}/index.html"
    return items


def _assign_submission_urls(model: SiteModel) -> None:
    uri_to_url: dict[str, str] = {}
    used: Counter[str] = Counter()
    for submission in model.submissions:
        if submission.spotify_uri in uri_to_url:
            submission.url = uri_to_url[submission.spotify_uri]
            continue
        slug = f"{slugify(submission.title)}-{submission.id[:8]}"
        used[slug] += 1
        if used[slug] > 1:
            slug = f"{slug}-{used[slug]}"
        submission.url = f"songs/{slug}/index.html"
        uri_to_url[submission.spotify_uri] = submission.url
