import sys
import os

OBJFILENALE = "normalized_model.obj"
MODELROOTPATH = "../../demodata/3d_future/"
CAMERARAMETERROOTPATH = "../../configs/camera_intrinsic_extrinsic/"
OUTDIR = "../../demodata/transformed_obj/"


def traversal_dirs(path):
    OBJPaths = []
    for item in os.scandir(path):
        if item.is_dir():
            OBJPaths.append(item.path)
            # OBJPaths.append(os.path.join(item.path, OBJFILENALE))
    return OBJPaths


def traversal_files(path):
    RenderParameterFilePath = []
    for item in os.scandir(path):
        if item.is_file():
            RenderParameterFilePath.append(item.path)
    return RenderParameterFilePath


OBJPaths = traversal_dirs(MODELROOTPATH)
CameraParameterFilePath = traversal_files(CAMERARAMETERROOTPATH)


def mk_obj_outdir(OBJpathList):
    for path in OBJpathList:
        working_dir = os.path.split(path)[-1]
        # print("mkdir /remote-home/share/StructureParsingDataset/TransformedModel/" + working_dir)
        os.system(
            "mkdir " + OUTDIR + working_dir)


def TransfromMesh2(OBJpathList, camerafile):
    for path in OBJpathList:
        for camerafile_i in camerafile:

            working_dir = os.path.split(path)[-1]
            outobjname = os.path.split(camerafile_i)[-1][-7:-4] + '.obj'

            commandstr = "./build/TransformOBJ " + \
                path + '/' + OBJFILENALE + ' ' + camerafile_i + ' ' + \
                OUTDIR + \
                working_dir + '/' + outobjname

            # print(commandstr)
            os.system(commandstr)


mk_obj_outdir(OBJPaths)
TransfromMesh2(OBJPaths, CameraParameterFilePath)


