import os
from backend.utils.assets_loader import AssetsLoader
from backend.utils.commands.command import Command


def open_dir_in_explorer(path: str, not_exists_command: Command):
    if not os.path.isdir(path):
        return not_exists_command.execute()

    opener = AssetsLoader.get_env('FILE_OPENER')
    if os.fork() == 0:
        os.execlp(opener, opener, path)
