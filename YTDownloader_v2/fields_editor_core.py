from io import BytesIO

from mutagen.id3 import APIC, ID3, ID3NoHeaderError, TALB, TCON, TIT2, TPE1, TRCK
from PIL import Image


TEXT_FRAMES = {
    "title": ("TIT2", TIT2),
    "artist": ("TPE1", TPE1),
    "album": ("TALB", TALB),
    "genre": ("TCON", TCON),
    "track": ("TRCK", TRCK),
}


def load_metadata(mp3_path: str) -> dict:
    try:
        tags = ID3(mp3_path)
    except ID3NoHeaderError:
        tags = ID3()
    result = {name: str(tags.get(frame_id, "")) for name, (frame_id, _) in TEXT_FRAMES.items()}
    covers = tags.getall("APIC")
    result["cover_image"] = None
    if covers:
        with Image.open(BytesIO(covers[0].data)) as image:
            result["cover_image"] = image.copy()
    return result


def edit_fields(mp3_path: str, cover_image: Image.Image | None = None, **values: str) -> None:
    try:
        tags = ID3(mp3_path)
    except ID3NoHeaderError:
        tags = ID3()
    for name, (frame_id, frame) in TEXT_FRAMES.items():
        if name in values:
            tags.delall(frame_id)
            if values[name]:
                tags.add(frame(encoding=3, text=values[name]))
    if cover_image is not None:
        image = cover_image.convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        tags.delall("APIC")
        tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=buffer.getvalue()))
    tags.save(mp3_path)
