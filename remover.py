import random
from pygame import Surface, gfxdraw, BLEND_RGB_ADD
from pygame.draw import line, polygon, circle
from math import pi, sin, cos
from colors import BLUE, CYAN, RED, WHITE, BLACK #@UnresolvedImport
from coin import Coin #@UnresolvedImport
from fonts import num_font20 #@UnresolvedImport

class Remover(Coin):
    def __init__(self, cx, cy, r, n):
        super().__init__(cx, cy, r)
        self.id = n
        self.sparks = None

    def proximity(self, ball):
        if self.touch(ball.position):
            self.host.update_beam_surface(self.id)
    
    def draw(self, surface, mode, creator = False, frame = 0):
        if mode == "back":
            gfxdraw.aacircle(surface, self.center_x, self.center_y, self.radius, CYAN)
            gfxdraw.filled_circle(surface, self.center_x, self.center_y, self.radius, CYAN)
        elif mode == "front":
            for dt in [0, pi/3, 2*pi/3, pi, 4*pi/3, 5*pi/3]:                
                gfxdraw.filled_polygon(surface, [self.center + ((self.radius + 0.5) * sin(dt + frame/50) * 0.8 + 0.5, (self.radius + 0.5) * cos(dt + frame/50) * 0.8 + 0.5),
                                                 self.center + ((self.radius + 0.5) * sin(dt + frame/50 + 0.2) + 0.5, (self.radius + 0.5) * cos(dt + frame/50 + 0.2) + 0.5),
                                                 self.center + ((self.radius + 0.5) * sin(dt + frame/50)       + 0.5, (self.radius + 0.5) * cos(dt + frame/50)       + 0.5),
                                                 self.center + ((self.radius + 0.5) * sin(dt + frame/50 - 0.2) + 0.5, (self.radius + 0.5) * cos(dt + frame/50 - 0.2) + 0.5)], BLUE)
                gfxdraw.aapolygon(surface,      [self.center + ((self.radius + 0.5) * sin(dt + frame/50) * 0.8 + 0.5, (self.radius + 0.5) * cos(dt + frame/50) * 0.8 + 0.5),
                                                 self.center + ((self.radius + 0.5) * sin(dt + frame/50 + 0.2) + 0.5, (self.radius + 0.5) * cos(dt + frame/50 + 0.2) + 0.5),
                                                 self.center + ((self.radius + 0.5) * sin(dt + frame/50)       + 0.5, (self.radius + 0.5) * cos(dt + frame/50)       + 0.5),
                                                 self.center + ((self.radius + 0.5) * sin(dt + frame/50 - 0.2) + 0.5, (self.radius + 0.5) * cos(dt + frame/50 - 0.2) + 0.5)], BLUE)
            if self.sparks:
                for beam in self.host.Beams:
                    if self.id in beam.remover:
                        beam.draw(surface, "full", color = CYAN)
                if self.sparks.progress < 38:
                    self.sparks.shock(surface)
            if creator:
                id_number = num_font20.render("{0:0g}".format(self.id), True, BLACK)
                surface.blit(id_number, self.center - (id_number.get_rect().width/2, id_number.get_rect().height/2))
        elif mode == "outline":
            circle(surface, RED, self.center + (1, 1), self.radius + 1, 4)

    def animate(self, surface, animate):
        if animate:
            if not self.sparks:
                self.sparks = self.Spark(self, self.host.Beams)
        else:
            for beam in self.host.Beams:
                if self.id in beam.remover:
                    beam.draw(surface, "full", color = CYAN)
    
    class Spark:
        def __init__(self, parent, Beams):
            self.parent = parent
            self.progress = 0
            self.beams = [beam for beam in Beams if self.parent.id in beam.remover]
            self.beam_hits = [(round((beam.right - beam.left) / 30), round((beam.down - beam.up) / 30)) for beam in self.beams]
            self.beam_slices = [(round((beam.right - beam.left) / hit[0]), round((beam.down - beam.up) / hit[1])) for beam, hit in zip(self.beams, self.beam_hits)]
            self.beam_areas = [[(beam.left + i * beam_slice[0], beam.left + (i + 1) * beam_slice[0], beam.up + j * beam_slice[1], beam.up + (j + 1) * beam_slice[1]) for i in range(hits[0]) for j in range(hits[1])] for beam, hits, beam_slice in zip(self.beams, self.beam_hits, self.beam_slices)]
            self.beam_centers = [(random.choice([hit[0] // 2, (hit[0] - 1) // 2]), random.choice([hit[1] // 2, (hit[1] - 1) // 2])) for hit in self.beam_hits]
            self.points = [[(random.randint(area[0] + 4, area[1] - 4), random.randint(area[2] + 4, area[3] - 4)) for area in beam] for beam in self.beam_areas]
            self.break_points = [[0.2 + 0.6 * random.random() for _ in range(len(point_set) - 1)] for point_set in self.points]
            self.break_points = [sorted(break_point, reverse = True) for break_point in self.break_points]
            self.break_points = [[break_point[2 * abs(i - len(break_point)//2) - (i < len(break_point)//2)] for i in range(len(break_point))] for break_point in self.break_points]
            self.break_points_2 = [[(point[max(center)][0] * b + self.parent.center_x * (1 - b), point[max(center)][1] * b + self.parent.center_y * (1 - b)) for b in break_point] for point, center, break_point in zip(self.points, self.beam_centers, self.break_points)]
            self.break_points_3 = [[(point[0] * b + self.parent.center_x * (1 - b), point[1] * b + self.parent.center_y * (1 - b)) for point, b in zip(point_set[:max(center)] + point_set[max(center) + 1:], break_point)] for point_set, center, break_point in zip(self.points, self.beam_centers, self.break_points)]
            self.light_edges = [(min([self.parent.center_x] + [p[0] for p in beam]), min([self.parent.center_y] + [p[1] for p in beam])) for beam in self.points]
            self.light_surfaces = [Surface((max([self.parent.center_x] + [p[0] for p in beam]) - edge[0], max([self.parent.center_y] + [p[1] for p in beam]) - edge[1])) for beam, edge in zip(self.points, self.light_edges)]
            for light_surface, point_set, edge in zip(self.light_surfaces, self.points, self.light_edges):
                if len(point_set) > 1:
                    polygon(light_surface, (60, 60, 60), [(p[0] - edge[0], p[1] - edge[1]) for p in ([self.parent.center] + point_set)])
            
        def shock(self, surface):
            width = [round(10 - self.progress/2), round(10 - self.progress/3), round(10 - self.progress/4)]
            for center, point, break_point2, break_point3 in zip(self.beam_centers, self.points, self.break_points_2, self.break_points_3):
                for bp3, p in zip(break_point3, point[:max(center)] + point[max(center) + 1:]):
                    line(surface, BLUE, bp3, p, width[2])
                for bp2, bp3 in zip(break_point2, break_point3):
                    line(surface, BLUE, bp2, bp3, width[2])
                line(surface, BLUE, self.parent.center, point[max(center)], width[2])
                for bp3, p in zip(break_point3, point[:max(center)] + point[max(center) + 1:]):
                    line(surface, CYAN, bp3, p, width[1])
                for bp2, bp3 in zip(break_point2, break_point3):
                    line(surface, CYAN, bp2, bp3, width[1])
                line(surface, CYAN, self.parent.center, point[max(center)], width[1])
                for bp3, p in zip(break_point3, point[:max(center)] + point[max(center) + 1:]):
                    line(surface, WHITE, bp3, p, width[0])
                for bp2, bp3 in zip(break_point2, break_point3):
                    line(surface, WHITE, bp2, bp3, width[0])
                line(surface, WHITE, self.parent.center, point[max(center)], width[0])
            if self.progress < 20:
                for light_surface, point_set in zip(self.light_surfaces, self.points):
                    surface.blit(light_surface, (min([self.parent.center_x] + [p[0] for p in point_set]), min([self.parent.center_y] + [p[1] for p in point_set])), special_flags = BLEND_RGB_ADD)
            self.progress += 1