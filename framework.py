# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.
import os

import sgtk


class ATFFramework(sgtk.platform.Framework):
    def __str__(self):
        return "ATF Framework"

    def init_framework(self):
        """
        Init this framework.

        Post an old cached data cleanup in the background
        """
        self.log_debug("%s: Initializing..." % self)

    def destroy_framework(self):
        """
        Destroy this framework.

        If an old cached data cleanup was posted in the background, stop it
        immediately.
        """
        self.log_debug("%s: Destroying..." % self)

    def translate(self, group_name, path):
        resources_dir = os.path.join(self.disk_location, "resources")
        translation = self.import_module("translation").ATFTranslator(group_name, path, resources_dir)

        return translation.translate()

    def get_thumbnail_data(self, group_name, path):
        resources_dir = os.path.join(self.disk_location, "resources")
        translation = self.import_module("translation").ATFTranslator(group_name, path, resources_dir)

        return translation.get_thumbnail_data()
