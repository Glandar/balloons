from math import sqrt
from pygame.draw import rect
from constants import PRECISION, GRAVITY #@UnresolvedImport
from colors import BLACK, BLUE, RED #@UnresolvedImport
from fonts import num_font20 #@UnresolvedImport

class Beam:
    def __init__(self, l, r, u, d, remover):
        self.left = l
        self.right = r
        self.up = u
        self.down = d
        self.remover = remover
                
    def proximity_edge(self, x_rate, y_rate, ball):
        # x - direction collision
        if (self.left - ball.size < ball.position.x + x_rate < self.right + ball.size and self.up <= ball.position.y <= self.down):
            if ball.position.x < (self.left + self.right)/2:
                x_rate = self.left - ball.position.x - ball.size
            else:
                x_rate = self.right - ball.position.x + ball.size
        # y - direction collision
        elif (self.left <= ball.position.x <= self.right and self.up - ball.size < ball.position.y + y_rate < self.down + ball.size):
            if ball.position.y < (self.up + self.down)/2:
                y_rate = self.up - ball.position.y - ball.size
            else:
                y_rate = self.down - ball.position.y + ball.size
            if (ball.position.y < self.up):
                ball.on_top = True
                ball.doublejump = True
        return x_rate if abs(x_rate) > PRECISION else 0, y_rate if abs(y_rate) > PRECISION else 0

    def proximity_vertex(self, x_rate, y_rate, ball):
        # speed changes if approaching a corner of an object (upper right, lower right, upper left, lower left)
        if (self.right < ball.position.x + x_rate < self.right + ball.size and self.up - ball.size < ball.position.y + y_rate < self.up):
            if (self.up - sqrt(ball.size * ball.size - (ball.position.x + x_rate - self.right) * (ball.position.x + x_rate - self.right)) < ball.position.y + y_rate < self.up):
                if x_rate < 0:
                    direction = [ball.position.x - self.right, self.up - ball.position.y]
                    direction = [direction[1] / (abs(direction[0]) + abs(direction[1])), direction[0] / (abs(direction[0]) + abs(direction[1]))]
                    y_rate = x_rate * direction[1]
                    x_rate *= direction[0]
                else:
                    y_rate = self.up - ball.position.y - sqrt(ball.size * ball.size - (ball.position.x - self.right) * (ball.position.x - self.right))
                ball.on_top = True
                ball.doublejump = True
        elif (self.right < ball.position.x + x_rate < self.right + ball.size and self.down < ball.position.y + y_rate < self.down + ball.size):
            if (self.down < ball.position.y + y_rate < self.down + sqrt(ball.size * ball.size - (ball.position.x + x_rate - self.right) * (ball.position.x + x_rate - self.right))):
                if x_rate < 0:
                    direction = [ball.position.x - self.right, self.down - ball.position.y]
                    direction = [direction[1] / (abs(direction[0]) + abs(direction[1])), direction[0] / (abs(direction[0]) + abs(direction[1]))]             
                    y_rate = max(GRAVITY, y_rate)
                    x_rate *= -direction[0] * (y_rate * direction[1] < -x_rate * direction[0])
                else:
                    y_rate = self.down - ball.position.y + sqrt(ball.size * ball.size - (ball.position.x - self.right) * (ball.position.x - self.right))
        elif (self.left - ball.size < ball.position.x + x_rate < self.left and self.up - ball.size < ball.position.y + y_rate < self.up):
            if (self.up - sqrt(ball.size * ball.size - (ball.position.x + x_rate - self.left) * (ball.position.x + x_rate - self.left)) < ball.position.y + y_rate < self.up):
                if x_rate > 0:
                    direction = [ball.position.x - self.left, self.up - ball.position.y]
                    direction = [direction[1] / (abs(direction[0]) + abs(direction[1])), direction[0] / (abs(direction[0]) + abs(direction[1]))]
                    y_rate = x_rate * direction[1]
                    x_rate *= direction[0]
                else:
                    y_rate = self.up - ball.position.y - sqrt(ball.size * ball.size - (ball.position.x - self.left) * (ball.position.x - self.left))
                ball.on_top = True
                ball.doublejump = True
        elif (self.left - ball.size < ball.position.x + x_rate < self.left and self.down < ball.position.y + y_rate < self.down + ball.size):
            if (self.down < ball.position.y + y_rate < self.down + sqrt(ball.size * ball.size - (ball.position.x + x_rate - self.left) * (ball.position.x + x_rate - self.left))):
                if x_rate > 0:
                    direction = [ball.position.x - self.left, self.down - ball.position.y]
                    direction = [direction[1] / (abs(direction[0]) + abs(direction[1])), direction[0] / (abs(direction[0]) + abs(direction[1]))]
                    y_rate = max(GRAVITY, y_rate)
                    x_rate *= -direction[0] * (y_rate * direction[1] < x_rate * direction[0])
                else:
                    y_rate = self.down - ball.position.y + sqrt(ball.size * ball.size - (ball.position.x - self.left) * (ball.position.x - self.left))
        elif (self.up - ball.size < ball.position.y + y_rate < self.up and (self.left - x_rate < ball.position.x < self.left or self.right < ball.position.x < self.right - x_rate)):
            y_rate = self.up - ball.position.y - ball.size
        elif (self.up - ball.size < ball.position.y < self.up and (self.left - x_rate < ball.position.x + ball.size <= self.left or self.right <= ball.position.x - ball.size < self.right - x_rate)):
            x_rate = 0
        return x_rate if abs(x_rate) > PRECISION else 0, y_rate if abs(y_rate) > PRECISION else 0
 
    def draw(self, surface, mode, creator = False, color = BLUE):
        if mode == "full":
            surface.fill(color, [self.left, self.up, self.right - self.left, self.down - self.up])
            if creator:
                id_number = num_font20.render(str(self.remover), True, BLACK)
                surface.blit(id_number, [(self.left + self.right)/2 - id_number.get_rect().width/2, (self.up + self.down)/2 - id_number.get_rect().height/2])
        elif mode == "outline":
                rect(surface, RED, [self.left, self.up, self.right - self.left, self.down - self.up], 4)

    def restrict(self, pos, size):
    # Returns False if the new situation is allowed
        if (self.left  - size < pos.x < self.right + size and self.up < pos.y < self.down):
            return True
        elif (self.left < pos.x < self.right and self.up - size < pos.y < self.down + size):
            return True
        elif (self.right < pos.x < self.right + size and self.up - size < pos.y < self.up):
            if (self.up - sqrt(size * size - (pos.x - self.right) * (pos.x - self.right)) < pos.y < self.up):
                return True
        elif (self.right < pos.x < self.right + size and self.down < pos.y < self.down + size):
            if (self.down < pos.y < self.down + sqrt(size * size - (pos.x - self.right) * (pos.x - self.right))):
                return True
        elif (self.left - size < pos.x < self.left and self.up - size < pos.y < self.up):
            if (self.up - sqrt(size * size - (pos.x - self.left) * (pos.x - self.left)) < pos.y < self.up):
                return True
        elif (self.left - size < pos.x < self.left and self.down < pos.y < self.down + size):
            if (self.down < pos.y < self.down + sqrt(size * size - (pos.x - self.left) * (pos.x - self.left))):
                return True
        return False
    
    def mouse(self, mouse_pos):
        return self.left < mouse_pos[0] < self.right and self.up < mouse_pos[1] < self.down
