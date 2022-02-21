import os
from pathlib import Path
from backend.db.playlist_repo import PlaylistRepo
from backend.model.account import Account
from backend.model.playlist_links_fetcher import PlaylistLinksFetcher
from backend.utils.yes_no_dialog import YesNoDialog
from backend.utils.commands.command import CallRcvrCommand, Command
from backend.view.new_playlist_window import NewPlaylistWindow


class NewPlaylistController:
    def __init__(self, account: Account, repo: PlaylistRepo,
                 playlist_fetcher: PlaylistLinksFetcher, on_view_closed: Command):
        self.account = account
        self.repo = repo
        self.playlist_fetcher = playlist_fetcher
        self.view = None
        self.on_view_closed = on_view_closed

    def _add_playlist(self, name: str, url: str, path: str):

        stored = self.account.get_playlist(url)
        if stored is not None:
            msg = f'Playlist with that url was saved at {stored.get_path()}/{stored.get_name()}' + \
                f' at {stored.get_added_at()}\nDo you want to download it again?'

            def clicked(accepted):
                if accepted:
                    self._handle_accepted_playlist(name, url, path)

                self._close_view()

            ynd = YesNoDialog(msg, CallRcvrCommand(lambda: clicked(True)),
                              CallRcvrCommand(lambda: clicked(False)))

            self.view.setDisabled(True)
            ynd.show()
        else:
            self._handle_accepted_playlist(name, url, path)
            self._close_view()

    def _handle_accepted_playlist(self, name: str, url: str, path: str):
        playlist = self.repo.create_playlist(name, url, path)
        self.playlist_fetcher.fetch_playlist_links(playlist)

    def show(self):
        self.view = NewPlaylistWindow(self.on_view_closed, CallRcvrCommand(
            lambda: self._on_playlist_add_requested()))
        self.view.show()

    def _on_playlist_add_requested(self):
        name = self.view.get_name()
        url = self.view.get_url()
        path = self.view.get_path()

        if not url.startswith('http'):
            print('BAD URL')  # TODO
            return

        out_path = str(Path(path).joinpath(name).absolute())

        try:
            os.mkdir(out_path)
        except FileExistsError:
            print('possibly going to overwrite')
        except Exception as e:
            print('Failed to create directory', e)
            return

        self._add_playlist(name, url, out_path)

    def _close_view(self):
        if self.view is not None:
            self.view.close()
            self.view = None
