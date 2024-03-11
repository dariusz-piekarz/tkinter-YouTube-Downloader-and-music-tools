from pytube import YouTube


def download_audio_from_youtube(url, ext="mp3"):
    yt = YouTube(url)
    if ext == "mp3":
        video = yt.streams.filter(only_audio=True).first()
    elif ext == "mp4":
        video = yt.streams.get_highest_resolution()
    return video
