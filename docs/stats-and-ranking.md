# Stats And Ranking Logic

This document describes the most important derived metrics and sort rules used by the site.

All logic described here is implemented primarily in [`scripts/music_league/stats.py`](../scripts/music_league/stats.py).

## Core Submission Metrics

For each submission:

- `total_points`
  Sum of all points assigned in votes
- `vote_count`
  Number of voters for that submission
- `average_vote`
  `total_points / vote_count`
- `vote_stddev`
  Population standard deviation of vote values
- `vote_range`
  `max(points) - min(points)`

## Round Ranking

Within a round, submissions are sorted by:

1. total points, descending
2. voter count, descending
3. song title, ascending
4. submitter name, ascending

Placement assignment is tie-aware:

- if two submissions have the same point total and the same voter count, they receive the same `place`
- later placements skip accordingly because the generator uses competition ranking semantics

This same ordering is also used to determine the round winner.

## Round Winner

Each round has exactly one winner for summary purposes.

Winner tiebreak order:

1. total points
2. voter count
3. song title
4. submitter name

The final two fields are only deterministic fallbacks so the generator can always choose one record.

## Player Metrics

For each player:

- `total_points`
  Sum of points across all of their submissions
- `average_points`
  Mean points per submission
- `average_finish`
  Mean round place
- `average_finish_percentile`
  Mean normalized finish percentile across submissions
- `round_wins`
  Count of rounds where the player's submission is the computed round winner

### Best and worst submissions

`best_submission` is selected by:

1. lowest place
2. higher point total
3. higher voter count
4. earlier round date
5. song title

`worst_submission` is selected by:

1. highest place
2. lower point strength within that place ordering
3. earlier round date
4. song title

Player-page best/worst tables then include all submissions tied at that best or worst place.

### Signature artists

Per player, artist relationships are ranked by:

1. appearance count with that artist
2. total points earned on those submissions
3. artist name

### Similar voters

Voter similarity is calculated only for players who have at least 5 overlapping voted submissions.

For a pair of players:

1. find all submissions both players voted on
2. compute the absolute points gap on each shared submission
3. compute `average_gap`
4. compute `similarity_score = max(0, 1 - average_gap / 6)`

Presentation sort order:

1. shared votes, descending
2. similarity score, descending
3. average gap, ascending

## Artist Metrics

For each artist:

- `total_points`
  Sum of points from all submissions involving that artist
- `average_points`
  Mean points per submission involving that artist
- `leagues`
  Distinct leagues where the artist appears
- `submitters`
  Distinct players who submitted the artist

Common artist ranking variants:

- by appearances, then points
- by total points, then appearances
- by average points with minimum submission thresholds where needed

## Album Metrics

Albums are intentionally not keyed by title alone.

Album identity is based on:

- album title
- canonical set of contributing artists on the submission

This avoids merging unrelated albums that happen to share the same title.

For each album:

- `total_points`
- `average_points`
- `artists`
- `submitters`
- `leagues`

Common album ranking variants:

- by appearances, then points
- by total points, then appearances

## Song Metrics

Songs are grouped by Spotify track URI for page identity and for the songs index.

That means:

- one song page can contain multiple round usages of the same track
- alternate recordings or separate Spotify track IDs remain separate

Common song index ranking:

1. submissions / uses of the track
2. total points across those uses
3. title

## Home Page Preview Logic

The home page uses preview tables, not full datasets.

Important behavior:

- those preview tables are intentionally not sortable
- they link to full pages for complete sortable listings

## Trending Logic

Trending is based on the most recent 5 rounds globally across all leagues.

It is not based on the last 5 rounds for a specific player.

Trending player ranking is sorted by:

1. total points earned in the recent 5-round window
2. number of submissions in that same window
3. player name

## Popular Rounds

The home page uses `Most Popular Rounds` as a simple browse concept rather than a single composite score.

Current sort order:

1. number of submissions / participants
2. average points per song
3. newest round date
4. round name

## Zero-Point Songs

Zero-point songs are submissions whose `total_points` is exactly zero.

They are sorted by:

1. round date
2. song title

## Sortable Tables

Many full pages opt into a shared client-side sortable table helper.

Key properties:

- default sort column and direction are defined per table
- home-page preview tables are intentionally excluded
- sorting is client-side only
- source-generated order should still be meaningful without JavaScript

## Maintenance Notes

If ranking logic changes, update both:

1. the implementation in `stats.py`
2. this document

If a new page introduces a user-visible metric, document:

- what it measures
- what entity it applies to
- how it is sorted
- any thresholds or tie rules
