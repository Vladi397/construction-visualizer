"""Plane geometry helpers shared by the build script.

The same maths runs in the browser (see index.html), so a quad measured here
gives the same aspect ratio there.
"""
import numpy as np


def square_to_quad(q):
    """Homography that maps the unit square (0,0),(1,0),(1,1),(0,1) onto quad q (TL, TR, BR, BL)."""
    src = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float64)
    dst = np.array(q, dtype=np.float64)
    A, b = [], []
    for (u, v), (x, y) in zip(src, dst):
        A.append([u, v, 1, 0, 0, 0, -u * x, -v * x]); b.append(x)
        A.append([0, 0, 0, u, v, 1, -u * y, -v * y]); b.append(y)
    h = np.linalg.solve(np.array(A), np.array(b))
    return np.append(h, 1).reshape(3, 3)


def default_focal(w, h):
    """Typical phone main camera (about 26 mm equivalent): f is roughly 0.6 x image diagonal."""
    return 0.6 * float(np.hypot(w, h))


def rect_aspect(q, w, h, f=None):
    """Real width/height ratio of the rectangle seen as quad q, assuming a pinhole camera.

    Columns h1, h2 of the square-to-quad homography are K*r1*W and K*r2*H (up to scale),
    and r1, r2 are unit vectors, so W/H = |K^-1 h1| / |K^-1 h2|.
    """
    f = f or default_focal(w, h)
    H = square_to_quad(q)
    Kinv = np.linalg.inv(np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]]))
    a = Kinv @ H[:, 0]
    b = Kinv @ H[:, 1]
    return float(np.linalg.norm(a) / np.linalg.norm(b))


def focal_from_orthogonality(q, w, h):
    """Estimate f from r1 . r2 = 0. Unstable for near-frontal quads, so only used as a check."""
    H = square_to_quad(q)
    cx, cy = w / 2, h / 2
    x1, y1, z1 = H[:, 0]
    x2, y2, z2 = H[:, 1]
    num = (x1 - cx * z1) * (x2 - cx * z2) + (y1 - cy * z1) * (y2 - cy * z2)
    if abs(z1 * z2) < 1e-12:
        return None
    f2 = -num / (z1 * z2)
    return float(np.sqrt(f2)) if f2 > 0 else None
