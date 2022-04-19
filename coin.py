from pygame.math import Vector2

class Coin:
    def __init__(self, cx, cy, r):
        self.center = Vector2(cx, cy)
        self.center_x = cx
        self.center_y = cy
        self.radius = r
    
    def touch(self, other):
        return self.center.distance_squared_to(other) < self.radius * self.radius

    def attach(self, host):
        self.host = host