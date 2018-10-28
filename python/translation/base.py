from .alias import AliasTranslator
from .vred import VREDTranslator


class ATFTranslator(object):
    def __init__(self, group_name, path, resources_dir):
        self.group_name = group_name
        self.path = path
        self.resources_dir = resources_dir

    def translate(self):
        if self.group_name == "alias":
            translator = AliasTranslator(self.path, self.resources_dir)
        elif self.group_name == "vred":
            translator = VREDTranslator(self.path, self.resources_dir)

        return translator.translate()

    def get_thumbnail_data(self, svf_path=None):
        if self.group_name == "alias":
            translator = AliasTranslator(self.path, self.resources_dir, svf_path)
        elif self.group_name == "vred":
            translator = VREDTranslator(self.path, self.resources_dir)

        return translator.get_thumbnail_data()
