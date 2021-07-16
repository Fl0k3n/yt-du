from controller.playlist_manager import PlaylistManager
from view.data_summary_box import DataSummaryBox


class DataSummaryController:
    _MAX_VISIBLE = 7

    def __init__(self, playlist_manager: PlaylistManager, view: DataSummaryBox):
        self.playlist_mgr = playlist_manager
        self.view = view

        self.item_count = self.playlist_mgr.get_item_count()
        self.view.set_item_count(self.item_count)

        self.playlists = self.playlist_mgr.get_playlists(
            limit=self._MAX_VISIBLE)

        self.visible_items = [item.to_data_list_item()
                              for item in self.playlists]

        view.show_all(self.visible_items)
