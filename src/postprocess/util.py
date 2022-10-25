from collections import Counter
from svgelements import *
import math
import cv2
from cmath import inf
import numpy as np
import os
from skimage.draw import line
from shapely.ops import linemerge
from shapely.ops import unary_union
from shapely.geometry import MultiLineString
from shapely.geometry import LineString
from shapely.geometry import CAP_STYLE, JOIN_STYLE
import base64
import json
import svgwrite


def angle(v1, v2):
    dx1 = v1[2] - v1[0]
    dy1 = v1[3] - v1[1]
    dx2 = v2[2] - v2[0]
    dy2 = v2[3] - v2[1]
    angle1 = math.atan2(dy1, dx1)
    angle1 = int(angle1 * 180 / math.pi)
    # print(angle1)
    angle2 = math.atan2(dy2, dx2)
    angle2 = int(angle2 * 180 / math.pi)
    # print(angle2)
    if angle1 * angle2 >= 0:
        included_angle = abs(angle1 - angle2)
    else:
        included_angle = abs(angle1) + abs(angle2)
        if included_angle > 180:
            included_angle = 360 - included_angle
    included_angle = included_angle % 180
    return included_angle


def LineBufferCheckOut2(Geo_In, Overlap_Threshold=0.9, WithShow=True):

    Geo_Out = []
    All_Segment_Sorted = []
    DeleteCounter = 0
    Geo_In = MulitLineStringShort2Long(Geo_In)

    if WithShow:
        image = np.ones((1080, 1080, 3), np.uint8) * 255
        for polyline in Geo_In:
            polylinexy = polyline.coords.xy
            COLORS = (np.random.randint(0, 255), np.random.randint(
                0, 255), np.random.randint(0, 255))
            for i in range(len(polylinexy[0])-1):

                image = cv2.line(image, (int(polylinexy[0][i]*2), int(polylinexy[1][i]*2)),
                                 (int(polylinexy[0][i+1]*2), int(polylinexy[1][i+1]*2)
                                  ), COLORS,
                                 1)

    # for A_LineString in Geo_In:
    #     A_LineString_Sort = LineStringShort2Long(A_LineString)
    #     All_Segment_Sorted.extend(A_LineString_Sort)

    for A_LineString in Geo_In:

        AllLineString = []
        ALineString_xy = A_LineString.coords.xy
        for i in range(len(ALineString_xy[0])-1):
            CuurLine = LineString([(ALineString_xy[0][i], ALineString_xy[1][i]),
                                   (ALineString_xy[0][i+1], ALineString_xy[1][i+1])])

            AllLineString.append(CuurLine)
        # A_LineString_Sort = LineStringShort2Long(A_LineString)
        All_Segment_Sorted.extend(AllLineString)

    Geo_buffer = []
    for A_Segment in All_Segment_Sorted:
        # print(len(A_Segment))
        Curr_Buffer = A_Segment.buffer(
            distance=1, cap_style=CAP_STYLE.round)
        Geo_buffer.append(Curr_Buffer)

    NotCompareList = []
    NotCheckList = []
    for index_check in range(len(Geo_buffer)):
        if index_check in NotCheckList:
            continue
        # if All_Segment_Sorted[index_check].length < 0.9:
        #     continue

        check_one = Geo_buffer[index_check]
        DeleteOrNot = False

        if WithShow:
            COLORS = (np.random.randint(0, 255), np.random.randint(
                0, 255), np.random.randint(0, 255))
            polylinexy = list(check_one.exterior.coords)

        cuurcheck_line = All_Segment_Sorted[index_check].coords

        for i in range(index_check, len(Geo_buffer)):
            if i != index_check and i not in NotCompareList:

                Compare_line = All_Segment_Sorted[i].coords
                cuur_angle = angle([cuurcheck_line[0][0], cuurcheck_line[0][1], cuurcheck_line[1][0], cuurcheck_line[1][1]], [
                    Compare_line[0][0], Compare_line[0][1], Compare_line[1][0], Compare_line[1][1]])

                if cuur_angle < 10 and All_Segment_Sorted[index_check].distance(All_Segment_Sorted[i]) < 2:
                    OverlapPolygon = check_one.intersection(Geo_buffer[i])
                    if OverlapPolygon.area / check_one.area > Overlap_Threshold:
                        ob1 = Solution()
                        xlist = [cuurcheck_line[0][0], cuurcheck_line[1]
                                 [0], Compare_line[0][0], Compare_line[1][0]]
                        ylist = [cuurcheck_line[0][1], cuurcheck_line[1]
                                 [1], Compare_line[0][1], Compare_line[1][1]]
                        KB_X_interval = []
                        KB_X_interval.append(
                            [cuurcheck_line[0][0], cuurcheck_line[1][0]])
                        KB_X_interval.append(
                            [Compare_line[0][0], Compare_line[1][0]])
                        result_merge = ob1.merge(KB_X_interval)
                        if len(result_merge) == 1:
                            x1 = result_merge[0][0]
                            x2 = result_merge[0][1]
                            partition = abs(
                                x2-x1) / (abs(cuurcheck_line[0][0]-cuurcheck_line[1][0]) + abs(Compare_line[0][0]-Compare_line[1][0]))
                            if partition < 0.8:
                                for x_index in range(4):
                                    if x1 == xlist[x_index]:
                                        y1 = ylist[x_index]
                                    if x2 == xlist[x_index]:
                                        y2 = ylist[x_index]
                                DeleteCounter += 1
                                NotCompareList.append(index_check)
                                NotCompareList.append(i)
                                NotCheckList.append(index_check)
                                NotCheckList.append(i)

                                DeleteOrNot = True
                                Geo_Out.append(
                                    LineString([(x1, y1), (x2, y2)]))
                                if WithShow:
                                    image = cv2.line(image, (int(x1*2), int(y1*2)),
                                                     (int(x2*2), int(y2*2)
                                                      ), (0, 0, 255),
                                                     2)
                                break

        if DeleteOrNot is False:
            Geo_Out.append(All_Segment_Sorted[index_check])

    print("Remove Segments number: " + str(DeleteCounter))
    if WithShow:
        cv2.imshow('Segment Check Overlap', image)
        cv2.waitKey(0)
    return Geo_Out


