import os
import shutil

from notebook.base.handlers import IPythonHandler
from notebook.utils import url_path_join
from tornado import ioloop

from empty_trash.config import ResourceUseDisplay
from empty_trash.metrics import TrashMetricsLoader
from empty_trash.prometheus import PrometheusHandler


def _jupyter_server_extension_paths():
    """
    Set up the server extension for collecting size & emptying Trash
    """
    return [{"module": "empty_trash"}]


def _jupyter_nbextension_paths():
    """
    Set up the notebook extension for displaying the button (and the size of Trash)
    """
    return [
        {
            "section": "tree",
            "dest": "empty_trash",
            "src": "static",
            "require": "empty_trash/trash",
        }
    ]


class DeleteTrash(IPythonHandler):
    def delete(self):
        config = self.settings["trash_display_config"]
        folder = config.trash_dir+"files/"
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
        folder = config.trash_dir+"info/"
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
        self.finish("Trash deleted")


def load_jupyter_server_extension(nbapp):
    """
    Called during notebook start
    """

    resuseconfig = ResourceUseDisplay(parent=nbapp)
    nbapp.web_app.settings["trash_display_config"] = resuseconfig

    # This is for the delete-trash stuff
    route_pattern = url_path_join(nbapp.web_app.settings["base_url"], "/del_trash")
    nbapp.web_app.add_handlers(".*", [(route_pattern, DeleteTrash)])

    # This is the ever-shouting promethius loop for values
    callback = ioloop.PeriodicCallback(
        PrometheusHandler(TrashMetricsLoader(nbapp)), 1000
    )
    callback.start()
