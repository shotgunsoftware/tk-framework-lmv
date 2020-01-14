# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.
import base64
import os
import sgtk
import shutil
import subprocess
import tempfile

ALIAS_VALID_EXTENSION = [".wire"]
VRED_VALID_EXTENSION = [".vpb"]

logger = sgtk.platform.get_logger(__name__)


class LMVTranslator(object):
    """
    """

    def __init__(self, path):
        """
        Class constructor

        :param path: Path to the file we want to translate to LMV
        """
        self.source_path = path
        self.output_directory = None
        self.svf_path = None

    def translate(self, output_directory=None):
        """
        Run the translation to convert the file to LMV
        :param output_path: Path to the directory we want to translate the file to. If no path is supplied, a temporary
                            one will be used
        :return: The path to the directory the LMV files have been written
        """

        self.output_directory = output_directory

        # get the translator path
        translator_path = self.__get_translator_path()

        if self.output_directory is None:
            # generate all the files and folders needed for the translation
            self.output_directory = tempfile.mkdtemp(prefix="lmv_")
        output_path = os.path.join(self.output_directory, os.path.basename(self.source_path))

        index_file_path = os.path.join(self.output_directory, "index.json")
        open(index_file_path, "w").close()

        # copy the source file to the temporary location and run the translation
        logger.debug("Copying source file to temporary folder")
        shutil.copyfile(self.source_path, output_path)

        logger.debug("Running translation process")
        cmd = [
            translator_path,
            index_file_path,
            output_path
        ]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_output, _ = p.communicate()

        if p.returncode != 0:
            raise Exception(p_output)

        return self.output_directory

    def package(self, svf_file_name=None, thumbnail_path=None):
        """
        :return:
        """

        if not self.output_directory or not os.path.isdir(self.output_directory):
            raise Exception("Couldn't package the LMV files: no file seems to have been created")

        output_dir_path = os.path.join(self.output_directory, "output")

        # rename the svf file if needed
        if svf_file_name:
            logger.debug("Renaming SVF file")
            source_path = self.__get_svf_path()
            target_path = os.path.join(output_dir_path, "1", "{}.svf".format(svf_file_name))
            if os.path.isfile(target_path):
                raise Exception("Couldn't rename svf file: target path %s already exists" % target_path)
            os.rename(source_path, target_path)
            self.svf_path = target_path
        else:
            svf_file_name = os.path.splitext(os.path.basename(self.source_path)[0])

        # extract the thumbnails
        thumbnail_path = self.extract_thumbnail(thumbnail_path)

        # zip the package
        logger.debug("Making archive from LMV files")
        zip_path = shutil.make_archive(
            base_name=os.path.join(self.output_directory, svf_file_name),
            format="zip",
            root_dir=output_dir_path
        )

        return zip_path, thumbnail_path

    def extract_thumbnail(self, thumbnail_source_path=None):
        """
        :return:
        """

        if not self.output_directory or not os.path.isdir(self.output_directory):
            raise Exception("Couldn't extract thumbnails from LMV: no file seems to have been created")

        output_dir_path = os.path.join(self.output_directory, "output")
        svf_file_name = os.path.splitext(os.path.basename(self.__get_svf_path()))[0]

        # get the thumbnail data
        if thumbnail_source_path:
            with open(thumbnail_source_path, "rb") as fp:
                thumbnail_data = fp.read()
        else:
            thumbnail_data = self.get_thumbnail_data()

        # write the thumbnails on disk
        logger.debug("Writing thumbnail on disk")
        if thumbnail_data:
            images_dir_path = os.path.join(output_dir_path, "images")
            if not os.path.exists(images_dir_path):
                os.makedirs(images_dir_path)
            tmp_image_path = os.path.join(images_dir_path, "{}.jpg".format(svf_file_name))
            with open(tmp_image_path, "wb") as fp:
                fp.write(thumbnail_data)

            return tmp_image_path

    def get_thumbnail_data(self):
        """
        :return:
        """

        _, ext = os.path.splitext(self.source_path)

        # if the source file is a wire file, we can try to directly read the SVF file to get the thumbnail data
        if ext == ".wire":
            thumbnail_data = self.__get_thumbnail_data_from_source_file()
            if not thumbnail_data:
                thumbnail_data = self.__get_thumbnail_data_from_command_line()
        else:
            thumbnail_data = self.__get_thumbnail_data_from_command_line()

        return thumbnail_data

    def __get_svf_path(self):
        """
        :return:
        """

        if not self.svf_path:
            svf_file_name = "{}.svf".format(os.path.splitext(os.path.basename(self.source_path))[0])
            svf_path = os.path.join(self.output_directory, "output", "1", svf_file_name)
            if not os.path.isfile(svf_path):
                raise Exception("Couldn't find svf file %s" % svf_path)
            self.svf_path = svf_path

        return self.svf_path

    def __get_thumbnail_data_from_command_line(self):
        """
        :return:
        """

        # get the command line to extract data from the thumbnail and execute it
        logger.debug("Running thumbnail extractor process")
        thumbnail_extractor_cmd, output_path = self.__get_thumbnail_extractor_command_line()
        p = subprocess.Popen(thumbnail_extractor_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p_output, _ = p.communicate()

        if p.returncode != 0:
            raise Exception(p_output)

        with open(output_path, "rb") as fp:
            thumbnail_data = fp.read()

        return thumbnail_data

    def __get_thumbnail_data_from_source_file(self):
        """
        :return:
        """

        thumbnail_data = []

        with open(self.source_path) as fp:
            line = fp.readline()
            while line and line != "thumbnail JPEG\n":
                line = fp.readline()
            if not line:
                return thumbnail_data
            line = fp.readline()
            while line != "thumbnail end\n":
                thumbnail_data.append(line.replace("Th ", ""))
                line = fp.readline()

        return base64.b64decode("".join(thumbnail_data))

    def __get_translator_path(self):
        """
        Get the path to the translator we have to use according to the file extension
        :return: The path to the translator
        """

        current_engine = sgtk.platform.current_engine()

        root_dir = _get_resources_folder_path()
        _, ext = os.path.splitext(self.source_path)

        # Alias case
        if ext in ALIAS_VALID_EXTENSION:
            if current_engine.name == "tk-alias":
                software_extractor = os.path.join(current_engine.alias_bindir, "LMVExtractor", "atf_lmv_extractor.exe")
                if os.path.exists(software_extractor):
                    return software_extractor
                else:
                    return os.path.join(root_dir, "LMVExtractor", "atf_lmv_extractor.exe")
            else:
                return os.path.join(root_dir, "LMVExtractor", "atf_lmv_extractor.exe")

        elif ext in VRED_VALID_EXTENSION:
            return os.path.join(root_dir, "LMV", "viewing-vpb-lmv.exe")
        else:
            raise ValueError("Couldn't find translator path: unknown file extension")

    def __get_thumbnail_extractor_command_line(self):
        """
        :return:
        """

        root_dir = _get_resources_folder_path()
        _, ext = os.path.splitext(self.source_path)

        # Alias case
        if ext in ALIAS_VALID_EXTENSION:
            svf_path = self.__get_svf_path()
            tmp_dir = os.path.normpath(
                os.path.join(
                    os.path.dirname(svf_path),
                    "..",
                    "..",
                    "images_{}".format(os.path.splitext(os.path.basename(svf_path))[0])
                )
            )
            # be sure the tmp directory is created
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            cmd = [
                os.path.join(root_dir, "SVFThumbnailExtractor", "svf_thumb.exe"),
                svf_path,
                "-outpath=%s" % tmp_dir,
                "-size=1280",
                "-depth=2",
                "-passes=4"
            ]
            output_path = os.path.join(tmp_dir, "01_thumb_1280x1280.png")

        # VRED case
        elif ext in VRED_VALID_EXTENSION:
            output_path = tempfile.NamedTemporaryFile(suffix=".jpg", prefix="sgtk_thumb", delete=False).name
            cmd = [
                os.path.join(root_dir, "VREDThumbnailExtractor", "extractMetaData.exe"),
                "--icv",
                output_path,
                self.source_path
            ]

        else:
            raise ValueError("Couldn't find thumbnail extractor path: unknown file extension")

        return cmd, output_path


def _get_resources_folder_path():
    """
    :return:
    """
    return os.path.normpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "resources"
        )
    )