def LineStringBufferCheckOut(Geo_In, Overlap_Threshold=0.9, WithShow=False):

    if WithShow:
        image = np.ones((1080, 1080, 3), np.uint8) * 255
    DeleteCounter = 0
    Geo_Out = []
    image = np.ones((1080, 1080, 3), np.uint8) * 255

    Geo_In = MulitLineStringShort2Long(Geo_In)

    Geo_obsdC_buffer = []
    for A_polyline in Geo_In:
        Curr_Buffer = A_polyline.buffer(
            distance=1,  cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.round)
        Geo_obsdC_buffer.append(Curr_Buffer)

    for polyline in Geo_In:
        polylinexy = polyline.coords.xy
        COLORS = (np.random.randint(0, 255), np.random.randint(
            0, 255), np.random.randint(0, 255))
        for i in range(len(polylinexy[0])-1):

            image = cv2.line(image, (int(polylinexy[0][i]*2), int(polylinexy[1][i]*2)),
                             (int(polylinexy[0][i+1]*2), int(polylinexy[1][i+1]*2)
                              ), COLORS,
                             1)

    NotCompareList = []
    for index_check in range(len(Geo_obsdC_buffer)):

        check_one = Geo_obsdC_buffer[index_check]
        COLORS = (np.random.randint(0, 255), np.random.randint(
            0, 255), np.random.randint(0, 255))
        polylinexy = list(check_one.exterior.coords)

        DeleteOrNot = False

        for i in range(len(Geo_obsdC_buffer)):
            if i != index_check and i not in NotCompareList:
                OverlapPolygon = check_one.intersection(Geo_obsdC_buffer[i])
                if OverlapPolygon.area / check_one.area > Overlap_Threshold:
                    # print("need detele")
                    NotCompareList.append(index_check)
                    for i in range(len(polylinexy)-1):
                        image = cv2.line(image, (int(polylinexy[i][0]*2), int(polylinexy[i][1]*2)),
                                         (int(polylinexy[i+1][0]*2), int(polylinexy[i+1][1]*2)
                                          ), (0, 0, 255),
                                         1)
                    DeleteOrNot = True
                    DeleteCounter += 1
                    break
        if DeleteOrNot is False:
            Geo_Out.append(Geo_In[index_check])
    print("Remove LineString number: " + str(DeleteCounter))
    if WithShow:
        return Geo_Out, image
    else:
        return Geo_Out


def SmallLineStringBufferCheckOut(Geo_In, Small_Length=15, Overlap_Threshold=0.9, WithShow=False):

    if WithShow:
        image = np.ones((1080, 1080, 3), np.uint8) * 255
    DeleteCounter = 0
    Geo_Out = []
    image = np.ones((1080, 1080, 3), np.uint8) * 255

    Geo_In = MulitLineStringShort2Long(Geo_In)

    Geo_obsdC_buffer = []
    for A_polyline in Geo_In:

        Curr_Buffer = A_polyline.buffer(
            distance=1,  cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.round)
        Geo_obsdC_buffer.append(Curr_Buffer)

    for polyline in Geo_In:
        polylinexy = polyline.coords.xy
        COLORS = (np.random.randint(0, 255), np.random.randint(
            0, 255), np.random.randint(0, 255))
        if polyline.length < Small_Length:
            for i in range(len(polylinexy[0])-1):

                image = cv2.line(image, (int(polylinexy[0][i]*2), int(polylinexy[1][i]*2)),
                                 (int(polylinexy[0][i+1]*2), int(polylinexy[1][i+1]*2)
                                  ), (0, 0, 255),
                                 1)
        else:
            for i in range(len(polylinexy[0])-1):

                image = cv2.line(image, (int(polylinexy[0][i]*2), int(polylinexy[1][i]*2)),
                                 (int(polylinexy[0][i+1]*2), int(polylinexy[1][i+1]*2)
                                  ), (0, 255, 0),
                                 1)

    NotCompareList = []
    for index_check in range(len(Geo_obsdC_buffer)):
        DeleteOrNot = False
        if Geo_In[index_check].length < Small_Length:

            check_one = Geo_obsdC_buffer[index_check]
            COLORS = (np.random.randint(0, 255), np.random.randint(
                0, 255), np.random.randint(0, 255))
            polylinexy = list(check_one.exterior.coords)

            for i in range(len(Geo_obsdC_buffer)):
                if i != index_check and i not in NotCompareList:
                    OverlapPolygon = check_one.intersection(
                        Geo_obsdC_buffer[i])
                    if OverlapPolygon.area / check_one.area > Overlap_Threshold:
                        # print("need detele")
                        NotCompareList.append(index_check)
                        for i in range(len(polylinexy)-1):
                            image = cv2.line(image, (int(polylinexy[i][0]*2), int(polylinexy[i][1]*2)),
                                             (int(polylinexy[i+1][0]*2), int(polylinexy[i+1][1]*2)
                                              ), (0, 0, 255),
                                             1)
                        DeleteOrNot = True
                        DeleteCounter += 1
                        break
        if DeleteOrNot is False:
            Geo_Out.append(Geo_In[index_check])
    print("Remove < 10 LineString number: " + str(DeleteCounter))
    if WithShow:
        return Geo_Out, image
        # cv2.imshow('Check Overlap', image)
        # cv2.waitKey(0)
    else:
        return Geo_Out


