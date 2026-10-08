"""Cells of different players eating each other. No pygame import."""
from .. import physics


def resolve_player_collisions(world):
    """Bigger cells eat smaller cells of OTHER players; the prey's mass is transferred.

    Cells of the same player never eat each other. A player left without cells
    is marked dead.
    """
    dead = set()  # id() of eaten cells (PlayerCell is a value-comparing dataclass)
    players = [p for p in world.players if p.alive]
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
    if not dead:
        return
    for p in players:
        p.cells[:] = [c for c in p.cells if id(c) not in dead]
        if not p.cells:
            p.alive = False
