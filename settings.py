from collections import defaultdict
from os.path import splitext
from os import listdir
from pygame.display import get_wm_info

class Settings:
    def __init__(self):
        with open("game_data/profile.txt", "r") as file:
            self.profile, self.window_loc, self.frame = eval(file.read())
            self.load_settings(self.profile)
            self.update_levels()
            self.update_profiles()

    def load_highscores(self, profile_name, update = False):
        if update:
            try:
                with open(f"game_data/profiles/{profile_name}/highscores/highscores.txt", "r") as file:
                    self.highscores = eval(file.read())
            except:
                self.highscores = {}
        else:
            try:
                with open(f"game_data/profiles/{profile_name}/highscores/highscores.txt", "r") as file:
                    return eval(file.read())
            except:
                return {}
        
    def load_settings(self, profile_name):
        with open(f"game_data/profiles/{profile_name}/settings.txt", "r") as file:
            self.background, self.textured_beams, self.pathclear, self.show_intro_text, self.darkness, self.dark_radius, self.dark_shape, self.show_info_mode, self.animations, self.replay_frame_rate = eval(file.read())
        self.load_highscores(profile_name, True)
    
    def update_profiles(self):
        self.profile_names = [splitext(filename)[0] for filename in listdir("game_data/profiles")]
        self.global_highscores = defaultdict(list)
        self.global_profile_scores = defaultdict(list)
        for profile_name in self.profile_names:
            profile_score = [0, 0]
            for level, score in self.load_highscores(profile_name).items():
                if level in self.level_names:
                    self.global_highscores[level].append((profile_name, score))
                    profile_score[0] += 1
                    profile_score[1] += score
                else:
                    print(f"{profile_name} contains highscore for non-existent level {level}")
            self.global_profile_scores[profile_name] = profile_score
        
        for score in self.global_highscores.values():
            score.sort(key = lambda x:x[1])
    
    def update_levels(self):
        self.level_names = [splitext(filename)[0] for filename in sorted(listdir("game_data/levels"), key = lambda x: (splitext(x)[1], splitext(x)[0]))]
        self.level_names[0] += "/template"

    def save_settings(self):
        def get_window():
            from ctypes import POINTER, WINFUNCTYPE, windll
            from ctypes.wintypes import BOOL, HWND, RECT
            rect = WINFUNCTYPE(BOOL, HWND, POINTER(RECT))(("GetWindowRect", windll.user32), ((1, "hwnd"), (2, "lprect")))(get_wm_info()["window"])
            return rect.left + 8 if self.frame else rect.left, rect.top + 31 if self.frame else rect.top

        with open(f"game_data/profile.txt", "w") as file:
            print("\"{0}\", '{1}, {2}', {3}".format(self.profile, *get_window(), self.frame), file = file)
        
        with open(f"game_data/profiles/{self.profile}/settings.txt", "w") as file:
            print(f"{self.background}, {self.textured_beams}, {self.pathclear}, {self.show_intro_text}, {self.darkness}, {self.dark_radius}, {self.dark_shape}, {self.show_info_mode}, {self.animations}, {self.replay_frame_rate}", file = file)