def LineDistanceCheckOut(Geo_In, distance_Threshold=0.5, WithShow=True):

    Geo_Out = []
    All_Segment_Sorted = []
    DeleteCounter = 0
    Geo_In = MulitLineStringShort2Long(Geo_In)

    if WithShow:
        image = np.ones((1080, 1080, 3), np.uint8) * 255
        for polyline in Geo_In:
            polylinexy = polyline.coords.xy
            COLORS = (np.random.randint(0, 255), np.random.randint(
                0, 255), np.random.randint(0, 255))
            for i in range(len(polylinexy[0])-1):

                image = cv2.line(image, (int(polylinexy[0][i]*2), int(polylinexy[1][i]*2)),
                                 (int(polylinexy[0][i+1]*2), int(polylinexy[1][i+1]*2)
                                  ), COLORS,
                                 1)

    for A_LineString in Geo_In:

        AllLineString = []
        ALineString_xy = A_LineString.coords.xy
        for i in range(len(ALineString_xy[0])-1):
            CuurLine = LineString([(ALineString_xy[0][i], ALineString_xy[1][i]),
                                   (ALineString_xy[0][i+1], ALineString_xy[1][i+1])])

            AllLineString.append(CuurLine)
        # A_LineString_Sort = LineStringShort2Long(A_LineString)
        All_Segment_Sorted.extend(AllLineString)

    # Geo_buffer = []
    # for A_Segment in All_Segment_Sorted:
    #     # print(len(A_Segment))
    #     Curr_Buffer = A_Segment.buffer(
    #         distance=1, cap_style=CAP_STYLE.round)
    #     Geo_buffer.append(Curr_Buffer)

    NotCompareList = []
    for index_check in range(len(All_Segment_Sorted)):

        check_one = All_Segment_Sorted[index_check]
        DeleteOrNot = False
        polylinexy = list(check_one.coords)

        for i in range(index_check, len(All_Segment_Sorted)):
            if i != index_check and i not in NotCompareList:

                # distance_min = check_one.distance(All_Segment_Sorted[i])
                # distance_max = check_one.hausdorff_distance(All_Segment_Sorted[i])
                # if distance_min < distance_Threshold  and distance_max < distance_Threshold:
                check_one_first_Point = check_one.coords.xy[0]
                check_one_second_Point = check_one.coords.xy[1]
                curr_one_first_point = All_Segment_Sorted[i].coords.xy[0]
                curr_one_second_point = All_Segment_Sorted[i].coords.xy[1]

                if check_one_first_Point == curr_one_second_point or check_one_second_Point == curr_one_first_point:
                    continue
                distance_min = check_one.distance(All_Segment_Sorted[i])
                distance_max = check_one.hausdorff_distance(
                    All_Segment_Sorted[i])
                if distance_min < distance_Threshold and distance_max < distance_Threshold:
                    # if check_one.almost_equals(All_Segment_Sorted[i], decimal=-0.25) :
                    DeleteCounter += 1
                    NotCompareList.append(index_check)
                    if WithShow:

                        image = cv2.line(image, (int(polylinexy[0][0]*2), int(polylinexy[0][1]*2)),
                                         (int(polylinexy[1][0]*2), int(polylinexy[1][1]*2)
                                          ), (0, 0, 255),
                                         2)
                    DeleteOrNot = True
                    break
        if DeleteOrNot is False:
            Geo_Out.append(All_Segment_Sorted[index_check])
    print("Remove Segments number: " + str(DeleteCounter))
    if WithShow:
        cv2.imshow('Segment Check Overlap', image)
        # cv2.waitKey(0)
    return Geo_Out


