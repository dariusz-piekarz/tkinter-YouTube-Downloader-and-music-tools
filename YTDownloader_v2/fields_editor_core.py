from mutagen.id3 import ID3, APIC, TIT2, TALB, TPE1, TRCK, TCON
from PIL import Image
from io import BytesIO


def edit_fields(**kwargs) -> None:
    if 'mp3_path' in kwargs.keys():
        audiofile = ID3(kwargs['mp3_path'])
    if 'cover_path' in kwargs.keys() and kwargs['cover_path'] is not '' and isinstance(kwargs['cover_path'], str):
        with open(kwargs['cover_path'], "rb") as cover_file:
            cover_data = cover_file.read()
            audiofile["APIC"] = APIC(encoding=3, mime="image/jpeg", type=3, desc=u"Cover", data=cover_data)
    if 'title' in kwargs.keys():
        audiofile["TIT2"] = TIT2(encoding=3, text=kwargs['title'])
    if 'album' in kwargs.keys():
        audiofile["TALB"] = TALB(encoding=3, text=kwargs['album'])
    if 'artist' in kwargs.keys():
        audiofile["TPE1"] = TPE1(encoding=3, text=kwargs['artist'])
    if 'track' in kwargs.keys():
        audiofile["TRCK"] = TRCK(encoding=3, text=kwargs['track'])
    if 'genre' in kwargs.keys():
        audiofile["TCON"] = TCON(encoding=3, text=kwargs['genre'])
    audiofile.save()


def load_metadata(mp3_path: str) -> dict:
    tags = ID3(mp3_path)
    if "TIT2" in tags.keys():
        title = tags["TIT2"]
    else:
        title = ""
    if "TPE1" in tags.keys():
        artist = tags["TPE1"]
    else:
        artist = ""
    if "TALB" in tags.keys():
        album = tags["TALB"]
    else:
        album = ""
    if "APIC:" in tags.keys():
        cover = tags["APIC:"]
        cover_image = Image.open(BytesIO(cover.data))
    elif "APIC:Cover" in tags.keys():
        cover = tags["APIC:Cover"]
        cover_image = Image.open(BytesIO(cover.data))
    else:
        cover_image = None
    if "TCON" in tags.keys():
        genre = tags["TCON"]
    else:
        genre = ""
    if "TRCK" in tags.keys():
        track_number = tags["TRCK"]
    else:
        track_number = ""

    return {'title': title, 'artist': artist,
            'album': album, 'genre': genre,
            'track': track_number, 'cover_image': cover_image}
