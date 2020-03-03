"""
control_utils.py utility module for manipulating controllers
"""
# import standard modules
import re
from functools import partial

# import local modules
import read_sides
from maya_utils import file_utils
from maya_utils import object_utils
from maya_utils import attribute_utils
from maya_utils import transform_utils
from maya_utils import curve_utils

# import maya modules
from maya import cmds

# define private variables
__control_folder_dir__ = file_utils.controller_data_dir()

# define local variables
CTRL_SUFFIX = 'ctrl'
LOCATOR_SUFFIX = 'loc'
re_brackets = re.compile(r'\[|]')
transform_attrs = attribute_utils.Attributes.DEFAULT_ATTR_VALUES
side_cls = read_sides.Sides()


def get_controllers():
    """
    get all controllers in scene.
    :return: <tuple> controller objects.
    """
    return tuple(cmds.ls('*_{}'.format(CTRL_SUFFIX)))


def get_selected_ctrl():
    """
    the joints from current selection.
    :return: <tuple> array of joints from selection.
    """
    selected_obj = object_utils.get_selected_node()
    if selected_obj and object_utils.is_shape_curve(selected_obj):
        return selected_obj


def mirror_transforms(object_name=""):
    """
    mirror the transform controllers. **Must have corresponding left/ right naming.
    :param object_name: <str> the object to get transform values and find the mirror object from.
    :return: <bool> True for success. <bool> False for failure.
    """
    if not object_name:
        object_name = object_utils.get_selected_node(single=True)
    mirror_obj_name = ''
    if '_l_' in object_name:
        mirror_obj_name = object_name.replace('_l_', '_r_')
    if '_r_' in object_name:
        mirror_obj_name = object_name.replace('_r_', '_l_')
    if mirror_obj_name == mirror_obj_name:
        return False
    p_object = object_utils.get_transform_relatives(
        object_name, find_parent=True, as_strings=True)[0]
    p_mirror_object = object_utils.get_transform_relatives(
        mirror_obj_name, find_parent=True, as_strings=True)[0]
    p_trm = transform_utils.Transform(p_object)
    matrix = p_trm.world_matrix()
    mirror_matrix = p_trm.mirror_matrix(matrix)
    cmds.xform(p_mirror_object, m=mirror_matrix, ws=1)
    return True


def create_locators():
    """
    create locators on position
    """
    for sl in cmds.ls(sl=1):
        if '.' in sl:
            name, dot, num = sl.partition('.')
            matrix = False
            translate = True
            name += '_{}'.format(re_brackets.sub('', num))
        else:
            matrix = True
            translate = False
            name = sl
        locator_name = name + '_{}'.format(LOCATOR_SUFFIX)
        cmds.createNode('locator', name=locator_name + 'Shape')
        object_utils.snap_to_transform(locator_name, sl, matrix=matrix, translate=translate)
    return True


def copy_xform(object_1, object_2):
    """
    copy the worldSpace matrix from object_2 to object_1.
    :param object_1: <str> the first object to snap the second object to.
    :param object_2: <str> the second object.
    :return: <bool> True for success.
    """
    x_mat = cmds.xform(object_1, m=1, q=1, ws=1)
    cmds.xform(object_2, m=x_mat, ws=1)
    return True


def check_locator_suffix_name(object_name):
    """
    checks if the incoming object has the locator suffix name.
    :param object_name:
    :return:
    """
    suffix_name = '_{}'.format(LOCATOR_SUFFIX)
    if suffix_name in object_name:
        return True
    return False


def remove_locator_suffix_name(object_name):
    """
    splits the object name from its locator suffix name.
    :param object_name:
    :return:
    """
    suffix_name = '_{}'.format(LOCATOR_SUFFIX)
    return object_name.rpartition(suffix_name)[0]


def check_control_suffix_name(object_name):
    """
    checks if the incoming object has the locator suffix name.
    :param object_name: <str> the object name to split.
    :return: <str> formatted name.
    """
    suffix_name = '_{}'.format(CTRL_SUFFIX)
    if suffix_name in object_name:
        return True
    return False


