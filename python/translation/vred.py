import logging
import os
import shutil
import subprocess
import tempfile

logger = logging.getLogger(__name__)


class VREDTranslator(object):
    def __init__(self, path, resources_dir):
        self.path = path
        self.resources_dir = resources_dir

    def translate(self):
        # Get translator
        translator = os.path.join(self.resources_dir, "LMV", "viewing-vpb-lmv.exe")

        # Temporal dir
        tmpdir = tempfile.mkdtemp(prefix='lmv_')

        # File name
        file_name = os.path.basename(self.path)

        # JSON file
        index_path = os.path.join(tmpdir, 'index.json')
        with open(index_path, 'w') as _:
            pass

        # Copy source file locally
        source_path_temporal = os.path.join(tmpdir, file_name)
        shutil.copyfile(self.path, source_path_temporal)

        # Execute translation command
        command = [translator, index_path, source_path_temporal]
        command_line_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process_output, _ = command_line_process.communicate()

        if command_line_process.returncode != 0:
            raise Exception(process_output)

        return tmpdir

    def get_thumbnail_data(self):
        extractor = os.path.join(self.resources_dir, "VREDThumbnailExtractor", "extractMetaData.exe")

        thumb_path = tempfile.NamedTemporaryFile(suffix=".jpg", prefix="sgtk_thumb", delete=False).name
        command = [extractor, "--icv", thumb_path, self.path]

        command_line_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process_output, _ = command_line_process.communicate()

        if command_line_process.returncode != 0:
            raise Exception(process_output)

        with open(thumb_path, "rb") as fh:
            data = fh.read()

        return data
