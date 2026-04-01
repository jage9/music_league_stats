from __future__ import annotations

import time
from datetime import datetime

from music_league.data_loader import load_model
from music_league.render import build_site
from music_league.stats import enrich_model


def main() -> None:
    started = time.perf_counter()
    model = load_model()
    enrich_model(model)
    model.generated_at = datetime.now().astimezone()
    model.generation_seconds = time.perf_counter() - started
    build_site(model)
    print(f"Generated site at: {model.site_dir}")
    print(f"Leagues: {model.stats['league_count']}")
    print(f"Rounds: {model.stats['round_count']}")
    print(f"Players: {model.stats['player_count']}")
    print(f"Artists: {model.stats['artist_count']}")
    print(f"Albums: {model.stats['album_count']}")
    print(f"Songs: {model.stats['submission_count']}")
    print(f"Votes: {model.stats['vote_count']}")
    print(f"Build seconds: {model.generation_seconds:.3f}")


if __name__ == "__main__":
    main()
