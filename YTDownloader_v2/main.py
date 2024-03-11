from app_core import YTDownloader
from fields_editor_frame import remove_temp


if __name__ == '__main__':
    YTD = YTDownloader()
    YTD.run()
    remove_temp()

