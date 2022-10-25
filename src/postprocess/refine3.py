import os
from util import *
from shapely.ops import linemerge


ContourRoot = "../../demodata/structure_contours/ContourSvg"
RenderRoot = "../../demodata/Rendered"
Result_dir = "../../demodata/structure_contours/Contour_refined"


svgRoot = traversal_dirs(ContourRoot)
svgfilenames = traversal_files(svgRoot[0])

edge_Overlap_Threshold = 2
LineStringLenghtThreshold = 4
LineStringOverlapThreshHoldD = 1.5

DirCounter = 0

for svgRootDir in svgRoot:
    DirCounter+=1
    working_dir = os.path.split(svgRootDir)[-1]
    print( '\n\n' + working_dir )
    # log_out_dir = os.path.join(Log_dir, working_dir)
    result_out_dir = os.path.join(Result_dir, working_dir)
    RenderDirCurr = os.path.join(RenderRoot, working_dir)
    
    if os.path.exists(RenderDirCurr) is False:
        continue
    

    cuur_svg_filenames = traversal_files(os.path.join(ContourRoot, working_dir))
    if len(cuur_svg_filenames) != 12:
        continue
    
    # if not os.path.exists(log_out_dir):
    #     os.makedirs(log_out_dir)
    if not os.path.exists(result_out_dir):
        os.makedirs(result_out_dir)
        

    for svgname in svgfilenames:
        print(svgname.name.split('.')[0])
        svgfilepath = os.path.join(svgRootDir, svgname.name)

        normal_image_name = 'normal_' + \
            svgname.name.split('.')[0] + "_0001.png"
        normal_image_path = os.path.join(RenderDirCurr, normal_image_name)

        depth_image_name = 'depth_' + \
            svgname.name.split('.')[0] + "_0001.png"
        depth_image_path = os.path.join(RenderDirCurr, depth_image_name)

        mask_image_name = 'mask_' + \
            svgname.name.split('.')[0] + "_0001.png"
        mask_image_path = os.path.join(RenderDirCurr, mask_image_name)

        rgb_image_name = 'image_' + svgname.name.split('.')[0] + ".png"
        rgb_image_path = os.path.join(RenderDirCurr, depth_image_name)

        rgb_image = cv2.imread(rgb_image_path)
        rgb_image_1080 = cv2.resize(rgb_image, (1080, 1080))

        edge_merge = merge_edge_image(
            normal_image_path, depth_image_path, mask_image_path)

        NPR_Polylines, Singular_Points = readlinesfromsvg(
            svgfilepath)
             

        # 使用深度图、法向量、Mask边缘图，根据与边缘先验信息去除错误结构线条
        # polyline_Edge = remove_polyline_by_edge(
        #     edge_merge, NPR_Polylines, 2, 2)
        polyline_Edge = PolyLineSplitByEdge(NPR_Polylines, edge_merge, 0.25)
        # print("Removed_by_Edge: " + str(len(NPR_Polylines) - len(polyline_Edge)))


        # 数据结构转换, polyline转为Shapely MulitLineString
        MultiLineString_C = PolyLine2MulitLingString(polyline_Edge)
        # polyline 相同节点合并
        MultiLineString_C = linemerge(MultiLineString_C)
        MultiLineString_C, ShortLineString = spiltShortLineString(MultiLineString_C, 10)
        
        
        
        MultiLineString_C = RemoveIsolateLineString(MultiLineString_C, distanceThreshHoldD=2, length_Threshhold=15)
        # MultiLineString_C = LineBufferCheckOut2(MultiLineString_C, Overlap_Threshold=0.7, WithShow=False)        
        # MultiLineString_C = linemerge(MultiLineString_C)

        if isinstance(MultiLineString_C, list) is False:
            MultiLineString_C2 = MultiLineString_C
        else:
            delnum_all = 0
            MultiLineString_C2 = []
            for SL in MultiLineString_C:
                xy_v = SL.coords.xy
                if len(xy_v[0]) == 2:
                    MultiLineString_C2.append(SL)
                else:    
                    Simplified_SL, delnum = Simplify_A_LineString(SL, 179.5)
                    MultiLineString_C2.append(Simplified_SL)
                    delnum_all+=delnum
            # print("MulitString removed " + str(delnum_all))

        result_svg_name = svgname.name.split('.')[0] + ".svg"
        result_svg_path = os.path.join(result_out_dir, result_svg_name) 
        try:
            WriteMulitLineStringSvg(MultiLineString_C2, result_svg_path, withJunctions =False)
        except Exception as r:
            WriteSingleLineStringSvg(MultiLineString_C2, result_svg_path)       
        
        # WriteMulitLineStringSvg(MultiLineString_C2, result_svg_path, withJunctions =False)
        print(str(DirCounter) + "..." + str(result_svg_name))
        # try:
        #     MultiLineString_C2 = list(MultiLineString_C2)
        # except Exception as r:
        #     WriteSingleLineStringSvg(MultiLineString_C2, result_svg_path)
        #     continue
        
  