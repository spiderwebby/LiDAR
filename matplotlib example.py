import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

xs = np.linspace(0, 10, 100)
zs = np.linspace(0, 10, 100)

X, Z = np.meshgrid(xs, zs)
Y = 5 - X


np.random.seed(19680801)


def randrange(n, vmin, vmax):
    """
    Helper function to make an array of random numbers having shape (n, )
    with each number distributed Uniform(vmin, vmax).
    """
    return (vmax - vmin)*np.random.rand(n) + vmin




x = [5,7,8,7,2,17,2,9,4,11,12,9,6]
y = [99,86,87,88,111,86,103,87,94,78,77,85,86]
z = [199,6,847,8,-11,16,103,57,-94,78,77,85,86]


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
# ax.plot_surface(X, Y, Z)
ax.plot(x, y, z, linestyle='None')
xs = 0
ys = 0
zs = 0

for n, m, zlow, zhigh in [(1, 'o', -50, -25), (12, '^', -30, -5)]:
    xs = x
    ys = y
    zs = z
    ax.scatter(xs, ys, zs, marker='o')

ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_zlabel('Z Label')

plt.show()