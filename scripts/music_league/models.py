from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class League:
    key: str
    name: str
    slug: str
    rounds: list["Round"] = field(default_factory=list)
    competitors: dict[str, str] = field(default_factory=dict)
    first_round_at: datetime | None = None
    last_round_at: datetime | None = None
    total_submissions: int = 0
    total_votes: int = 0
    total_points: int = 0
    player_names: set[str] = field(default_factory=set)
    url: str = ""


@dataclass
class Round:
    key: str
    id: str
    league: League
    name: str
    slug: str
    created_at: datetime
    description: str
    playlist_url: str
    submissions: list["Submission"] = field(default_factory=list)
    votes: list["Vote"] = field(default_factory=list)
    total_points: int = 0
    average_points_per_song: float = 0.0
    hall_of_fame_score: float = 0.0
    comments_count: int = 0
    url: str = ""


@dataclass
class Submission:
    key: str
    id: str
    round: Round
    league: League
    spotify_uri: str
    title: str
    album: str
    artists: list[str]
    artist_display: str
    submitter_key: str
    submitter_name: str
    created_at: datetime
    comment: str
    album_key: str = ""
    votes: list["Vote"] = field(default_factory=list)
    total_points: int = 0
    vote_count: int = 0
    average_vote: float = 0.0
    vote_stddev: float = 0.0
    vote_range: int = 0
    place: int = 0
    finish_percentile: float = 0.0
    url: str = ""


@dataclass
class Vote:
    submission: Submission
    voter_key: str
    voter_name: str
    created_at: datetime
    points: int
    comment: str


@dataclass
class PlayerSimilarity:
    other_key: str
    overlap: int
    similarity_score: float
    average_gap: float


@dataclass
class Player:
    key: str
    name: str
    slug: str
    submissions: list[Submission] = field(default_factory=list)
    votes_cast: list[Vote] = field(default_factory=list)
    total_points: int = 0
    average_points: float = 0.0
    average_finish: float = 0.0
    average_finish_percentile: float = 0.0
    round_wins: int = 0
    leagues: set[str] = field(default_factory=set)
    signature_artists: list[tuple[str, int, int]] = field(default_factory=list)
    best_rounds: list[tuple[str, int, int]] = field(default_factory=list)
    best_submission: Submission | None = None
    worst_submission: Submission | None = None
    placement_history: list[Submission] = field(default_factory=list)
    similar_voters: list[PlayerSimilarity] = field(default_factory=list)
    url: str = ""


@dataclass
class Artist:
    key: str
    name: str
    slug: str
    submissions: list[Submission] = field(default_factory=list)
    total_points: int = 0
    average_points: float = 0.0
    leagues: set[str] = field(default_factory=set)
    submitters: set[str] = field(default_factory=set)
    url: str = ""


@dataclass
class Album:
    key: str
    name: str
    slug: str
    submissions: list[Submission] = field(default_factory=list)
    total_points: int = 0
    average_points: float = 0.0
    artists: set[str] = field(default_factory=set)
    submitters: set[str] = field(default_factory=set)
    leagues: set[str] = field(default_factory=set)
    url: str = ""


@dataclass
class SiteModel:
    root: Path
    leagues_dir: Path
    site_dir: Path
    assets_dir: Path
    site_assets_dir: Path
    config_path: Path
    sample_config_path: Path
    site_title: str = "Music League Archive"
    site_description: str = ""
    leagues: list[League] = field(default_factory=list)
    rounds: list[Round] = field(default_factory=list)
    submissions: list[Submission] = field(default_factory=list)
    votes: list[Vote] = field(default_factory=list)
    players: dict[str, Player] = field(default_factory=dict)
    artists: dict[str, Artist] = field(default_factory=dict)
    albums: dict[str, Album] = field(default_factory=dict)
    round_winners: dict[str, Submission] = field(default_factory=dict)
    league_urls_by_name: dict[str, str] = field(default_factory=dict)
    player_urls_by_name: dict[str, str] = field(default_factory=dict)
    artist_urls_by_name: dict[str, str] = field(default_factory=dict)
    playlists: list[Round] = field(default_factory=list)
    latest_leagues: list[League] = field(default_factory=list)
    top_submissions: list[Submission] = field(default_factory=list)
    top_players: list[Player] = field(default_factory=list)
    trending_players: list[Player] = field(default_factory=list)
    best_average_finish_players: list[Player] = field(default_factory=list)
    top_artists_by_points: list[Artist] = field(default_factory=list)
    top_artists_by_appearances: list[Artist] = field(default_factory=list)
    cross_league_artists: list[Artist] = field(default_factory=list)
    top_albums_by_points: list[Album] = field(default_factory=list)
    top_albums_by_appearances: list[Album] = field(default_factory=list)
    best_rounds: list[Round] = field(default_factory=list)
    hall_of_fame_rounds: list[Round] = field(default_factory=list)
    most_polarizing_songs: list[Submission] = field(default_factory=list)
    zero_point_songs: list[Submission] = field(default_factory=list)
    top_similarity_pairs: list[tuple[str, str, int, float, float]] = field(default_factory=list)
    generated_at: datetime | None = None
    generation_seconds: float = 0.0
    stats: dict[str, int] = field(default_factory=dict)
