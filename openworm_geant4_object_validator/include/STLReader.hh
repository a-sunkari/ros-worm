#pragma once
#include <string>
#include <vector>

struct Tri3 {
    double x0, y0, z0;
    double x1, y1, z1;
    double x2, y2, z2;
};

struct STLMesh {
    std::vector<Tri3> triangles;
    std::size_t raw_triangles = 0;
    std::size_t skipped_degenerate = 0;
};

STLMesh ReadBinarySTL(const std::string& path, double minArea2 = 0.0);
