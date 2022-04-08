"""
The Rigidbody component contains an implementation of rigidbody physics. They
have hitboxes and can collide and interact with other rigidbodies.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from . import Component
from ... import Vector, Defaults, Time

if TYPE_CHECKING:
    from . import Manifold


class RigidBody(Component):
    """
    A RigidBody implementation with built in physics and collisions.
    Rigidbodies require hitboxes.

    Attributes:
        static (bool): Whether or not the rigidbody is static (as in, it does
            not move).
        gravity (Vector): The acceleration of the gravity that should be
            applied.
        friction (float): The friction coefficient of the Rigidbody (usually a
            a value between 0 and 1).
        max_speed (Vector): The maximum speed of the Rigidbody.
        min_speed (Vector): The minimum speed of the Rigidbody.
        velocity (Vector): The current velocity of the Rigidbody.
        inv_mass (float): The inverse of the mass of the Rigidbody (0 if the
            mass is infinite).
        bounciness (float): How bouncy the rigidbody is (usually a value
            between 0 and 1).
    """

    def __init__(self, options: dict = {}):
        """
        Initializes a Rigidbody.

        Args:
            options: A rigidbody config. Defaults to the :ref:`Rigidbody defaults <rigidbodydef>`.
        """
        params = Defaults.rigidbody_defaults | options

        super().__init__()

        self.static: bool = params["static"]

        self.gravity: Vector = params["gravity"]
        self.friction: float = params["friction"]
        self.max_speed: Vector = params["max_speed"]

        self.pos_correction: float = params["pos_correction"]

        self.velocity: Vector = params["velocity"]
        self.ang_vel: float = params["ang_vel"]

        self.singular = True

        if params["mass"] == 0 or self.static:
            self.inv_mass = 0
        else:
            self.inv_mass: float = 1 / params["mass"]

        if params["moment"] == 0 or self.static:
            self.inv_moment = 0
        else:
            self.inv_moment: float = 1 / params["moment"]

        self.bounciness: float = params["bounciness"]

    @property
    def mass(self) -> float:
        """The mass of the Rigidbody."""
        if self.inv_mass == 0:
            return 0
        else:
            return 1 / self.inv_mass

    @mass.setter
    def mass(self, new: float):
        if new == 0:
            self.inv_mass = 0
        else:
            self.inv_mass: float = 1 / new

    @property
    def moment(self) -> float:
        """The moment of inertia of the Rigidbody."""
        if self.inv_moment == 0:
            return 0
        else:
            return 1 / self.inv_moment

    @moment.setter
    def moment(self, new: float):
        if new == 0:
            self.inv_moment = 0
        else:
            self.inv_moment: float = 1 / new

    def physics(self):
        """Applies general kinematic laws to the rigidbody."""
        self.add_force(self.gravity * self.mass)

        self.velocity.clamp(-self.max_speed, self.max_speed)

        self.gameobj.pos += self.velocity * Time.milli_to_sec(Time.fixed_delta)
        self.gameobj.rotation += self.ang_vel * Time.milli_to_sec(Time.fixed_delta)

    def add_force(self, force: Vector):
        """
        Add a force to the Rigidbody.

        Args:
            force (Vector): The force to add.
        """
        accel = force * self.inv_mass

        self.velocity += accel * Time.milli_to_sec(Time.fixed_delta)

    def add_cont_force(self, impulse: Vector, time: int):
        """
        Add a continuous force to the Rigidbody.
        A continuous force is a force that is continuously applied over a time period.
        (the force is added every frame for a specific duration).

        Args:
            impulse (Vector): The force to add.
            time (int): The time in seconds that the force should be added.
        """
        if time <= 0:
            return
        else:
            self.add_force(impulse)
            Time.delayed_frames(1, lambda: self.add_impulse(impulse, time - Time.delta_time))

    def fixed_update(self):
        """The physics loop for the rigidbody component."""
        if not self.static:
            self.physics()

    def clone(self) -> RigidBody:
        return RigidBody(
            {
                "static": self.static,
                "gravity": self.gravity,
                "friction": self.friction,
                "max_speed": self.max_speed,
                "pos_correction": self.pos_correction,
                "velocity": self.velocity,
                "mass": self.mass,
                "bounciness": self.bounciness,
            }
        )

    @staticmethod
    def handle_collision(col: Manifold):
        """
        Resolve the collision between two rigidbodies.
        Utilizes a simplistic impulse resolution method.

        Args:
            col: The collision information.
        """
        # Get the rigidbody components
        rb_a: RigidBody = col.shape_b.gameobj.get(RigidBody)
        rb_b: RigidBody = col.shape_a.gameobj.get(RigidBody)

        a_none = rb_a is None
        b_none = rb_b is None

        if a_none and b_none:
            return

        # Find inverse masses
        inv_mass_a: float = 0 if a_none else rb_a.inv_mass
        inv_mass_b: float = 0 if b_none else rb_b.inv_mass

        # Handle infinite mass cases
        if inv_mass_a == inv_mass_b == 0:
            if a_none:
                inv_mass_b = 1
            elif b_none:
                inv_mass_a = 1
            else:
                inv_mass_a, inv_mass_b = 1, 1

        inv_sys_mass = 1 / (inv_mass_a + inv_mass_b)

        # Position correction
        correction = max(col.penetration - 0.01, 0) * inv_sys_mass * col.normal

        # Impulse Resolution

        # Relative velocity
        rv = (0 if b_none else rb_b.velocity - col.contact_b.perpendicular(rb_b.ang_vel)
             ) - (0 if a_none else rb_a.velocity - col.contact_a.perpendicular(rb_a.ang_vel))

        if (vel_along_norm := rv.dot(col.normal)) > 0:
            return

        # Calculate restitution
        e = max(0 if a_none else rb_a.bounciness, 0 if b_none else rb_b.bounciness)

        # Calculate inverse angular components
        i_a = 0 if a_none else col.contact_a.cross(col.normal)**2 * rb_a.inv_moment
        i_b = 0 if a_none else col.contact_b.cross(col.normal)**2 * rb_b.inv_moment

        # Calculate impulse scalar
        j = -(1 + e) * vel_along_norm / (inv_mass_a + inv_mass_b + i_a + i_b)

        # Apply the impulse
        impulse = j * col.normal

        if not (a_none or rb_a.static):
            rb_a.gameobj.pos -= inv_mass_a * correction * rb_a.pos_correction
            rb_a.velocity -= inv_mass_a * impulse
            rb_a.ang_vel -= col.contact_a.cross(impulse) * rb_a.inv_moment

        if not (b_none or rb_b.static):
            rb_b.gameobj.pos += inv_mass_b * correction * rb_b.pos_correction
            rb_b.velocity += inv_mass_b * impulse
            rb_b.ang_vel += col.contact_b.cross(impulse) * rb_b.inv_moment

        # Friction

        # Calculate friction coefficient
        if a_none:
            mu = rb_b.friction * rb_b.friction
        elif b_none:
            mu = rb_a.friction * rb_a.friction
        else:
            mu = min(rb_a.friction * rb_a.friction, rb_b.friction * rb_b.friction)

        # Stop redundant friction calculations
        if mu == 0:
            return

        # Tangent vector
        tangent = rv - rv.dot(col.normal) * col.normal
        tangent.magnitude = 1

        # Solve for magnitude to apply along the friction vector
        jt = -rv.dot(tangent) * inv_sys_mass

        # Calculate friction impulse
        if abs(jt) < j * mu:
            friction_impulse = jt * tangent  # "Static friction"
        else:
            friction_impulse = -j * tangent * mu  # "Dynamic friction"

        if not (a_none or rb_a.static):
            rb_a.velocity -= inv_mass_a * friction_impulse
            rb_a.ang_vel -= col.contact_a.cross(friction_impulse) * rb_a.inv_moment

        if not (b_none or rb_b.static):
            rb_b.velocity += inv_mass_b * friction_impulse
            rb_b.ang_vel += col.contact_b.cross(friction_impulse) * rb_b.inv_moment
