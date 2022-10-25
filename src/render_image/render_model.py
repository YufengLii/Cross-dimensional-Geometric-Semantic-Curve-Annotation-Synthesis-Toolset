'''
Render multi-view image for object with texture and
generate model with same orientation with rendered image

'''
import argparse, sys, os, time
import math
import numpy as np
import pdb

# add current path to env
sys.path.append(os.getcwd())
# add custom python env
# sys.path += ['/home/helab/.virtualenvs/3dfuture/lib/python3.5/site-packages']

from utils.blender_utils import *
from utils.utils import *
from math import radians
from scipy.spatial.transform import Rotation as R_

parser = argparse.ArgumentParser(description='Renders given obj file by rotation a camera around it.')
parser.add_argument('--views', type=int, default=12,
                    help='number of views to be rendered')
parser.add_argument('--output_folder', type=str, default='/tmp',
                    help='The path the output will be dumped to.')
parser.add_argument('--scale', type=float, default=1,
                    help='Scaling factor applied to model. Depends on size of mesh.')
parser.add_argument('--remove_doubles', type=bool, default=True,
                    help='Remove double vertices to improve mesh quality.')
parser.add_argument('--edge_split', type=bool, default=True,
                    help='Adds edge split filter.')
parser.add_argument('--depth_scale', type=float, default=1.0,
                    help='Scaling that is applied to depth. Depends on size of mesh. Try out various values until you get a good result. Ignored if format is OPEN_EXR.')
parser.add_argument('--color_depth', type=str, default='16',
                    help='Number of bit per channel used for output. Either 8 or 16.')
parser.add_argument('--format', type=str, default='PNG',
                    help='Format of files generated. Either PNG or OPEN_EXR')
parser.add_argument('--model_file', type=str, default='data/mv_data/norm_models/normalized_model.obj',
                    help='file of model')
parser.add_argument('--texture_file', type=str, default='data/mv_data/texture/texture.png',
                    help='file of texture')

argv = sys.argv[sys.argv.index("--") + 1:]
args = parser.parse_args(argv)

import bpy
import pdb


def get_3x4_RT_matrix_from_blender2(obj):
    isCamera = (obj.type == 'CAMERA')
    R_BlenderView_to_OpencvView = np.diag([1 if isCamera else -1,-1,-1])

    location, rotation = obj.matrix_world.decompose()[:2]
    R_BlenderView = rotation.to_matrix().transposed()

    T_BlenderView = -1.0 * R_BlenderView@location

    R_Opencv = R_BlenderView_to_OpencvView @ R_BlenderView
    T_Opencv = R_BlenderView_to_OpencvView @ T_BlenderView

    RT_Opencv = Matrix(np.column_stack((R_Opencv, T_Opencv)))

    return RT_Opencv, R_Opencv, T_Opencv




def get_calibration_matrix_K_from_blender(camd):
    f_in_mm = camd.lens
    scene = bpy.context.scene
    resolution_x_in_px = scene.render.resolution_x
    resolution_y_in_px = scene.render.resolution_y
    scale = scene.render.resolution_percentage / 100
    sensor_width_in_mm = camd.sensor_width
    sensor_height_in_mm = camd.sensor_height
    pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
    if (camd.sensor_fit == 'VERTICAL'):
        # the sensor height is fixed (sensor fit is horizontal), 
        # the sensor width is effectively changed with the pixel aspect ratio
        s_u = resolution_x_in_px * scale / sensor_width_in_mm / pixel_aspect_ratio 
        s_v = resolution_y_in_px * scale / sensor_height_in_mm
    else: # 'HORIZONTAL' and 'AUTO'
        # the sensor width is fixed (sensor fit is horizontal), 
        # the sensor height is effectively changed with the pixel aspect ratio
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y
        s_u = resolution_x_in_px * scale / sensor_width_in_mm
        s_v = resolution_y_in_px * scale * pixel_aspect_ratio / sensor_height_in_mm
    

    # Parameters of intrinsic calibration matrix K
    alpha_u = f_in_mm * s_u
    alpha_v = f_in_mm * s_v
    u_0 = resolution_x_in_px * scale / 2
    v_0 = resolution_y_in_px * scale / 2
    skew = 0 # only use rectangular pixels

    K = Matrix(
        ((alpha_u, skew,    u_0),
        (    0  , alpha_v, v_0),
        (    0  , 0,        1 )))
    return K

