from random import uniform, randint
from math import sqrt
from pygame import gfxdraw
from pygame.draw import circle
from pygame.math import Vector2
from colors import RED, PURPLE #@UnresolvedImport
from coin import Coin #@UnresolvedImport

class Teleporter(Coin):
    def __init__(self, cx, cy, r, dx, dy):
        super().__init__(cx, cy, r)
        self.destination = Vector2(dx, dy)
        self.difference_x = dx - cx
        self.difference_y = dy - cy
        self.distance = sqrt(self.difference_x * self.difference_x + self.difference_y * self.difference_y)
        self.pulses = []
    
    def proximity(self, ball, other):
        if self.touch(ball.position) and not other.touch(self.destination, ball.size + other.size) and not self.host.beam_border_restrict([(self.destination, ball.size)]):
            ball.position.update(self.destination)
    
    def update_colors(self, frame):
        phase = [(96 - frame) % 128, (64 - frame) % 128, (32 - frame) % 128, -frame % 128]
        self.colors = [(127 + i % 2 * 64 + min(p, 128 - p), 0, 127 + i % 2 * 64 + min(p, 128 - p)) for i, p in enumerate(phase)]
    
    def draw(self, surface, mode, frame = 0):
        if mode == "back":
            gfxdraw.filled_circle(surface, self.center_x, self.center_y,       self.radius,                             self.colors[(frame // 32    ) % 4])
            gfxdraw.filled_circle(surface, self.center_x, self.center_y, round(self.radius * (128 - frame % 32) / 128), self.colors[(frame // 32 + 3) % 4])
            gfxdraw.filled_circle(surface, self.center_x, self.center_y, round(self.radius * (96  - frame % 32) / 128), self.colors[(frame // 32 + 2) % 4])
            gfxdraw.filled_circle(surface, self.center_x, self.center_y, round(self.radius * (64  - frame % 32) / 128), self.colors[(frame // 32 + 1) % 4])
            gfxdraw.filled_circle(surface, self.center_x, self.center_y, round(self.radius * (32  - frame % 32) / 128), self.colors[(frame // 32    ) % 4])
        elif mode == "front":
            gfxdraw.aacircle(surface, self.center_x, self.center_y,       self.radius,                             self.colors[(frame // 32    ) % 4])
            gfxdraw.aacircle(surface, self.center_x, self.center_y, round(self.radius * (128 - frame % 32) / 128), self.colors[(frame // 32 + 3) % 4])
            gfxdraw.aacircle(surface, self.center_x, self.center_y, round(self.radius * (96  - frame % 32) / 128), self.colors[(frame // 32 + 2) % 4])
            gfxdraw.aacircle(surface, self.center_x, self.center_y, round(self.radius * (64  - frame % 32) / 128), self.colors[(frame // 32 + 1) % 4])
            gfxdraw.aacircle(surface, self.center_x, self.center_y, round(self.radius * (32  - frame % 32) / 128), self.colors[(frame // 32    ) % 4])
            if self.pulses:
                circle(surface, PURPLE, self.destination, 15, 0)
                self.pulses = [pulse for pulse in self.pulses if pulse.shine(surface)]
        elif mode == "outline":
            circle(surface, RED, self.center + (1, 1), self.radius + 1, 4)

    def animate(self, surface, animate):
        if animate:
            self.pulses.append(self.Pulse(self))
        else:
            circle(surface, PURPLE, self.destination, 15, 0)
    
    class Pulse:
        def __init__(self, parent):
            self.parent = parent
            self.progress = 0
            self.duration = randint(round(parent.distance / 6), round(parent.distance / 4))
            self.deviation_x = uniform(-2, 2)
            self.deviation_y = uniform(-2, 2)
            self.color = (randint(127, 255), 0 , randint(127, 255))
            self.radius = randint(3, 8)
            
        def shine(self, surface):
            circle(surface, self.color, self.parent.center + ((self.progress / self.duration) * (self.parent.difference_x + self.deviation_x * (self.duration - self.progress) * self.parent.difference_y / self.parent.distance),
                                                              (self.progress / self.duration) * (self.parent.difference_y + self.deviation_y * (self.duration - self.progress) * self.parent.difference_x / self.parent.distance)), self.radius, 0)
            self.progress += 1
            return self.progress < self.duration