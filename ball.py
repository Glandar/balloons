from pygame.math import Vector2
from constants import FIRST_JUMP, SECOND_JUMP #@UnresolvedImport

class Ball:
    def __init__(self, x, y, s):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.size = s
        self.doublejump = True
        self.on_top = False
        self.on_ball = False
        
    def weight(self):
        return self.size * self.size
    
    def weighted_speed(self):
        return self.velocity * self.weight()
    
    def next_pos(self):
        return self.position + self.velocity
    
    def distance(self, other, fstep = False):
        return self.next_pos().distance_squared_to(other) if fstep else self.position.distance_squared_to(other)
    
    def touch(self, other, radius, fstep = False):
        return self.distance(other, fstep) < radius * radius
    
    def jump(self):
        if self.on_top or self.on_ball:
            self.velocity.y = min(self.velocity.y, -FIRST_JUMP)
        elif self.doublejump:
            if self.velocity.y > -SECOND_JUMP:
                self.velocity.y = -SECOND_JUMP
                self.doublejump = False