# def LineBufferCheckOut(Geo_In, Overlap_Threshold=0.9, WithShow=True):

#     Geo_Out = []
#     All_Segment_Sorted = []
#     DeleteCounter = 0
#     Geo_In = MulitLineStringShort2Long(Geo_In)

#     if WithShow:
#         image = np.ones((1080, 1080, 3), np.uint8) * 255
#         for polyline in Geo_In:
#             polylinexy = polyline.coords.xy
#             COLORS = (np.random.randint(0, 255), np.random.randint(
#                 0, 255), np.random.randint(0, 255))
#             for i in range(len(polylinexy[0])-1):

#                 image = cv2.line(image, (int(polylinexy[0][i]*2), int(polylinexy[1][i]*2)),
#                                  (int(polylinexy[0][i+1]*2), int(polylinexy[1][i+1]*2)
#                                   ), COLORS,
#                                  1)

#     # for A_LineString in Geo_In:
#     #     A_LineString_Sort = LineStringShort2Long(A_LineString)
#     #     All_Segment_Sorted.extend(A_LineString_Sort)

#     for A_LineString in Geo_In:

#         AllLineString = []
#         ALineString_xy = A_LineString.coords.xy
#         for i in range(len(ALineString_xy[0])-1):
#             CuurLine = LineString([(ALineString_xy[0][i], ALineString_xy[1][i]),
#                                    (ALineString_xy[0][i+1], ALineString_xy[1][i+1])])

#             AllLineString.append(CuurLine)
#         # A_LineString_Sort = LineStringShort2Long(A_LineString)
#         All_Segment_Sorted.extend(AllLineString)

#     Geo_buffer = []
#     for A_Segment in All_Segment_Sorted:
#         # print(len(A_Segment))
#         Curr_Buffer = A_Segment.buffer(
#             distance=1, cap_style=CAP_STYLE.round)
#         Geo_buffer.append(Curr_Buffer)

#     NotCompareList = []
#     for index_check in range(len(Geo_buffer)):

#         check_one = Geo_buffer[index_check]
#         DeleteOrNot = False

#         if WithShow:
#             COLORS = (np.random.randint(0, 255), np.random.randint(
#                 0, 255), np.random.randint(0, 255))
#             polylinexy = list(check_one.exterior.coords)
#             # for i in range(len(polylinexy)-1):
#             #     image = cv2.line(image, (int(polylinexy[i][0]*2), int(polylinexy[i][1]*2)),
#             #                         (int(polylinexy[i+1][0]*2), int(polylinexy[i+1][1]*2)
#             #                         ), (0, 0, 255),
#             #                         1)
#         for i in range(index_check, len(Geo_buffer)):
#             if i != index_check and i not in NotCompareList:
#                 OverlapPolygon = check_one.intersection(Geo_buffer[i])
#                 if OverlapPolygon.area / check_one.area > Overlap_Threshold and All_Segment_Sorted[index_check].length > 5:
#                     DeleteCounter += 1
#                     NotCompareList.append(index_check)
#                     if WithShow:
#                         for i in range(len(polylinexy)-1):
#                             image = cv2.line(image, (int(polylinexy[i][0]*2), int(polylinexy[i][1]*2)),
#                                              (int(polylinexy[i+1][0]*2), int(polylinexy[i+1][1]*2)
#                                               ), (0, 0, 255),
#                                              1)
#                     DeleteOrNot = True
#                     break
#         if DeleteOrNot is False:
#             Geo_Out.append(All_Segment_Sorted[index_check])
#     print("Remove Segments number: " + str(DeleteCounter))
#     if WithShow:
#         cv2.imshow('Segment Check Overlap', image)
#         # cv2.waitKey(0)
#     return Geo_Out


def LineStringShort2Long(ALineString):

    Geo_Out = []
    lineLength = []
    AllLineString = []
    ALineString_xy = ALineString.coords.xy
    for i in range(len(ALineString_xy[0])-1):
        CuurLine = LineString([(ALineString_xy[0][i], ALineString_xy[1][i]),
                              (ALineString_xy[0][i+1], ALineString_xy[1][i+1])])
        lineLength.append(CuurLine.length)
        AllLineString.append(CuurLine)

    sort_index = np.flip(np.argsort(np.array(lineLength)))
    for index in sort_index[::-1]:
        Geo_Out.append(AllLineString[index])

    return Geo_Out


def MulitLineStringShort2Long(Geo_IN):
    polylineLength = []
    for polylineI in Geo_IN:
        polylineLength.append(polylineI.length)

    sort_index = np.flip(np.argsort(np.array(polylineLength)))
    Geo_Out = []
    for index in sort_index[::-1]:
        Geo_Out.append(Geo_IN[index])

    return Geo_Out