# Returns camera rotation and translation matrices from Blender.
# 
# There are 3 coordinate systems involved:
#    1. The World coordinates: "world"
#       - right-handed
#    2. The Blender camera coordinates: "bcam"
#       - x is horizontal
#       - y is up
#       - right-handed: negative z look-at direction
#    3. The desired computer vision camera coordinates: "cv"
#       - x is horizontal
#       - y is down (to align to the actual pixel coordinates 
#         used in digital images)
#       - right-handed: positive z look-at direction
def get_3x4_RT_matrix_from_blender(cam):
    # bcam stands for blender camera
    R_bcam2cv = Matrix(
        ((1, 0,  0),
         (0, -1, 0),
         (0, 0, -1)))

    # Transpose since the rotation is object rotation, 
    # and we want coordinate rotation
    # R_world2bcam = cam.rotation_euler.to_matrix().transposed()
    # T_world2bcam = -1*R_world2bcam * location
    #
    # Use matrix_world instead to account for all constraints
    location, rotation = cam.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()

    # Convert camera location to translation vector used in coordinate changes
    # T_world2bcam = -1*R_world2bcam*cam.location
    # Use location from matrix_world to account for constraints:     
    T_world2bcam = -1*R_world2bcam * location

    # Build the coordinate transform matrix from world to computer vision camera
    # NOTE: Use * instead of @ here for older versions of Blender
    # TODO: detect Blender version
    R_world2cv = R_bcam2cv*R_world2bcam
    T_world2cv = R_bcam2cv*T_world2bcam

    # put into 3x4 matrix
    RT = Matrix((
        R_world2cv[0][:] + (T_world2cv[0],),
        R_world2cv[1][:] + (T_world2cv[1],),
        R_world2cv[2][:] + (T_world2cv[2],)
         ))

    # xyzxzy = np.zeros((3,3))
    # xyzxzy[0][2] = -1
    # xyzxzy[1][0] = 1
    # xyzxzy[2][1] = 1

    # RMM = R_world2cv * xyzxzy

    # RTM = Matrix((
    #     RMM[0][:] + (T_world2cv[0],),
    #     RMM[1][:] + (T_world2cv[1],),
    #     RMM[2][:] + (T_world2cv[2],)
    #      ))

    return RT, R_world2cv, T_world2cv

def get_3x4_P_matrix_from_blender(cam):
    K = get_calibration_matrix_K_from_blender(cam.data)
    RT, R_world2cv, T_world2cv  = get_3x4_RT_matrix_from_blender(cam)


    return K*RT, K, RT


### setting
bpy.context.scene.use_nodes = True
tree = bpy.context.scene.node_tree
links = tree.links

# Add passes for additionally dumping albedo and normals.
bpy.context.scene.render.layers["RenderLayer"].use_pass_normal = True
# bpy.context.scene.render.layers["RenderLayer"].use_pass_color = True
bpy.context.scene.render.layers["RenderLayer"].use_pass_environment = True
bpy.context.scene.render.image_settings.file_format = args.format
bpy.context.scene.render.image_settings.color_depth = args.color_depth

# Clear default nodes
for n in tree.nodes:
    tree.nodes.remove(n)

# Create input render layer node.
render_layers = tree.nodes.new('CompositorNodeRLayers')

depth_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
depth_file_output.label = 'Depth Output'
if args.format == 'OPEN_EXR':
    links.new(render_layers.outputs['Depth'], depth_file_output.inputs[0])
