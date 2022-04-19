from constants import PRECISION #@UnresolvedImport

class Border:
    def __init__(self, w, h):
        self.left = 0
        self.right = w
        self.up = 0
        self.down = h
    
    def proximity(self, x_rate, y_rate, ball):
        if ball.position.x + x_rate > self.right - ball.size:
            x_rate = self.right - ball.position.x - ball.size
        elif ball.position.x + x_rate < self.left + ball.size:
            x_rate = self.left - ball.position.x + ball.size
        if ball.position.y + y_rate > self.down - ball.size:
            y_rate = self.down - ball.position.y - ball.size
            ball.on_top = True
        elif ball.position.y + y_rate < self.up + ball.size:
            y_rate = self.up - ball.position.y + ball.size
        return x_rate if abs(x_rate) > PRECISION else 0, y_rate if abs(y_rate) > PRECISION else 0

    def restrict(self, pos, size):
    # Returns False if the new situation is allowed
        return not (self.left + size <= pos.x <= self.right - size and self.up + size <= pos.y <= self.down - size)