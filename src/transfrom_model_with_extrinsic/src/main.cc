#include <Eigen/Core>
#include <Eigen/Dense>
#include <strstream>
#include <set>
#include <unordered_set>
#include <chrono>

// #include "arrangement.h"
#include "camera.h"
#include "mesh.h"


int main (int argc, char** argv)
{
	Mesh mesh;
	Camera camera;
	mesh.LoadFromFile(argv[1]);
	camera.LoadFromFile(argv[2]);
	camera.ApplyExtrinsic(mesh);

	const char* filename = argv[3];
	mesh.SaveOBJ(filename, camera, false);

	return 0;
}