def WriteMulitLineStringJson(polylines, outfilename, rgb_image_path):

    data = {}
    data['version'] = "4.6.0"
    data["flags"] = {}
    data["shapes"] = []
    data["imagePath"] = outfilename + ".jpg"
    data["imageHeight"] = 520
    data["imageWidth"] = 520

    with open(rgb_image_path, "rb") as img:
        image = base64.b64encode(img.read())
        data['imageData'] = image.decode()  # not just image

    group_id = 1
    for A_polyline in polylines:
        polylinexy = A_polyline.coords.xy
        for i in range(len(polylinexy[0])-1):
            x1 = polylinexy[0][i]
            y1 = polylinexy[1][i]
            x2 = polylinexy[0][i+1]
            y2 = polylinexy[1][i+1]

            shape_i = {}
            shape_i["label"] = "segment"
            shape_i["points"] = []
            shape_i["group_id"] = str(group_id)
            shape_i["shape_type"] = "line"
            shape_i["flags"] = {}

            shape_i["points"].append([x1, y1])
            shape_i["points"].append([x2, y2])

            data["shapes"].append(shape_i)
        group_id += 1
    with open('.\\json\\' + outfilename+'.json', 'w') as outfile:
        json.dump(data, outfile)


def WriteSingleLineStringSvg(A_polyline, svgpath):
    dwg = svgwrite.Drawing(svgpath, size=(540, 540), profile='tiny')
    polylinexy = A_polyline.coords.xy
    COLORS = (np.random.randint(0, 255), np.random.randint(
        0, 255), np.random.randint(0, 255))
    pointsxy = []

    for i in range(len(polylinexy[0])):
        pointsxy.append((polylinexy[0][i], polylinexy[1][i]))

    if polylinexy[0][0] == polylinexy[0][-1] and polylinexy[1][0] == polylinexy[1][-1]:
        print("Polygon")

        dwg.add(
            dwg.polygon(points=pointsxy,
                        stroke=svgwrite.rgb(
                            COLORS[0], COLORS[1], COLORS[2], 'RGB'),
                        stroke_width=1, fill="none"))
    else:
        dwg.add(
            dwg.polyline(points=pointsxy,
                         stroke=svgwrite.rgb(
                             COLORS[0], COLORS[1], COLORS[2], 'RGB'),
                         stroke_width=1, fill="none"))

    dwg.save()


def WriteMulitLineStringSingularSvg(polylines, Singular_points, svgpath):
    dwg = svgwrite.Drawing(svgpath, size=(540, 540), profile='tiny')

    for A_polyline in polylines:

        polylinexy = A_polyline.coords.xy
        COLORS = (np.random.randint(0, 255), np.random.randint(
            0, 255), np.random.randint(0, 255))
        pointsxy = []

        for i in range(len(polylinexy[0])):
            pointsxy.append((polylinexy[0][i], polylinexy[1][i]))

        if polylinexy[0][0] == polylinexy[0][-1] and polylinexy[1][0] == polylinexy[1][-1]:
            print("Polygon")

            dwg.add(
                dwg.polygon(points=pointsxy,
                            stroke=svgwrite.rgb(
                                COLORS[0], COLORS[1], COLORS[2], 'RGB'),
                            stroke_width=1, fill="none"))
        else:
            dwg.add(
                dwg.polyline(points=pointsxy,
                             stroke=svgwrite.rgb(
                                 COLORS[0], COLORS[1], COLORS[2], 'RGB'),
                             stroke_width=1, fill="none"))
    for A_point in Singular_points:
        dwg.add(dwg.circle(center=(A_point[0], A_point[1]), r=1,  fill=svgwrite.rgb(
            A_point[2], A_point[3], A_point[4], 'RGB')))
    

    dwg.save()


def WriteMulitLineStringSvg(polylines, svgpath, withJunctions = False):
    dwg = svgwrite.Drawing(svgpath, size=(540, 540), profile='tiny')

    for A_polyline in polylines:

        polylinexy = A_polyline.coords.xy
        COLORS = (np.random.randint(0, 255), np.random.randint(
            0, 255), np.random.randint(0, 255))
        pointsxy = []

        
        for i in range(len(polylinexy[0])):
            pointsxy.append((polylinexy[0][i], polylinexy[1][i]))
            if withJunctions :
                  
                dwg.add(dwg.circle(center=(polylinexy[0][i], polylinexy[1][i]), r=1,  fill=svgwrite.rgb(
                    COLORS[0], COLORS[1], COLORS[2], 'RGB')))  

        if polylinexy[0][0] == polylinexy[0][-1] and polylinexy[1][0] == polylinexy[1][-1]:
            print("Polygon")

            dwg.add(
                dwg.polygon(points=pointsxy,
                            stroke=svgwrite.rgb(
                                COLORS[0], COLORS[1], COLORS[2], 'RGB'),
                            stroke_width=1, fill="none"))
        else:
            dwg.add(
                dwg.polyline(points=pointsxy,
                             stroke=svgwrite.rgb(
                                 COLORS[0], COLORS[1], COLORS[2], 'RGB'),
                             stroke_width=1, fill="none"))

    dwg.save()


