from utils.commands.command import Command
from model.db_models import Playlist
from controller.playlist_manager import PlaylistManager
from view.data_summary_box import DataSummaryBox


class ShowDetailsCommand(Command):
    def __init__(self, playlist: Playlist, playlist_manager: PlaylistManager,
                 view: DataSummaryBox):
        self.playlist = playlist
        self.playlist_manager = playlist_manager
        self.view = view

    def execute(self):
        pass
