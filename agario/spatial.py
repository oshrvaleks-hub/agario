"""Uniform-grid spatial index for static points. No pygame import."""
import math

from . import config


class SpatialGrid:
    """Buckets objects with `.x`/`.y` into square cells for fast area queries.

    Objects must not move while stored (use remove + add to relocate them).
    Buckets are keyed by id(), so equal-valued dataclasses stay distinct.
    """

    def __init__(self, cell_size=config.SPATIAL_CELL_SIZE):
        self.cell_size = cell_size
        self._buckets = {}   # (cx, cy) -> {id(obj): obj}
        self._keys = {}      # id(obj) -> (cx, cy)

    def __len__(self):
        return len(self._keys)

    def _key(self, x, y):
        s = self.cell_size
        return math.floor(x / s), math.floor(y / s)

    def add(self, obj):
        if id(obj) in self._keys:
            return
        key = self._key(obj.x, obj.y)
        self._keys[id(obj)] = key
        self._buckets.setdefault(key, {})[id(obj)] = obj

    def remove(self, obj):
        key = self._keys.pop(id(obj), None)
        if key is None:
            return False
        bucket = self._buckets[key]
        del bucket[id(obj)]
        if not bucket:
            del self._buckets[key]
        return True

    def clear(self):
        self._buckets.clear()
        self._keys.clear()

    def query_rect(self, x0, y0, x1, y1):
        """Objects with x0 <= x <= x1 and y0 <= y <= y1 (edges inclusive)."""
        cx0, cy0 = self._key(x0, y0)
        cx1, cy1 = self._key(x1, y1)
        out = []
        buckets = self._buckets
        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                bucket = buckets.get((cx, cy))
                if bucket:
                    out.extend(o for o in bucket.values()
                               if x0 <= o.x <= x1 and y0 <= o.y <= y1)
        return out

    def query_circle(self, x, y, radius):
        """Objects whose distance to (x, y) is <= radius."""
        r2 = radius * radius
        return [o for o in self.query_rect(x - radius, y - radius, x + radius, y + radius)
                if (o.x - x) ** 2 + (o.y - y) ** 2 <= r2]

    def nearest(self, x, y, max_radius):
        """Closest object within max_radius of (x, y), or None."""
        s = self.cell_size
        cx, cy = self._key(x, y)
        best, best_d2 = None, max_radius * max_radius
        max_ring = int(max_radius // s) + 1
        for ring in range(max_ring + 1):
            # Every cell in this ring is at least (ring - 1) * s away.
            if best is not None and best_d2 <= ((ring - 1) * s) ** 2:
                break
            for dx in range(-ring, ring + 1):
                for dy in range(-ring, ring + 1):
                    if max(abs(dx), abs(dy)) != ring:
                        continue
                    bucket = self._buckets.get((cx + dx, cy + dy))
                    if not bucket:
                        continue
                    for o in bucket.values():
                        d2 = (o.x - x) ** 2 + (o.y - y) ** 2
                        if d2 <= best_d2 and (best is None or d2 < best_d2):
                            best, best_d2 = o, d2
        return best


class SpatialList(list):
    """A list that keeps a SpatialGrid in sync with its contents.

    Behaves like a normal list for callers (append, remove, slice assignment...).
    Rare bulk mutations simply rebuild the grid.
    """

    def __init__(self, items=(), cell_size=config.SPATIAL_CELL_SIZE):
        super().__init__(items)
        self.grid = SpatialGrid(cell_size)
        self._rebuild()

    def _rebuild(self):
        self.grid.clear()
        for o in self:
            self.grid.add(o)

    def append(self, obj):
        super().append(obj)
        self.grid.add(obj)

    def extend(self, items):
        items = list(items)
        super().extend(items)
        for o in items:
            self.grid.add(o)

    def insert(self, index, obj):
        super().insert(index, obj)
        self.grid.add(obj)

    def remove(self, obj):
        super().remove(obj)
        # Equal-valued items may have been removed in place of `obj`: resync cheaply.
        self._rebuild()

    def pop(self, *args):
        obj = super().pop(*args)
        self.grid.remove(obj)
        return obj

    def remove_many(self, objs):
        """Remove the given objects (by identity) in one pass."""
        dead = {id(o) for o in objs}
        if not dead:
            return
        super().__setitem__(slice(None), [o for o in self if id(o) not in dead])
        for o in objs:
            self.grid.remove(o)

    def clear(self):
        super().clear()
        self.grid.clear()

    def __setitem__(self, index, value):
        super().__setitem__(index, value)
        self._rebuild()

    def __delitem__(self, index):
        super().__delitem__(index)
        self._rebuild()

    def __iadd__(self, items):
        self.extend(items)
        return self