def DrawMulitLineString(polylines, image):
    # image = np.ones((1080, 1080, 3), np.uint8) * 255
    scale = 2
    for polyline in polylines:
        if polyline.length < 5:
            continue
        polylinexy = polyline.coords.xy
        COLORS = (np.random.randint(0, 255), np.random.randint(
            0, 255), np.random.randint(0, 255))
        for i in range(len(polylinexy[0])-1):

            image = cv2.line(image, (int(polylinexy[0][i]*scale), int(polylinexy[1][i]*scale)),
                             (int(polylinexy[0][i+1]*scale), int(polylinexy[1][i+1]*scale)
                              ), COLORS,
                             2)
            # if polyline.length > 10:
            #     image = cv2.line(image, (int(polylinexy[0][i]*scale), int(polylinexy[1][i]*scale)),
            #                      (int(polylinexy[0][i+1]*scale), int(polylinexy[1][i+1]*scale)
            #                       ), COLORS,
            #                      1)

        # image = cv2.circle(
        #     image,
        #     (int(polylinexy[0][0]*scale), int(polylinexy[1][0]*scale)), radius=5, color=COLORS, thickness=1)

        # image = cv2.circle(
        #     image,
        #     (int(polylinexy[0][-1]*scale), int(polylinexy[1][-1]*scale)),
        #     radius=5,
        #     color=COLORS,
        #     thickness=1)
    # cv2.imshow(windowname, image)
    # cv2.waitKey(0)
    return image


def showBufferMulitLineString(windowname, polylines, buffuerPolygon, image):
    # image = np.ones((1080, 1080, 3), np.uint8) * 255
    scale = 2
    polylinexy = polylines.coords.xy
    COLORS = (np.random.randint(0, 255), np.random.randint(
        0, 255), np.random.randint(0, 255))
    for i in range(len(polylinexy[0])-1):

        image = cv2.line(image, (int(polylinexy[0][i]*scale), int(polylinexy[1][i]*scale)),
                         (int(polylinexy[0][i+1]*scale), int(polylinexy[1][i+1]*scale)
                          ), COLORS,
                         1)
    COLORS = (np.random.randint(0, 255), np.random.randint(
        0, 255), np.random.randint(0, 255))
    polylinexy = list(buffuerPolygon.exterior.coords)
    for i in range(len(polylinexy)-1):

        image = cv2.line(image, (int(polylinexy[i][0]*scale), int(polylinexy[i][1]*scale)),
                         (int(polylinexy[i+1][0]*scale), int(polylinexy[i+1][1]*scale)
                          ), COLORS,
                         1)

    # cv2.imshow(windowname, image)
    # cv2.waitKey(0)
    return image

def Simplify_A_LineString(A_LineString, degreeThresh = 179.9):
    
    xy_v = A_LineString.coords.xy
    
    ContinueFlag = True
    delcounter = 0
    
    while ContinueFlag:
        
        if len(xy_v[0]) == 2:
            break
        for index in range(1, len(xy_v[0])-1):
            
            vector_1 = [xy_v[0][index-1] - xy_v[0][index],xy_v[1][index-1]-xy_v[1][index]]
            vector_2 = [xy_v[0][index+1]-xy_v[0][index], xy_v[1][index+1]-xy_v[1][index]]

            unit_vector_1 = vector_1 / np.linalg.norm(vector_1)
            unit_vector_2 = vector_2 / np.linalg.norm(vector_2)
            dot_product = np.dot(unit_vector_1, unit_vector_2)
            angle = math.degrees(np.arccos(dot_product))    
            if angle > degreeThresh:
                xy_v = np.delete(xy_v, index, axis=1)
                # xy_v[0].remove(index)
                # xy_v[1].remove(index)
                ContinueFlag = True
                delcounter+=1
                break
            else:
                ContinueFlag = False
    # print("this string removed " + str(delcounter))
    
    polyline_curr = []
    for index_i in range(len(xy_v[0])):

        polyline_curr.append(
            (xy_v[0][index_i], xy_v[1][index_i]))

    LineString_curr = LineString(polyline_curr)

    return LineString_curr, delcounter
            

    
    
    



class Solution(object):

    def merge(self, intervals):
        """
      :type intervals: List[Interval]
      :rtype: List[Interval]
      """
        if len(intervals) == 0:
            return []
        self.quicksort(intervals, 0, len(intervals) - 1)
        # for i in intervals:
        #print(i.start, i.end)
        stack = []
        stack.append(intervals[0])
        for i in range(1, len(intervals)):
            last_element = stack[len(stack) - 1]
            if last_element[1] >= intervals[i][0]:
                last_element[1] = max(intervals[i][1], last_element[1])
                stack.pop(len(stack) - 1)
                stack.append(last_element)
            else:
                stack.append(intervals[i])
        return stack

    def partition(self, array, start, end):
        pivot_index = start
        for i in range(start, end):
            if array[i][0] <= array[end][0]:
                array[i], array[pivot_index] = array[pivot_index], array[i]
                pivot_index += 1
        array[end], array[pivot_index] = array[pivot_index], array[end]
        return pivot_index

    def quicksort(self, array, start, end):
        if start < end:
            partition_index = self.partition(array, start, end)
            self.quicksort(array, start, partition_index - 1)
            self.quicksort(array, partition_index + 1, end)


