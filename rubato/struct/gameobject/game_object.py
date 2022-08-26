"""
A game object is a basic element that holds components, postion, and z_index.
"""
from __future__ import annotations
from typing import Optional, Type, TypeVar

from . import Component
from .. import Surface
from ... import Game, Vector, DuplicateComponentError, Draw, ImplementationError, Camera, Color

T = TypeVar("T", bound=Component)


class GameObject:
    """
    The base game object class.

    Args:
        name: The name of the game object. Defaults to "".
        pos: The position of the game object. Defaults to (0, 0).
        rotation: The rotation of the game object. Defaults to 0.
        z_index: The z-index of the game object. Defaults to 0.
        debug: Whether to draw the center of the game object. Defaults to False.
        active: Whether the group is active or not. Defaults to True.
    """

    def __init__(
        self,
        name: str = "",
        pos: Vector | tuple[float, float] = (0, 0),
        rotation: float = 0,
        z_index: int = 0,
        debug: bool = False,
        active: bool = True,
    ):
        self.name: str = name
        """
        The name of the game object. Will default to: "Game Object {number in group}"
        """
        self.pos: Vector = Vector.create(pos)
        """The current position of the game object."""
        self.debug: bool = debug
        """Whether to draw a debug crosshair for the game object."""
        self.z_index: int = z_index
        """The z_index of the game object."""
        self._components: dict[type, list[Component]] = {}
        self.rotation: float = rotation
        """The rotation of the game object in degrees."""
        self.hidden: bool = False
        """Whether the game object (its components) will be drawn that frame. Keeps debug outline."""
        self.active: bool = active
        """Whether the group is active or not. Note: gets rid of debug outline as well as removing draw and update."""
        self._debug_cross: Surface = Surface(10, 10)
        self._debug_cross.draw_line(Vector(4, 0), Vector(4, 9), Color.debug)
        self._debug_cross.draw_line(Vector(5, 0), Vector(5, 9), Color.debug)
        self._debug_cross.draw_line(Vector(0, 4), Vector(9, 4), Color.debug)
        self._debug_cross.draw_line(Vector(0, 5), Vector(9, 5), Color.debug)

    def add(self, *components: Component) -> GameObject:
        """
        Add a component to the game object.

        Args:
            components (Component): The component(s) to add.

        Raises:
            DuplicateComponentError: Raised when there is already a component of the same type in the game object.
                Note that this error is only raised if the component type's 'singular' attribute is True.

        Returns:
            GameObject: This GameObject.
        """
        for component in components:
            comp_type = type(component)

            try:
                if component.singular and comp_type in self._components:
                    raise DuplicateComponentError(
                        f"There is already a component of type '{comp_type}' in the game object '{self.name}'"
                    )
            except AttributeError as err:
                raise ImplementationError(
                    "The component does not have the attribute 'singular'. You most likely overrode the"
                    "__init__ method of the component without calling super().__init__()."
                ) from err

            if comp_type not in self._components:
                self._components[comp_type] = []
            self._components[comp_type].append(component)
            component.gameobj = self

        return self

    def remove(self, comp_type: Type[T]):
        """
        Removes the first instance of a component from the game object.

        Args:
            comp_type: The type of the component to remove.

        Raises:
            IndexError: The component was not in the game object and nothing was removed.
        """
        self.remove_ind(comp_type, 0)

    def remove_ind(self, comp_type: Type[T], ind: int):
        """
        Removes a component from the game object.

        Args:
            comp_type: The Type of component to remove
            ind: The index of the component to remove.

        Raises:
            IndexError: The component was not in the game object and nothing was removed or the index was out of bounds.
        """
        for key, val in self._components.items():
            if issubclass(key, comp_type):
                if ind < len(val):
                    del val[ind]
                    return
                else:
                    ind -= len(val)
        raise IndexError(
            f"There are no components of type '{comp_type}' in game object '{self.name}' or the index is out of bounds."
        )

    def remove_all(self, comp_type: Type[T]):
        """
        Removes all components of a type from the game object.

        Args:
            comp_type: The type of the component to remove.

        Raises:
            IndexError: The components were not in the game object and nothing was removed.
        """
        deleted = False
        for key, val in self._components.items():
            if issubclass(key, comp_type):
                del val
                deleted = True
        if not deleted:
            raise IndexError(f"There are no components of type '{comp_type}' in game object '{self.name}'.")

    def get(self, comp_type: Type[T]) -> Optional[T]:
        """
        Gets a component from the game object.

        Args:
            comp_type: The type of the component to search for.

        Returns:
            The component if it was found or None if it wasn't.
        """
        for key, val in self._components.items():
            if issubclass(key, comp_type):
                return val[0]
        return None

    def get_all(self, comp_type: Type[T]) -> list[T]:
        """
        Gets all the components of a type from the game object.

        Args:
            comp_type: The type of component to search for.

        Returns:
            A list containing all the components of that type. If no components were found, the
                list is empty.
        """
        fin = []
        for key, val in self._components.items():
            if issubclass(key, comp_type):
                fin.extend(val)
        return fin

    def delete(self):
        """
        Deletes and frees everything from the game object. This is called when you remove it from a group or scene.

        Warning:
            Calling this will render the gameobject useless in the future.
        """
        for comps in self._components.values():
            for comp in comps:
                comp.delete()

    def draw(self, camera: Camera):
        if self.active:
            if not self.hidden:
                for comps in self._components.values():
                    for comp in comps:
                        if comp.hidden:
                            continue
                        comp.draw(camera)

            if self.debug or Game.debug:
                self._debug_cross.rotation = self.rotation

                Draw.queue_surf(self._debug_cross, self.pos, camera=camera)

    def update(self):
        if self.active:
            all_comps = list(self._components.values())
            for comps in all_comps:
                for comp in comps:
                    comp.private_update()

    def fixed_update(self):
        if self.active:
            for comps in self._components.values():
                for comp in comps:
                    comp.fixed_update()

    def clone(self) -> GameObject:
        """
        Clones the game object.
        """
        new_obj = GameObject(
            name=f"{self.name} (clone)",
            pos=self.pos.clone(),
            rotation=self.rotation,
            z_index=self.z_index,
            debug=self.debug
        )
        for component in self._components.values():
            for comp in component:
                new_obj.add(comp.clone())

        return new_obj

    def __repr__(self):
        return f"{self.name} rubato.GameObject with {len(self.get_all(Component))} components at {hex(id(self))}"