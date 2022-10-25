#! /bin/bash

DATASETPATH="/media/helab/EXTERNAL_USB/dataset/GeometricStructureSemanticUnderstandingDataset/demodata/3d_future/"
OBJFILENAME="normalized_model.obj"
TEXTUREFILENAME="texture.png"
OUTROOT="/media/helab/EXTERNAL_USB/dataset/GeometricStructureSemanticUnderstandingDataset/demodata/Rendered/"

for dir in /media/helab/EXTERNAL_USB/dataset/GeometricStructureSemanticUnderstandingDataset/demodata/3d_future/*/
do
    OBJFILE="$dir$OBJFILENAME"
    TEXTUREFILE="$dir$TEXTUREFILENAME"
    CuurOBJFileDir=$(basename $dir) 
    OUTPUTDIR=$OUTROOT$CuurOBJFileDir
    
    if [ -d "$OUTPUTDIR" ];then
        echo "remove old"
        rm -r "$OUTPUTDIR"
    else
	echo "-----------------------"
    fi
    blender --background --python render_model.py -- --output_folder "$OUTPUTDIR" --model_file "$OBJFILE" --texture_file "$TEXTUREFILE"

done
