"""Pure leaderboard ranking. No pygame import."""


def rank_players(players, local_player, top=10):
    """Return (1-based rank, player) rows, appending a living local outside top.

    Equal masses retain the input order. Dead players and empty players are omitted.
    """
    if top < 0:
        raise ValueError("top must be non-negative")
    ranked = sorted((p for p in players if p.alive and p.cells),
                    key=lambda p: p.total_mass, reverse=True)
    rows = list(enumerate(ranked, start=1))
    result = rows[:top]
    result.extend((rank, player) for rank, player in rows[top:]
                  if player is local_player)
    return result