def remove_control_suffix_name(object_name):
    """
    splits the object name from its control suffix name.
    :param object_name: <str> the object name to split.
    :return: <str> formatted name.
    """
    return object_name.rpartition('_{}'.format(CTRL_SUFFIX))[0]


def snap_control_to_selected_locator():
    """
    snap the controller to the selected locator with the same leading name.
    :return: <bool> True for success.
    """
    for sl in cmds.ls(sl=1, type='transform'):
        if not check_locator_suffix_name(sl):
            continue
        ctrl_name = remove_locator_suffix_name(sl)
        copy_xform(ctrl_name, sl)
    return True


def get_shape_names(transforms_array=()):
    """
    from an array of transform objects given, return an array of associated shape names.
    :param transforms_array: <tuple> array of transform objects
    :return: <tuple> shape names.
    """
    shapes_array = ()
    for transform_name in transforms_array:
        shapes_array += object_utils.get_shape_name(transform_name, "nurbsCurve")
    return shapes_array


def color_code_controllers():
    """
    color code all controller shape names.
    :return: <bool> True for success.
    """
    ctrl_curves = get_controllers()
    shape_names_array = get_shape_names(ctrl_curves)
    for shape_name in shape_names_array:
        # get a uniform side name
        side_name = side_cls.side_name_from_string(shape_name)
        if side_name == 'Center':
            curve_utils.set_nurb_shape_color(shape_name, color='yellow')
        if side_name == 'Left':
            curve_utils.set_nurb_shape_color(shape_name, color='blue')
        if side_name == 'Right':
            curve_utils.set_nurb_shape_color(shape_name, color='red')
    return True


def attr_str(ctrl_name, attr_name):
    """
    join the two strings together to form the attribute name.
    :param ctrl_name:
    :param attr_name:
    :return:
    """
    return '{}.{}'.format(ctrl_name, attr_name)


def zero_controllers():
    """
    assuming controllers are all named with a suffix _ctrl
    :return: <bool> True for success.
    """
    for ctrl_name in get_controllers():
        for attr_name, attr_val in transform_attrs.items():
            ctrl_attribute = attr_str(ctrl_name, attr_name)
            cmds.setAttr(ctrl_attribute, attr_val)
    return True


def zero_all_controllers():
    """
    zeroes out all the scene controllers.
    :return: <bool> True for success.
    """
    for ctrl_name in get_controllers():
        c_attr = attribute_utils.Attributes(ctrl_name, keyable=True)
        if c_attr.non_zero_attributes():
            c_attr.zero_attributes()
    return True


def get_controller_path(shape_name):
    """
    returns the shape name path.
    :param shape_name:
    :return:
    """
    return file_utils.concatenate_path(__control_folder_dir__, shape_name)


def save_controller_shape(controller_name):
    """
    saves the controller shape data to file.
    :return: <str> controller file path name.
    """
    curve_data = curve_utils.get_nurb_data(controller_name)
    controller_data_file_name = get_controller_path(controller_name)
    json_cls = file_utils.JSONSerializer(file_name=controller_data_file_name)
    json_cls.write(data=curve_data)
    print("[ControllerShapeFile] :: {}".format(json_cls.file_name))
    return controller_data_file_name


def find_shape_in_dir(shape_name):
    """
    returns the shape name from the directory.
    :param shape_name:
    :return:
    """
    return filter(lambda x: shape_name in file_utils.split_file_name(x), find_controller_shapes())


def is_shape_in_dir(shape_name):
    """
    finds if the file name is in the directory.
    :param shape_name: <str> find this name in the shape directory.
    :return: <bool> the shape name exists in directory.
    """
    return bool(find_shape_in_dir(shape_name))


