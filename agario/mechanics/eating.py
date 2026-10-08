"""Cells of different players eating each other. No pygame import."""
from .. import physics


def resolve_player_collisions(world):
    """Bigger cells eat smaller cells of OTHER players; the prey's mass is transferred.

    Cells of the same player never eat each other. A player left without cells
    is marked dead. Returns {eater_owner: fully eliminated players}.
    """
    dead = set()  # id() of eaten cells (PlayerCell is a value-comparing dataclass)
    players = [p for p in world.players if p.alive]
    last_eater = {}
    kills = {}
    for eater_owner in players:
        for eater in eater_owner.cells:
            if id(eater) in dead:
                continue
            for prey_owner in players:
                if prey_owner is eater_owner:
                    continue
                for prey in prey_owner.cells:
                    if id(prey) in dead:
                        continue
                    if physics.can_eat_cell(eater, prey):
                        eater.mass += prey.mass
                        dead.add(id(prey))
                        last_eater[prey_owner] = eater_owner
                        # Record gains even if the eater dies later in this tick.
                        if hasattr(world, "tick_peak_mass"):
                            mass = sum(c.mass for c in eater_owner.cells if id(c) not in dead)
                            world.tick_peak_mass[eater_owner] = max(
                                world.tick_peak_mass.get(eater_owner, 0), mass)
    if not dead:
        return kills
    for p in players:
        p.cells[:] = [c for c in p.cells if id(c) not in dead]
        if not p.cells:
            p.alive = False

            eater_owner = last_eater.get(p)
            if eater_owner is not None:
                kills[eater_owner] = kills.get(eater_owner, 0) + 1
    return kills
