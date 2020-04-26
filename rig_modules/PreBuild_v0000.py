"""
singleton method to creating a single joint in the scene.
"""
# import maya modules
from maya import cmds
from rig_modules import template

class_name = "PreBuild"


class PreBuild(template.TemplateModule):
    class_name = class_name
    PUBLISH_ATTRIBUTES = {
        "name": "",
        "moduleType": ""
    }
    ATTRIBUTE_EDIT_TYPES = {
        'line-edit': ["name"],
        'label': ["moduleType"]
    }

    def __init__(self, name=""):
        super(PreBuild, self).__init__(name=name)
        self.name = name

    def create(self):
        """
        do nothing
        :return:
        """
        return True

    def finish(self):
        """
        perform an action of creating a new file.
        :return:
        """
        cmds.file(new=True, f=1)