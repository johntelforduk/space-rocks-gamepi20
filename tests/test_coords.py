# Test the triangle functions.

import cartesian_coordinates as cc

#         v2(10, 30)
#             / \
#            /   \
#           /     \
#          /   t1  \     t2
#         /         \
# v1(0, 0) ---------- v3(20, 0)

print('Should be true', cc.is_inside_triangle([10, 15], [0, 0], [10, 30], [20, 0]))
print('Should be false', cc.is_inside_triangle([25, 15], [0, 0], [10, 30], [20, 0]))
