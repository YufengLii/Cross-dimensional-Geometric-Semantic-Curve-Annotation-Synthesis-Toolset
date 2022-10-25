import pymesh
import sys
import os
import pymeshlab

MODELROOTPATH = "../../demodata/transformed_obj/"
OUTDIR = "../../demodata/cleaned_obj/"


def traversal_dirs(path):
    OBJPaths = []
    for item in os.scandir(path):
        if item.is_dir():
            OBJPaths.append(item.name)
            # OBJPaths.append(os.path.join(item.path, OBJFILENALE))
    return OBJPaths

ALLOBJPaths = traversal_dirs(MODELROOTPATH)


def traversal_files(path):
    RenderParameterFilePath = []
    for item in os.scandir(path):
        if item.is_file():
            RenderParameterFilePath.append(item.name)
    return RenderParameterFilePath

OBJFILENAMES = traversal_files(os.path.join(MODELROOTPATH, ALLOBJPaths[0]))

fo = open('bad.txt', 'a')

def CleanOBJMesh(WORKINGOBJDIR):
    Counter = 1

    for CurrOBJDir in WORKINGOBJDIR:
        # print(CurrOBJDir)
        OBJFILENAMES = traversal_files(os.path.join(MODELROOTPATH, CurrOBJDir))
        if len(OBJFILENAMES) != 12:
            print('empty')
            continue
        OutMeshDIR = os.path.join(OUTDIR, CurrOBJDir)
        if os.path.exists(OutMeshDIR):
            print("file exists! cleaned before...")
            filenames = traversal_files(OutMeshDIR)
            if len(filenames) != 12:
                fo.write(CurrOBJDir)
                # os.system("rm -rf " + str(OutMeshDIR))
                # print("del error files")
            continue
        else:
            os.system('mkdir ' + OutMeshDIR)
        for CurrObjFileName in OBJFILENAMES:
            InputMeshPath = os.path.join(MODELROOTPATH, CurrOBJDir)
            InputMeshPath = os.path.join(InputMeshPath, CurrObjFileName)
            OutMeshpath = os.path.join(OutMeshDIR, CurrObjFileName)
            
            try:
                ms = pymeshlab.MeshSet()
                ms.load_new_mesh(InputMeshPath)
                ms.load_filter_script('meshlab_clean.mlx')

                ms.apply_filter_script()
                ms.save_current_mesh(OutMeshpath)
            except:
                os.system('rm ' + OutMeshDIR)
                continue
            
        print(str(CurrOBJDir) + " cleaned!")
        Counter+=1
CleanOBJMesh(ALLOBJPaths)
fo.close()