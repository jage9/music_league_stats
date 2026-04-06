from __future__ import annotations

import csv
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from .models import League, Round, SiteModel, Submission, Vote
from .site_meta import SITE_VERSION


def slugify(value: str) -> str:
    text = canonical_text(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "item"


def canonical_key(value: str) -> str:
    text = canonical_text(value).casefold()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text or "item"


def repair_mojibake(value: str) -> str:
    if not value:
        return value
    suspicious = ("Ã", "Â", "ƒ", "‚", "\x92", "\x93", "\x94")
    if any(token in value for token in suspicious):
        try:
            repaired = value.encode("cp1252", errors="ignore").decode("utf-8", errors="ignore")
            if repaired:
                value = repaired
        except Exception:
            pass
    return value


def canonical_text(value: str) -> str:
    value = repair_mojibake(value or "")
    value = value.replace("‚", ",").replace("¢", "›").replace("¤", "")
    value = value.replace("\u2018", "'").replace("\u2019", "'")
    value = value.replace("\u201c", '"').replace("\u201d", '"')
    value = value.replace("\u2013", "-").replace("\u2014", "-")
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def split_artist_field(value: str) -> list[str]:
    text = canonical_text(value)
    if not text:
        return []
    if "," not in text:
        return [text]
    if _looks_like_single_band_name(text):
        return [text]
    return [canonical_text(part) for part in text.split(",") if canonical_text(part)]


def _looks_like_single_band_name(text: str) -> bool:
    if text.count(",") != 1 or text.count("&") != 1:
        return False
    left, right = [part.strip() for part in text.split(",", 1)]
    if not left or not right or "&" not in right:
        return False
    first, second = [part.strip() for part in right.split("&", 1)]
    tokens = [left, first, second]
    return all(_is_single_name_token(token) for token in tokens)


def _is_single_name_token(token: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9.'-]+", token))


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [{canonical_text(key): canonical_text(val) for key, val in row.items()} for row in rows]


def load_site_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return {
        "title": canonical_text(str(raw.get("title", ""))),
        "description": canonical_text(str(raw.get("description", ""))),
    }


def load_model() -> SiteModel:
    root = Path(__file__).resolve().parents[2]
    model = SiteModel(
        root=root,
        leagues_dir=root / "leagues",
        site_dir=root / "site",
        assets_dir=root / "assets",
        site_assets_dir=root / "site" / "assets",
        config_path=root / "config.json",
        sample_config_path=root / "config.sample.json",
        site_version=SITE_VERSION,
    )
    config = load_site_config(model.config_path)
    if config.get("title"):
        model.site_title = config["title"]
    if config.get("description"):
        model.site_description = config["description"]
    rounds_by_key: dict[str, Round] = {}
    submissions_by_key: dict[str, Submission] = {}
    league_dirs = sorted((path for path in model.leagues_dir.iterdir() if path.is_dir()), key=lambda path: path.name.lower())

    for league_dir in league_dirs:
        league = League(key=league_dir.name, name=canonical_text(league_dir.name), slug=slugify(league_dir.name))
        competitors_rows = read_csv(league_dir / "competitors.csv")
        rounds_rows = read_csv(league_dir / "rounds.csv")
        submissions_rows = read_csv(league_dir / "submissions.csv")
        votes_rows = read_csv(league_dir / "votes.csv")

        for row in competitors_rows:
            player_name = canonical_text(row["Name"])
            league.competitors[row["ID"]] = player_name
            league.player_names.add(player_name)
        league.total_votes = len(votes_rows)

        for row in rounds_rows:
            round_obj = Round(
                key=f"{league.key}::{row['ID']}",
                id=row["ID"],
                league=league,
                name=canonical_text(row["Name"]),
                slug=f"{slugify(league.name)}-{slugify(row['Name'])}-{row['ID'][:8]}",
                created_at=parse_dt(row["Created"]),
                description=canonical_text(row.get("Description", "")),
                playlist_url=canonical_text(row.get("Playlist URL", "")),
            )
            league.rounds.append(round_obj)
            model.rounds.append(round_obj)
            rounds_by_key[round_obj.key] = round_obj

        league.rounds.sort(key=lambda item: item.created_at)
        if league.rounds:
            league.first_round_at = league.rounds[0].created_at
            league.last_round_at = league.rounds[-1].created_at

        for row in submissions_rows:
            round_obj = rounds_by_key[f"{league.key}::{row['Round ID']}"]
            submitter_name = league.competitors.get(row["Submitter ID"], canonical_text(row["Submitter ID"]))
            artists = split_artist_field(row["Artist(s)"])
            submission = Submission(
                key=f"{league.key}::{row['Round ID']}::{row['Spotify URI']}",
                id=row["Spotify URI"].split(":")[-1],
                round=round_obj,
                league=league,
                spotify_uri=row["Spotify URI"],
                title=canonical_text(row["Title"]),
                album=canonical_text(row["Album"]),
                artists=artists,
                artist_display=", ".join(artists),
                submitter_key=canonical_key(submitter_name),
                submitter_name=submitter_name,
                created_at=parse_dt(row["Created"]),
                comment=canonical_text(row.get("Comment", "")),
            )
            round_obj.submissions.append(submission)
            model.submissions.append(submission)
            submissions_by_key[submission.key] = submission
            league.total_submissions += 1

        for row in votes_rows:
            submission = submissions_by_key.get(f"{league.key}::{row['Round ID']}::{row['Spotify URI']}")
            if submission is None:
                continue
            voter_name = league.competitors.get(row["Voter ID"], canonical_text(row["Voter ID"]))
            vote = Vote(
                submission=submission,
                voter_key=canonical_key(voter_name),
                voter_name=voter_name,
                created_at=parse_dt(row["Created"]),
                points=int(row["Points Assigned"] or 0),
                comment=canonical_text(row.get("Comment", "")),
            )
            submission.votes.append(vote)
            submission.round.votes.append(vote)
            model.votes.append(vote)

        model.leagues.append(league)

    return model
