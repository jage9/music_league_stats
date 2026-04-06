# Data Schema

This document describes the logical schema used inside the generator after CSV loading and normalization.

## Source Tables

### competitors.csv

Purpose:

- Maps Music League competitor IDs to display names within a league export

Core fields used by the loader:

- `ID`
- `Name`

### rounds.csv

Purpose:

- Defines round-level metadata

Core fields used by the loader:

- `ID`
- `Name`
- `Created`
- `Description`
- `Playlist URL`

### submissions.csv

Purpose:

- Defines one submitted track in one round

Core fields used by the loader:

- `Round ID`
- `Spotify URI`
- `Title`
- `Album`
- `Artist(s)`
- `Submitter ID`
- `Created`
- `Comment`

### votes.csv

Purpose:

- Defines one player's points assignment to one submitted track

Core fields used by the loader:

- `Round ID`
- `Spotify URI`
- `Voter ID`
- `Created`
- `Points Assigned`
- `Comment`

## In-Memory Objects

These types are defined in [`scripts/music_league/models.py`](../scripts/music_league/models.py).

### League

Represents one source league folder.

Important fields:

- `key`
  Stable internal key, currently the league directory name
- `name`
  Human-readable league name
- `rounds`
  Ordered list of `Round` objects
- `competitors`
  Map of source competitor ID to player name
- `first_round_at` / `last_round_at`
- `total_submissions`
- `total_votes`
- `total_points`
- `url`

### Round

Represents one prompt/round inside a league.

Important fields:

- `key`
  Internal unique key combining league and round ID
- `league`
  Parent `League`
- `name`
- `created_at`
- `description`
- `playlist_url`
- `submissions`
- `votes`
- `total_points`
- `average_points_per_song`
- `comments_count`
- `url`

### Submission

Represents one submitted track in one round.

Important fields:

- `key`
  Internal key combining league, round, and Spotify URI
- `round`
- `league`
- `spotify_uri`
- `title`
- `album`
- `artists`
  Parsed list of artist names
- `artist_display`
  Display string built from `artists`
- `submitter_key`
- `submitter_name`
- `comment`
- `album_key`
  Derived identity used to avoid merging unrelated albums with the same title
- `votes`
- `total_points`
- `vote_count`
  Count of voters for this submission
- `average_vote`
- `vote_stddev`
- `vote_range`
- `place`
- `finish_percentile`
- `url`

Important identity rule:

- Song detail pages collapse repeated uses of the same Spotify track URI into a single page.
- A submission still remains round-specific in the in-memory model.

### Vote

Represents one player's vote on one submission.

Important fields:

- `submission`
- `voter_key`
- `voter_name`
- `created_at`
- `points`
- `comment`

### Player

Derived from submission and vote data, not from a separate top-level source table.

Important fields:

- `key`
- `name`
- `submissions`
- `votes_cast`
- `total_points`
- `average_points`
- `average_finish`
- `average_finish_percentile`
- `round_wins`
- `leagues`
- `signature_artists`
- `best_submission`
- `worst_submission`
- `placement_history`
- `similar_voters`
- `url`

### Artist

Derived aggregate keyed by canonical artist name.

Important fields:

- `key`
- `name`
- `submissions`
- `total_points`
- `average_points`
- `leagues`
- `submitters`
- `url`

### Album

Derived aggregate keyed by album title plus artist-set identity.

Important fields:

- `key`
- `name`
- `submissions`
- `total_points`
- `average_points`
- `artists`
- `submitters`
- `leagues`
- `url`

### SiteModel

Top-level container for everything needed during render.

Important categories:

- filesystem paths
- site title, description, and version
- primary collections: leagues, rounds, submissions, votes
- derived aggregate maps: players, artists, albums
- precomputed ranking lists for page generation
- generated timestamp and build duration
- summary counts in `stats`

## Normalization Rules

Implemented in [`scripts/music_league/data_loader.py`](../scripts/music_league/data_loader.py).

### Text normalization

The loader:

- strips repeated whitespace
- normalizes quote and dash characters
- attempts light mojibake repair
- trims surrounding whitespace

### Canonical keys

Canonical keys are lowercased, accent-folded, and stripped to alphanumeric content so objects can be matched across source files and across leagues.

### Artist parsing

The loader attempts to split multi-artist fields while preserving some band-style names that contain commas. This is heuristic logic because source exports do not fully disambiguate all artist-credit patterns.

## URL Model

Each major entity gets a generated URL:

- leagues: `leagues/<slug>/index.html`
- rounds: `rounds/<slug>/index.html`
- players: `players/<slug>/index.html`
- artists: `artists/<slug>/index.html`
- albums: `albums/<slug>/index.html`
- songs: `songs/<slug>/index.html`

Song URL assignment is special:

- repeated uses of the same Spotify track URI share one song page URL
- duplicate slug collisions are disambiguated by suffixing
