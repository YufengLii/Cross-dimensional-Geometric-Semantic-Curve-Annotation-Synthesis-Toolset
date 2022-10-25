#include <iostream>
#include "camera.h"
#include "mesh.h"
#include <set>
#include <vector>




int main (int argc, char** argv)
{
	Mesh mesh;
	Camera camera;
	mesh.LoadFromFile(argv[1]);
	camera.LoadFromFile(argv[2]);
	camera.ApplyExtrinsic(mesh);

    char* filename = "./transformed.obj";
    mesh.SaveOBJ(filename, camera, false);

    return 0;

}
