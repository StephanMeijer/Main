import numpy
import pickle

from base64 import b64encode, b64decode

class Body(): pass # Will make Type Hinting work.

class Body(object):
    def __init__(self, name: str, mass: float, radius: float, position: tuple, velocity: tuple):
        self.name, self.mass, self.radius = name, mass, radius

        # Vector
        self.position = numpy.array([[position[0]],
                                     [position[1]],
                                     [position[2]]]).astype('float64')

        # Vector
        self.velocity = numpy.array([[velocity[0]],
                                     [velocity[1]],
                                     [velocity[2]]]).astype('float64')

    def distance_to(self, other: Body) -> numpy.ndarray:
        """Takes two instances of a bodies and calculates the distance.

        Returns a Vector. Use numpy.linalg.norm(<Vector>) to get real distance in a float.

        >>> earth = Body("Earth", 5.972*(10**24), 100, (1.506*(10**11), 0, 100), (0, 29290, 0))
        >>> moon = Body("Moon", 0.0735*(10**24), 100, (1.496*(10**11), 384.4*(10**6), -500), (1050, 29290, 0))
        >>> moon.distance_to(earth)
        array([[  1.00000000e+09],
               [ -3.84400000e+08],
               [  6.00000000e+02]])
        """
        if self == other:
            return numpy.array([[0],
                                [0],
                                [0]])

        return other.position - self.position
        
    def absolute_distance_to_one(self, other: Body) -> numpy.ndarray:
        """Takes two instances of a bodies and calculates the absolute distance.

        >>> earth = Body("Earth", 5.972*(10**24), 100.0, (1.496*(10**11), 0, 0), (0, 29290, 0))
        >>> moon = Body("Moon", 0.0735*(10**24), 100.0, (1.496*(10**11), 384.4*(10**6), 0), (1050, 29290, 0))
        >>> moon.absolute_distance_to_one(earth)
        384400000.0
        """
        test = other.position - self.position
        return numpy.linalg.norm(test)
        
    def acceleration_to_one(self, other: Body) -> numpy.ndarray:
        """Return acceleration in x, y, z directions.
        >>> earth = Body("Earth", (5.972*(10**24)), 100.0, (0, 0, 0), (0, 0, 0))
        >>> kg = Body("kg", 1.0, 100.0, (0, 6371000, 0), (0, 0, 0))
        >>> kg.acceleration_to_one(earth)
        array([[ 0.        ],
               [-9.81964974],
               [ 0.        ]])
        """
        if self == other:
            return numpy.array([[0],
                                [0],
                                [0]])

        distance_vector = other.position - self.position
        distance = self.absolute_distance_to_one(other)
        
        force = (6.67408 * (10 ** -11)) * ((self.mass * other.mass) / (distance ** 2))
        forceratio = force / distance

        return ( distance_vector * forceratio ) / self.mass
        
    def acceleration_to_all(self, bodies: [Body]) -> numpy.ndarray:
        """ Return the acceleration in vectors to alll other bodies
        >>> kg = Body("kg", 1.0, 100.0, (0, 0, 0), (0, 0, 0))
        >>> earth1 = Body("Earth1", (5.972*(10**24)), 100.0, (0, 6371000, 6280), (0, 0, 0))
        >>> earth2 = Body("Earth4", (5.972*(10**24)), 100.0, (-6371000, 0, 0), (0, 0, 0))
        >>> moon = Body("Moon", 0.0735*(10**24), 100.0, (0, 384.4*(10**6), -1000), (0, 0, 0))
        >>> bodies = [kg, earth1, earth2, moon]
        >>> moon.acceleration_to_all(bodies)
        array([[ -4.46878801e-05],
               [ -5.48536334e-03],
               [  6.07257588e-08]])
        
        """
        total_acceleration = 0.0

        for body in bodies:
            total_acceleration += self.acceleration_to_one(body)

        return total_acceleration
        
    def calculate_position(self, delta_time: float) -> None:
        """ Calculates a new position for a new tick
        >>> test_body = Body("Test_body", 1.0, 1.0, (60, -20, 15), (4, 10.2, -6))
        >>> test_body.calculate_position(3.0)
        >>> test_body.position
        array([[ 72. ],
               [ 10.6],
               [ -3. ]])
        """
        self.position += delta_time * self.velocity
    
    def calculate_velocity(self, bodies, delta_time: float) -> None:
        """ Calculates new velocity for a new tick.
        >>> kg = Body("kg", 1.0, 100.0, (0, 0, 0), (0, 0, 0))
        >>> earth1 = Body("Earth1", (5.972*(10**24)), 100.0, (0, 6371000, 0), (0, 0, 0))
        >>> earth2 = Body("Earth2", (5.972*(10**24)), 100.0, (0, -6371000, 0), (0, 0, 0))
        >>> earth3 = Body("Earth3", (5.972*(10**24)), 100.0, (6371000, 0, 0), (0, 0, 0))
        >>> earth4 = Body("Earth4", (5.972*(10**24)), 100.0, (-6371000, 0, 0), (0, 0, 0))
        >>> earth5 = Body("Earth5", (5.972*(10**24)), 100.0, (6371000, 9000, -532), (0, 0, 0))
        >>> earth6 = Body("Earth6", (5.972*(10**24)), 100.0, (-6371000, -9000, 532), (0, 0, 0))
        >>> bodies = [kg, earth1, earth2, earth3, earth4, earth5, earth6]
        >>> kg.calculate_velocity(bodies, 314.0)
        >>> kg.velocity
        array([[ 0.],
               [ 0.],
               [ 0.]])
        
        >>> kg = Body("kg", 1.0, 100.0, (0, 0, 0), (0, 0, 0))
        >>> earth1 = Body("Earth1", (5.972*(10**24)), 100.0, (0, 6371000, 6280), (0, 0, 0))
        >>> moon = Body("Moon", 0.0735*(10**24), 100.0, (0, 384.4*(10**6), -1000), (0, 0, 0))
        >>> bodies = [kg, earth1, moon]
        >>> kg.calculate_velocity(bodies, 16.0)
        >>> kg.velocity
        array([[  0.00000000e+00],
               [  1.57114698e+02],
               [  1.54870030e-01]])
         
        >>> kg = Body("kg", 1.0, 100.0, (0, 0, 0), (0, 0, 0))
        >>> earth1 = Body("Earth1", (5.972*(10**24)), 100.0, (0, 6371000, 6280), (0, 0, 0))
        >>> moon = Body("Moon", 0.0735*(10**24), 100.0, (0, 384.4*(10**6), -1000), (0, 0, 0))
        >>> bodies = [kg, earth1, moon]
        >>> kg.calculate_velocity(bodies, 16.0)
        >>> kg.calculate_position(16.0) # This is basicly a test of a tick
        >>> kg.position
        array([[  0.00000000e+00],
               [  2.51383517e+03],
               [  2.47792047e+00]])
        """
        self.velocity += delta_time * self.acceleration_to_all(bodies)