def get_controller_data_file(shape_name):
    """
    get the data from shape name given.
    :param shape_name:
    :return:
    """
    if not is_shape_in_dir(shape_name):
        raise IOError("[NoControllerShapesFoundInDir] :: {}".format(shape_name))
    shape_file = find_shape_in_dir(shape_name)[0]
    controller_data_file_name = get_controller_path(shape_file)
    json_cls = file_utils.JSONSerializer(file_name=controller_data_file_name)
    return json_cls.read()


def find_controller_shapes():
    """
    finds all the saves controller shapes.
    :return: <tuple> array of files.
    """
    return file_utils.list_controller_files()


def insert_groups(object_name="", names=()):
    """
    insert transform groups.
    :param object_name: <str> insert groups here.
    :param names: <tuple> array of names to use to create the groups with.
    :return:
    """
    grps = ()
    for name in names:
        grps += object_utils.insert_transform(object_name, name),
    return grps


def create_controller_shape(shape_name):
    """
    creates the shape from the file.
    :param shape_name:
    :return: <tuple> array of created curves.
    """
    curve_data = get_controller_data_file(shape_name)
    curves = ()
    for c_name, c_data in curve_data.items():
        form = c_data['form']
        knots = c_data['knots']
        cvs = c_data['cvs']
        degree = c_data['degree']
        order = c_data['order']
        cv_length = len(cvs)
        cv_points = ()
        # knot = cv_length + degree - 1
        for cv_point in cvs:
            cv_points += cv_point[1:],
        curves += cmds.curve(p=cv_points, k=knots[:-2], degree=degree),
    return curves


def get_curve_shapes_in_array(curve_names):
    """
    get the curve shape names in the array given.
    :param curve_names:
    :return:
    """
    c_shapes = ()
    for c_name in curve_names:
        c_shapes += object_utils.get_shape_name(c_name)[0],
    return c_shapes


def parent_curve_shapes(curve_names):
    """
    parents the shapes of the curves to the last curve in the array.
    :param curve_names: <tuple> array of objects to parent.
    :return: <str> the name of the curve.
    """
    curve_name = curve_names[-1]
    if len(curve_names) != 1:
        curve_shapes = list(get_curve_shapes_in_array(curve_names))
        cmds.parent(curve_shapes[:-1] + [curve_name], r=True, s=True)
        cmds.delete(curve_names[:-1])
    return curve_name


def create_control(shape_name, name='', groups=('grp',)):
    """
    create a controller object with specified groups.
    :param shape_name: <str> create this shape.
    :param name: <str> the name of the controller to name.
    :param groups: <tuple> array of group suffixes to create.
    :return: <tuple> group names belonging to this controller name.
    """
    return_data = {}
    curve_names = create_controller_shape(shape_name)
    curve_name = parent_curve_shapes(curve_names)
    if name:
        curve_name = cmds.rename(curve_name, name)
    else:
        curve_name = cmds.rename(curve_name, shape_name)
    return_data['controller'] = curve_name
    group_names = map(lambda x: '{}_{}'.format(curve_name, x), groups)
    grps = insert_groups(curve_name, names=group_names)
    return_data['group_names'] = grps
    return return_data


def create_control_at_transform(object_name, name='', shape_name="cube"):
    """
    creates a controller object at the same space as the transform.
    :param shape_name: <str> build this shape.
    :return: <str> control grp.
    """
    tfm = transform_utils.Transform(object_name)
    ctrl_data = create_control(shape_name, name=name)
    grps = ctrl_data['group_names']
    cmds.xform(grps[-1], m=tfm.world_matrix(), ws=1)
    return ctrl_data


def create_controls(objects_array, name, shape_name="cube"):
    """
    creates controllers at this transform object name.
    :param name: <str> create curves with this object name.
    :param objects_array: <tuple> array of objects.
    :param shape_name: <str> build this shape.
    :return:
    """
    names = ()
    for idx in range(len(objects_array)):
        names += '{}_{}_{}'.format(name, idx, CTRL_SUFFIX),
    groups = ()
    for trfm_name, obj_name in zip(objects_array, names):
        groups += create_control_at_transform(trfm_name, obj_name, shape_name),
    return groups