"""
player.py – Music Player logic
Manages playlist, playback state, and pygame.mixer integration.
"""

import pygame
import os


class MusicPlayer:
    """Handles loading tracks, playback controls, and state tracking."""

    SUPPORTED = (".mp3", ".wav", ".ogg")

    def __init__(self, music_dir: str):
        pygame.mixer.init()
        self.tracks: list[str] = []          # full file paths
        self.names:  list[str] = []          # display names
        self.index:  int       = 0           # current track index
        self.playing: bool     = False
        self.paused:  bool     = False
        self.volume:  float    = 0.8         # 0.0 – 1.0

        self._load_tracks(music_dir)
        pygame.mixer.music.set_volume(self.volume)

        # Fire an event when a track ends so we can auto-advance
        self.END_EVENT = pygame.USEREVENT + 2
        pygame.mixer.music.set_endevent(self.END_EVENT)

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _load_tracks(self, directory: str):
        """Scan directory for audio files."""
        if not os.path.isdir(directory):
            return
        for fname in sorted(os.listdir(directory)):
            if fname.lower().endswith(self.SUPPORTED):
                self.tracks.append(os.path.join(directory, fname))
                self.names.append(os.path.splitext(fname)[0])

    def _load_and_play(self):
        """Load current track and start playback."""
        if not self.tracks:
            return
        pygame.mixer.music.load(self.tracks[self.index])
        pygame.mixer.music.play()
        self.playing = True
        self.paused  = False

    # ── Public controls ──────────────────────────────────────────────────────

    def play(self):
        """Play or resume the current track."""
        if not self.tracks:
            return
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused  = False
            self.playing = True
        elif not self.playing:
            self._load_and_play()

    def stop(self):
        """Stop playback entirely."""
        pygame.mixer.music.stop()
        self.playing = False
        self.paused  = False

    def pause(self):
        """Pause if playing; resume if paused."""
        if self.playing and not self.paused:
            pygame.mixer.music.pause()
            self.paused  = True
            self.playing = False
        elif self.paused:
            self.play()

    def next_track(self):
        """Advance to the next track (wraps around)."""
        if not self.tracks:
            return
        self.index = (self.index + 1) % len(self.tracks)
        self._load_and_play()

    def prev_track(self):
        """Go back to the previous track (wraps around)."""
        if not self.tracks:
            return
        self.index = (self.index - 1) % len(self.tracks)
        self._load_and_play()

    def volume_up(self):
        self.volume = min(1.0, self.volume + 0.1)
        pygame.mixer.music.set_volume(self.volume)

    def volume_down(self):
        self.volume = max(0.0, self.volume - 0.1)
        pygame.mixer.music.set_volume(self.volume)

    def on_track_end(self):
        """Called when pygame fires the END_EVENT; auto-advance."""
        self.next_track()

    # ── State queries ────────────────────────────────────────────────────────

    @property
    def current_name(self) -> str:
        if not self.tracks:
            return "No tracks found"
        return self.names[self.index]

    @property
    def status(self) -> str:
        if not self.tracks:
            return "EMPTY"
        if self.paused:
            return "PAUSED"
        if self.playing:
            return "PLAYING"
        return "STOPPED"

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def position_label(self) -> str:
        if not self.tracks:
            return "0 / 0"
        return f"{self.index + 1} / {self.track_count}"