def KB_Group_Merge(segments):
    segmentswithKB = []
    for A_line_S in segments:
        if A_line_S[2] == A_line_S[0]:
            K = inf
            b = inf
        else:
            K = (A_line_S[3] - A_line_S[1]) / (A_line_S[2] - A_line_S[0])
            b = A_line_S[3] - K * A_line_S[2]
        segmentswithKB.append(
            [A_line_S[0], A_line_S[1], A_line_S[2], A_line_S[3], K, b])

    kB_group = []
    BelongtoGroup = False
    for A_line_S in segmentswithKB:
        if kB_group == []:
            kB_group.append([A_line_S])
            continue
        for group_id in range(len(kB_group)):

            if math.isinf(A_line_S[4]):
                if math.isinf(kB_group[group_id][0][4]) and math.isinf(
                        kB_group[group_id][0][5]):
                    if kB_group[group_id][0][0] == A_line_S[0]:
                        kB_group[group_id].append(A_line_S)
                        BelongtoGroup = True
                        break
                    else:
                        BelongtoGroup = False
            else:
                if kB_group[group_id][0][4] == A_line_S[4] and kB_group[
                        group_id][0][5] == A_line_S[5]:
                    kB_group[group_id].append(A_line_S)
                    BelongtoGroup = True
                    break
                else:
                    BelongtoGroup = False

        if BelongtoGroup == True:
            continue
        else:
            kB_group.append([A_line_S])
            BelongtoGroup = False

    ob1 = Solution()
    merged_lines = []
    for kB_group_i in kB_group:
        KB_X_interval = []
        # print(kB_group_i)
        if math.isinf(kB_group_i[0][4]):
            for KB_line in kB_group_i:
                KB_X_interval.append([KB_line[1], KB_line[3]])
        else:
            for KB_line in kB_group_i:
                KB_X_interval.append([KB_line[0], KB_line[2]])
        # print(KB_X_interval)
        result_merge = ob1.merge(KB_X_interval)
        # print(result_merge)

        if math.isinf(kB_group_i[0][4]):
            for seg_i in result_merge:
                # print('result_merge length : '+ str(len(result_merge)))
                x1 = int(kB_group_i[0][0])
                x2 = int(kB_group_i[0][0])
                y1 = int(seg_i[0])
                y2 = int(seg_i[1])
                Line_I_length = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                if Line_I_length > 1:
                    merged_lines.append([x1, y1, x2, y2])
        else:
            for seg_i in result_merge:
                # print('result_merge length : '+ str(len(result_merge)))

                x1 = int(seg_i[0])
                x2 = int(seg_i[1])
                y1 = int(kB_group_i[0][4] * x1 + kB_group_i[0][5])
                y2 = int(kB_group_i[0][4] * x2 + kB_group_i[0][5])
                Line_I_length = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                if Line_I_length > 1:
                    merged_lines.append([x1, y1, x2, y2])

    # print('Simplified num line by KB: ' +
    #       str(len(segments) - len(merged_lines)))
    return merged_lines


def showPolyLine(polylines, image, scale=2):

    for A_polyline in polylines:
        COLORS = (np.random.randint(0, 255), np.random.randint(
            0, 255), np.random.randint(0, 255))
        for index_i in range(len(A_polyline)-1):

            image = cv2.line(image, (int(A_polyline[index_i].x*scale), int(A_polyline[index_i].y*scale)),
                             (int(A_polyline[index_i+1].x*scale), int(A_polyline[index_i+1].y*scale)
                              ), COLORS,
                             2)

        # image = cv2.circle(
        #     image,
        #     (int(A_polyline[index_i].x*scale), int(A_polyline[index_i].y*scale)), radius=5, color=COLORS, thickness=1)

        # image = cv2.circle(
        #     image,
        #     (int(A_polyline[index_i+1].x*scale),
        #      int(A_polyline[index_i+1].y*scale)),
        #     radius=5,
        #     color=COLORS,
        #     thickness=1)

    return image
    # cv2.imshow(windowname, image)
    # cv2.waitKey(0)


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
            RenderParameterFilePath.append(item)
    return RenderParameterFilePath


def remove_polyline_by_edge(EdgeImage, PolyLineIn, T_PolyLineLength, T_Edge_Thresh):

    PolyOut = []

    for A_Polyline in PolyLineIn:

        edge_overlap = 0
        LengthPolyline = 0
        for index_i in range(len(A_Polyline)-1):
            A_Line = LineString([(A_Polyline[index_i].x, A_Polyline[index_i].y),
                                 (A_Polyline[index_i+1].x, A_Polyline[index_i+1].y)])

            LengthPolyline += A_Line.length

            discrete_line = list(
                zip(*line(int(A_Polyline[index_i].x), int(A_Polyline[index_i].y), int(A_Polyline[index_i+1].x), int(A_Polyline[index_i+1].y))))
            x = np.array(discrete_line)[:, 1]
            y = np.array(discrete_line)[:, 0]

            for xi, yi in zip(x, y):
                edge_overlap += np.sum(EdgeImage[xi - 1:xi + 2, yi - 1:yi + 2])

        if LengthPolyline < T_PolyLineLength:
            continue

        overlap_level = edge_overlap / LengthPolyline
        if overlap_level >= T_Edge_Thresh:
            PolyOut.append(A_Polyline)

    return PolyOut


