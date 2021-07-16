from backend.model.db_models import Playlist
from controller.playlist_manager import PlaylistManager
from utils.yes_no_dialog import YesNoDialog
from utils.commands.command import CallRcvrCommand, Command
from view.new_playlist_window import NewPlaylistWindow


class NewPlaylistController:
    def __init__(self, playlist_manager: PlaylistManager, on_view_closed: Command):
        self.playlist_manager = playlist_manager
        self.view = None
        self.on_view_closed = on_view_closed

    def _add_playlist(self, name: str, url: str, path: str):
        playlist = Playlist(name=name, url=url, directory_path=path)

        stored = self.playlist_manager.get_playlist(url)
        if stored is not None:
            msg = f'Playlist with that url was saved at {stored.directory_path}/{stored.name}' + \
                f'at {stored.added_at}\nDo you want to download it again?'

            def clicked(accepted):
                if accepted:
                    self.playlist_manager.add_playlist(playlist)

                self._close_view()

            ynd = YesNoDialog(msg, CallRcvrCommand(lambda: clicked(True)),
                              CallRcvrCommand(lambda: clicked(False)))

            self.view.setDisabled(True)
            ynd.show()
        else:
            self.playlist_manager.add_playlist(playlist)
            self._close_view()

    def show(self):
        self.view = NewPlaylistWindow(self.on_view_closed, CallRcvrCommand(
            lambda: self._on_playlist_add_requested()))
        self.view.show()

    def _on_playlist_add_requested(self):
        url, name, path = [inp.text() for inp in self.view.get_inputs()]
        self._add_playlist(name, url, path)

    def _close_view(self):
        if self.view is not None:
            self.view.close()
            self.view = None