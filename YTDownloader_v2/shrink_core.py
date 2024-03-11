from moviepy.editor import AudioFileClip
from moviepy.editor import VideoFileClip


class Segment:
    def __init__(self, input_path, ext='mp3'):
        if ext == 'mp3':
            self.sound = AudioFileClip(input_path)
        elif ext == 'mp4':
            self.sound = VideoFileClip(input_path)

    def set_min_max(self, start, end):
        self.start = round(float(start[0])*60 + float(start[1]) + (1/60)*float(start[2]), 2)
        self.end = round(float(end[0])*60 + float(end[1]) + 1/60*float(end[2]), 2)

    def extract(self):
        extract = self.sound.subclip(self.start, self.end)
        return extract
