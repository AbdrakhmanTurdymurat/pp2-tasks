

import pygame
import os


class Player:
   

    def __init__(self, music_dir="music"):
        pygame.mixer.init()
        self.music_dir = music_dir
        self.tracks = []          
        self.track_names = []    
        self.current_index = 0
        self.is_playing = False
        self._load_tracks()

    

    def _load_tracks(self):
        
        supported = (".mp3", ".wav", ".ogg")
        if not os.path.isdir(self.music_dir):
            return
        for fname in sorted(os.listdir(self.music_dir)):
            if fname.lower().endswith(supported):
                self.tracks.append(os.path.join(self.music_dir, fname))
                self.track_names.append(os.path.splitext(fname)[0])

   

    def play(self):
        if not self.tracks:
            return
        if pygame.mixer.music.get_busy() and self.is_playing:
            return 
        if not self.is_playing:
            pygame.mixer.music.load(self.tracks[self.current_index])
            pygame.mixer.music.play()
        self.is_playing = True

    def stop(self):
       
        pygame.mixer.music.stop()
        self.is_playing = False

    def next_track(self):
       
        if not self.tracks:
            return
        self.current_index = (self.current_index + 1) % len(self.tracks)
        self._switch_track()

    def prev_track(self):
       
        if not self.tracks:
            return
        self.current_index = (self.current_index - 1) % len(self.tracks)
        self._switch_track()

    def _switch_track(self):
       
        pygame.mixer.music.stop()
        pygame.mixer.music.load(self.tracks[self.current_index])
        if self.is_playing:
            pygame.mixer.music.play()

   

    def get_current_name(self):
        
        if not self.track_names:
            return "No tracks found"
        return self.track_names[self.current_index]

    def get_track_count(self):
        return len(self.tracks)

    def get_position_str(self):
        
        if not self.is_playing or not self.tracks:
            return "00:00"
        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms < 0:
            return "00:00"
        secs = pos_ms // 1000
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def check_track_ended(self):
       
        if self.is_playing and not pygame.mixer.music.get_busy():
            self.next_track()