else:
    # Remap as other types can not represent the full range of depth.
    normalize = tree.nodes.new(type="CompositorNodeNormalize")
    links.new(render_layers.outputs['Depth'], normalize.inputs[0])
    links.new(normalize.outputs[0], depth_file_output.inputs[0])

scale_normal = tree.nodes.new(type="CompositorNodeMixRGB")
scale_normal.blend_type = 'MULTIPLY'
# scale_normal.use_alpha = True
scale_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 1)
links.new(render_layers.outputs['Normal'], scale_normal.inputs[1])

bias_normal = tree.nodes.new(type="CompositorNodeMixRGB")
bias_normal.blend_type = 'ADD'
# bias_normal.use_alpha = True
bias_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 0)
links.new(scale_normal.outputs[0], bias_normal.inputs[1])

normal_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
normal_file_output.label = 'Normal Output'
links.new(bias_normal.outputs[0], normal_file_output.inputs[0])

albedo_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
albedo_file_output.label = 'Albedo Output'
links.new(render_layers.outputs['Env'], albedo_file_output.inputs[0])

# Delete default cube
bpy.data.objects['Cube'].select = True
bpy.ops.object.delete()
bpy.data.objects['Lamp'].select = True
bpy.ops.object.delete()


def transform_and_save_object(obj_file, save_obj_file, P):
    '''
    align object and rendered images
    '''
    mesh_vertices = get_obj_vertex_ali(obj_file)
    rot_mat = P[:3, :3]
    trans_vec = P[:3, 3]

    # since blender coordinate is different with object coordination, we need to do additional 
    # transformation operations.
    # For mv image rendering, object rotate 90 degrees around x axis in blender. Thus euler angle should be changed as below:
    # blender_coordinate xyz -> object coordinate xzy (x = 90 - x', x: euler in x for object coordinate, x': euler in x for blender coordinate)
    
    # get rotation and translation in object coordinate
    r_blender = R_.from_matrix(rot_mat)
    x_angle, z_angle, y_angle = r_blender.as_euler('xyz', degrees=True) # xyz ->xzy blender_coordinate -> object coordinate
    r_object = R_.from_euler('yxz', [[-y_angle, 90 - x_angle, z_angle]], degrees=True)
    rot_mat_object = r_object.as_matrix()[0]
    dist = np.sqrt(np.square(trans_vec[0]) + np.square(trans_vec[1]) + np.square(trans_vec[2]))
    trans_vec_object = [0, 0, dist]
    
    mesh_vertices_trans = np.transpose(np.dot(rot_mat_object, np.transpose(mesh_vertices)))
    mesh_vertices_trans = mesh_vertices_trans - trans_vec_object
    
    replace_and_save_obj(mesh_vertices_trans.tolist(), obj_file, save_obj_file)

