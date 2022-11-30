"""
A simple tilemap doesn't need to use the Tiled editor. It uses an array of
numbers to keep track of tile types.
"""
from __future__ import annotations
from .. import Component, Rectangle
from .... import Vector, Surface, Draw


class SimpleTilemap(Component):

    def __init__(
        self,
        tilemap: list[list[int]],
        tiles: list[Surface],
        tile_size: Vector | tuple[int, int] = (32, 32),
        collision: list[int] = [],
        collider_tag: list[str] = [],
        scale: Vector | tuple[float, float] = (1, 1),
        offset: Vector | tuple[float, float] = (0, 0),
        rot_offset: float = 0,
        z_index: int = 0,
        hidden: bool = False
    ):
        super().__init__(offset, rot_offset, z_index, hidden)

        self._map = tilemap
        self._tiles = tiles
        self._tile_size = Vector.create(tile_size)
        self._collision = collision
        self._collider_tag = collider_tag
        self.scale = Vector.create(scale)
        self._result = Surface(1, 1, scale)

        self.uptodate = False

    @property
    def tilemap(self) -> list[list[int]]:
        return self._map

    @tilemap.setter
    def tilemap(self, value: list[list[int]]):
        self._map = value
        self.uptodate = False

    @property
    def tiles(self) -> list[Surface]:
        return self._tiles

    @tiles.setter
    def tiles(self, value: list[Surface]):
        self._tiles = value
        self.uptodate = False

    @property
    def tile_size(self) -> Vector:
        return self._tile_size

    @tile_size.setter
    def tile_size(self, value: Vector | tuple[int, int]):
        self._tile_size = Vector.create(value)
        self.uptodate = False

    @property
    def collision(self) -> list[int]:
        return self._collision

    @collision.setter
    def collision(self, value: list[int]):
        self._collision = value
        self.uptodate = False

    @property
    def collider_tag(self) -> list[str]:
        return self._collider_tag

    @collider_tag.setter
    def collider_tag(self, value: list[str]):
        self._collider_tag = value
        self.uptodate = False

    def _regen(self):
        dims = max([len(row) for row in self._map]), len(self._map)
        self._result = Surface(int(dims[0] * self.tile_size.x), int(dims[1] * self.tile_size.y))

        for i, row in enumerate(self._map):
            y = (i * self.tile_size.y) - self._result.height / 2 + self.tile_size.y / 2
            for j, tile in enumerate(row):
                x = (j * self.tile_size.x) - self._result.width / 2 + self.tile_size.x / 2
                self._result.blit(self._tiles[tile], dst=(int(x), int(y)))
                if tile in self._collision:
                    self.gameobj.add( # TODO: add to a child gameobject when that's a thing
                        Rectangle(
                            *(self.tile_size * self.scale).tuple_int(),
                            tag=self._collider_tag[tile] if tile < len(self._collider_tag) else "",
                            offset=(x, y) * self.scale,
                        )
                    )

    def update(self):
        if not self.uptodate:
            self._regen()
            self.uptodate = True

    def draw(self, camera):
        self._result.scale = self.scale
        self._result.rotation = self.true_rotation()
        Draw.queue_surface(self._result, self.true_pos(), self.true_z(), camera)

    def clone(self) -> SimpleTilemap:
        s = SimpleTilemap(
            self._map,
            self._tiles,
            self._tile_size.clone(),
            self._collision,
            self._collider_tag,
            self.scale.clone(),
            self.offset.clone(),
            self.rot_offset,
            self.z_index,
            self.hidden,
        )
        s._result = self._result.clone()
        return s