def merge_edge_image(normal_image_path, depth_image_path, mask_image_path):

    normal_image = cv2.imread(normal_image_path)
    depth_image = cv2.imread(depth_image_path)
    mask_image = cv2.imread(mask_image_path)

    edges_normal = cv2.Canny(normal_image, 50, 100)
    edges_depth = cv2.Canny(depth_image, 50, 100)
    edges_mask = cv2.Canny(mask_image, 50, 100)

    edges_normal_binary = np.array(edges_normal / 255, bool)
    edges_depth_binary = np.array(edges_depth / 255, bool)
    edges_mask_binary = np.array(edges_mask / 255, bool)

    edge_merge = edges_normal_binary | edges_depth_binary | edges_mask_binary

    return edge_merge


def readlinesfromsvg(svgfile):

    svg = SVG.parse(svgfile)
    NPR_Polylines = []

    Singular_Points = []

    for element in svg.elements():
        try:
            if element.values['visibility'] == 'hidden':
                continue
        except (KeyError, AttributeError):
            pass
        if isinstance(element, Polyline):
            NPR_Polylines.append(element.points)
        if isinstance(element, Circle):
            # if element.fill.blue == 255 and element.fill.green == 0 and element.fill.red == 0:
            #     continue
            Singular_Points.append(
                [element.cx, element.cy, element.fill.red, element.fill.green, element.fill.blue])

    return NPR_Polylines, Singular_Points


def spiltShortLineString(MulitLineStringIn, Threshold=10):

    MultiLineStringOut = []
    ShortLineString = []
    
    if MulitLineStringIn.geom_type == 'LineString':
        return MulitLineStringIn, ShortLineString
    
    for ALineString in MulitLineStringIn:
        if ALineString.length > Threshold:
            MultiLineStringOut.append(ALineString)
        else:
            ShortLineString.append(ALineString)
    return MultiLineStringOut, ShortLineString


def PolyLineSplitByEdge(occlusion, edge_merge, edge_Overlap_Threshold):

    polyline_oc_out = []
    for polyline_i in occlusion:

        polyline_cuur = []
        isNeedSplit = False

        for index_i in range(len(polyline_i)-1):

            forward_line = [int(polyline_i[index_i].x), int(polyline_i[index_i].y), int(
                polyline_i[index_i+1].x), int(polyline_i[index_i+1].y)]
            discrete_line = list(
                zip(*line(forward_line[0], forward_line[1], forward_line[2], forward_line[3])))
            x = np.array(discrete_line)[:, 1]
            y = np.array(discrete_line)[:, 0]
            edge_overlap = 0

            for xi, yi in zip(x, y):
                # edge_overlap += np.sum(edge_merge[xi -
                #                        1:xi + 2, yi - 1:yi + 2])
                if xi >= 540:
                    xi = 539
                if yi >= 540:
                    yi = 539
                edge_overlap += np.sum(edge_merge[xi, yi])
            if len(x) <= 3:
                forward_overlap = 1
            else:
                forward_overlap = edge_overlap / len(x)

            if forward_overlap >= edge_Overlap_Threshold:
                polyline_cuur.extend([polyline_i[index_i]])
            else:
                isNeedSplit = True
                polyline_cuur.extend([polyline_i[index_i+1]])
                if len(polyline_cuur) >= 2:
                    polyline_oc_out.append(polyline_cuur)
                    polyline_cuur = []
                    isNeedSplit = False

        if isNeedSplit is False:
            polyline_cuur = []
            for index_i in range(len(polyline_i)):
                polyline_cuur.extend([polyline_i[index_i]])
            polyline_oc_out.append(polyline_cuur)

    return polyline_oc_out


def PolyLine2MulitLingString(polylineIN):

    LineStringList = []
    for A_PolyLine in polylineIN:
        polyline_curr = []
        for index_i in range(len(A_PolyLine)):

            polyline_curr.append(
                (A_PolyLine[index_i].x, A_PolyLine[index_i].y))

        LineString_curr = LineString(polyline_curr)
        LineStringList.append(LineString_curr)
    return MultiLineString(LineStringList)


def RemoveIsolateLineString(polyline_in, distanceThreshHoldD=2, length_Threshhold=4):

    polyline_out = []
    if isinstance(polyline_in,list) is False:
        return polyline_in
        
    for index_main in range(len(polyline_in)):
        mindistance = 1000
        for index_loop in range(len(polyline_in)):
            if index_main != index_loop:
                distance = polyline_in[index_main].distance(
                    polyline_in[index_loop])
                if distance < mindistance:
                    mindistance = distance
        if mindistance < distanceThreshHoldD or polyline_in[index_main].length > length_Threshhold:
            polyline_out.append(polyline_in[index_main])

    return polyline_out


def removeShortLinesString(polylines, threshold_length):

    outpolylines = []
    for polyline in polylines:
        if polyline.length >= threshold_length:
            outpolylines.append(polyline)
    return outpolylines