# render main function
def render_function(model_file, texture_file):
    ## render
    model_id = model_file.split('/')[-1].split('.')[0]
    obj_file = model_file
    # print('obj_file')

    # print(obj_file)
    # for ob in bpy.data.objects:
    #     print('---------')
    #     print(ob.name)
    try: bpy.ops.import_scene.obj(filepath=obj_file)
    except: return None
    
    # print('-----------')
    # for ob in bpy.data.objects:
    #     print('---------')
    #     print(ob.name)

    bpy.context.scene.render.engine = 'CYCLES'
    for object in bpy.context.scene.objects:
        # print(object.name)
        if object.name in ['Camera']:
            object.select = False
        else:
            object.select = False
            object.cycles_visibility.shadow = False
    
    bpy.data.worlds['World'].use_nodes = True
    bpy.data.worlds['World'].node_tree.nodes['Background'].inputs[0].default_value[0:3] = (0.75, 0.75, 0.75)
    
    def parent_obj_to_camera(b_camera):
        origin = (0, 0, 0)
        # chaungjian yige kongwuti
        b_empty = bpy.data.objects.new("Empty", None)
        b_empty.location = origin
        b_camera.parent = b_empty  # setup parenting

        scn = bpy.context.scene
        scn.objects.link(b_empty)
        scn.objects.active = b_empty
        return b_empty
    
    # Cameralens = bpy.data.cameras['Camera'].lens
    # Camerasensorheight = bpy.data.cameras['Camera'].sensor_height
    # Camerasensorwidth = bpy.data.cameras['Camera'].sensor_width

    # print('Cameralens---------')
    # print(Cameralens)
    # print('Camera Sensor Height---------')
    # print(Camerasensorheight)
    # print('Camera Sensor Width---------')
    # print(Camerasensorwidth)
    # print('Camera Sensor fx---------')
    # print(Cameralens*Camerasensorwidth/540)
    # print('Camera Sensor fy---------')
    # print(Cameralens*Camerasensorheight/540)

    scene = bpy.context.scene
    bpy.context.scene.cycles.samples = 20
    scene.render.resolution_x = 540 # raw 256
    scene.render.resolution_y = 540 # raw 256
    scene.render.resolution_percentage = 100
    scene.render.alpha_mode = 'TRANSPARENT'
    cam = scene.objects['Camera']
    cam.location = (0, 3.2, 0.8) # modified
    cam.data.angle = 0.9799147248268127
    cam_constraint = cam.constraints.new(type='TRACK_TO')
    cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    cam_constraint.up_axis = 'UP_Y'
    b_empty = parent_obj_to_camera(cam)
    cam_constraint.target = b_empty
    
    # get intrinsic matrix
    K_blender = get_calibration_matrix_K_from_blender(cam.data)
    # K = np.array(K_blender)
    # print('intrinsic matrix')
    # print(K)

    # set lighting
    bpy.ops.object.lamp_add(type='SUN')
    sun = scene.objects['Sun']
    sun.location = (0, 2.0, 2.0)
    # sun.shadow_method = 'NOSHADOW'
    sun_constraint = sun.constraints.new(type='TRACK_TO')
    sun_constraint.target = b_empty

    bpy.ops.object.lamp_add(type='SUN')
    sun = scene.objects['Sun.001']
    sun.location = (1.73, -1.0, 2.0)
    # .shadow_method = 'NOSHADOW'
    sun_constraint = sun.constraints.new(type='TRACK_TO')
    sun_constraint.target = b_empty

    bpy.ops.object.lamp_add(type='SUN')
    sun = scene.objects['Sun.002']
    sun.location = (-1.73, -1.0, 2.0)
    # sun.shadow_method = 'NOSHADOW'
    sun_constraint = sun.constraints.new(type='TRACK_TO')
    sun_constraint.target = b_empty
    
    # load texture 
    bpy.data.materials.new('UVTexture')
    bpy.data.materials['UVTexture'].use_nodes = True
    texture_tree = bpy.data.materials['UVTexture'].node_tree
    texture_links = texture_tree.links
    texture_node = texture_tree.nodes.new("ShaderNodeTexImage")
    texture_node.image = bpy.data.images.load(texture_file)
    texture_links.new(texture_node.outputs[0], texture_tree.nodes['Diffuse BSDF'].inputs[0])
    bpy.data.scenes['Scene'].render.layers['RenderLayer'].material_override = bpy.data.materials['UVTexture']

    fp = args.output_folder
    scene.render.image_settings.file_format = 'PNG'  # set output format to .png

    stepsize = 360.0 / args.views
    rotation_mode = 'XYZ'

    for output_node in [depth_file_output, normal_file_output, albedo_file_output]:
        output_node.base_path = ''
    b_empty.rotation_euler[2] += radians(330)
    
    # render image by views
    pose_dict = {}
    for i in range(args.views):
        print("Rotation {}, {}".format((stepsize * i), radians(stepsize * i)))
        # save_dir = os.path.join(args.output_folder, model_id)
        # save_dir = os.path.join(args.output_folder, 'render')
        save_dir = args.output_folder
        if os.path.exists(save_dir) == False: os.makedirs(save_dir)
        
        scene.render.filepath = os.path.join(save_dir, 'image_' + '{0:03d}'.format(int(i * stepsize)))                              # rgb
        depth_file_output.file_slots[0].path = os.path.join(save_dir, 'depth_' + '{0:03d}'.format(int(i * stepsize)) + '_')         # depth
        normal_file_output.file_slots[0].path = os.path.join(save_dir, 'normal_' + '{0:03d}'.format(int(i * stepsize)) + '_')       # normal
        albedo_file_output.file_slots[0].path = os.path.join(save_dir, 'mask_' + '{0:03d}'.format(int(i * stepsize)) + '_')         # mask
        
        bpy.ops.render.render(write_still=True)  # render still


        RT_Camera_Opencv, R_Camera_Opencv, T_Camera_Opencv = get_3x4_RT_matrix_from_blender(cam)
        # RT_OBJ_Opencv, R_OBJ_Opencv, T_OBJ_Opencv = get_3x4_RT_matrix_from_blender(b_empty)
        # R_Camera_Opencv = np.dot( np.linalg.inv(np.array(R_OBJ_Opencv)), np.array(R_Camera_Opencv) )
        
        # T_Camera_Opencv_np =  np.array(T_Camera_Opencv)

        # print('T_Camera_Opencv_np')
        # print(T_Camera_Opencv_np)


        # T_Camera_Opencv_np = np.dot(np.linalg.inv(np.array(R_OBJ_Opencv)), T_Camera_Opencv_np)

        # print('T_Camera_Opencv_np')
        # print(T_Camera_Opencv_np)

        # RT_Camera_Opencv = np.column_stack((R_Camera_Opencv, T_Camera_Opencv_np))

 
        # print('RT_Camera_Opencv')
        # print(RT_Camera_Opencv)
        # print('RT_OBJ_Opencv')
        # print(RT_OBJ_Opencv)

        # P, K, RT = get_3x4_P_matrix_from_blender(cam)
        rtnew = np.array(RT_Camera_Opencv)
        # rtnew = RT_Camera_Opencv

        # outRTNP = np.array(rtnew)
        save_camera_file = os.path.join(save_dir, 'model_' + '{0:03d}'.format(int(i * stepsize))+ '.txt')

        # pvector = outRTNP.reshape(12)
        # strP = ["%.6f" % number for number in pvector]
        filetxt = open(save_camera_file,'w+')
        filetxt.write('540 540\n')
        filetxt.write('506.24996948 506.24996948 270 270\n\n')
        np.savetxt(filetxt, rtnew, fmt='%f', delimiter=' ')
        # filetxt.write(strP[0][0] + ' ' + strP[0][1] + ' ' + strP[0][2] + ' ' + strP[0][3] + ' \n')
        # filetxt.write(strP[1][0] + ' ' + strP[1][1] + ' ' + strP[1][2] + ' ' + strP[1][3] + ' \n')
        # filetxt.write(strP[2][0] + ' ' + strP[2][1] + ' ' + strP[2][2] + ' ' + strP[2][3] + ' \n')
        filetxt.write("0.0" + ' ' + "0.0" + ' ' + "0.0" + ' ' + "1" + ' \n')
        filetxt.write(' \n')
        filetxt.write('30')
        filetxt.close() 

        P = np.array(cam.matrix_world)

        save_obj_file = os.path.join(save_dir, 'model_' + '{0:03d}'.format(int(i * stepsize))+ '.obj')

        transform_and_save_object(obj_file, save_obj_file, P)
        b_empty.rotation_euler[2] += radians(stepsize)
    
    # clear sys        
    clear_mv()

###### render model images
# model_file = 'data/mv_data/norm_models/0000000.obj'
# texture_file = 'data/mv_data/texture/0000000.png'
render_function(args.model_file, args.texture_file)
