from backend.model.downloadable import Downloadable
from backend.model.downloadable_type import DownloadableType
from backend.model.playlist import Playlist
from backend.model.playlist_link import PlaylistLink
from backend.view.data_list_item import DataListItem
from backend.view.link_list_item import LinkListItem
from backend.view.playlist_list_item import PlaylistListItem


class DataListItemsFactory:
    def create_data_list_item(self, downloadable: Downloadable) -> DataListItem:
        dl_type = downloadable.get_downloadable_type()

        if dl_type == DownloadableType.LINK:
            return self._create_link_list_item(downloadable)
        else:
            return self._create_playlist_list_item(downloadable)

    def _create_link_list_item(self, playlist_link: PlaylistLink) -> LinkListItem:
        list_item = LinkListItem()
        self._init_downloadable_list_item(playlist_link, list_item)

        list_item.name_property.bind(
            playlist_link.get_name_property())

        list_item.playlist_idx_property.bind(
            playlist_link.get_playlist_number_property().as_string())

        list_item.directory_path_property.bind(
            playlist_link.get_playlist().get_path_property())

        return list_item

    def _create_playlist_list_item(self, playlist: Playlist) -> PlaylistListItem:
        list_item = PlaylistListItem()
        self._init_downloadable_list_item(playlist, list_item)

        list_item.name_property.bind(
            playlist.get_name_property())

        list_item.size_property.bind(
            playlist.get_size_property().mapped_as(
                Downloadable.get_formatted_size))

        list_item.speed_property.bind(
            playlist.get_dl_speed_mbps_property().mapped_as(
                Downloadable.get_formatted_dl_speed))

        list_item.directory_path_property.bind(
            playlist.get_path_property())

        return list_item

    def _init_downloadable_list_item(self, downloadable: Downloadable, data_list_item: DataListItem):
        data_list_item.url_property.bind(
            downloadable.get_url_property())

        data_list_item.status_property.bind(
            downloadable.get_status_property().as_string())

        data_list_item.is_resumable_property.bind(
            downloadable.get_status_property().mapped_as(
                lambda _: downloadable.is_resumable()))

        data_list_item.is_resumable_property.bind(
            downloadable.get_resume_requested_property().mapped_as(
                lambda _: downloadable.is_resumable()))

        data_list_item.is_resumable_property.bind(
            downloadable.get_pause_requested_property().mapped_as(
                lambda _: downloadable.is_resumable()))

        data_list_item.is_pausable_property.bind(
            downloadable.get_status_property().mapped_as(
                lambda _: downloadable.is_pausable()))

        data_list_item.is_pausable_property.bind(
            downloadable.get_pause_requested_property().mapped_as(
                lambda _: downloadable.is_pausable()))

        data_list_item.is_pausable_property.bind(
            downloadable.get_resume_requested_property().mapped_as(
                lambda _: downloadable.is_pausable()))

        data_list_item.progress_status_property.bind(
            downloadable.get_size_property().mapped_as(
                lambda _: downloadable.get_dl_progress()))

        data_list_item.progress_status_property.bind(
            downloadable.get_dled_size_property().mapped_as(
                lambda _: downloadable.get_dl_progress()))
