"""Generate the CatNapClub cap (red crown + brim + "M", white badge) as two OBJ files.

Run:  DigiPhantStarter/Tracking/.venv/bin/python StudentModels/make_cap.py [--preview DIR]
Writes Assets/StudentWork/Hat/CapRed.obj and CapWhite.obj. Units: crown base is 1.0 wide.
Axes (right-handed OBJ): +Y up, +Z = front of the cap (brim side). Unity's OBJ importer
mirrors X on import; the cap is symmetric, so nothing changes.
"""
import argparse
import math
from pathlib import Path

import numpy as np

A, B = .5, .56            # crown base half-width (x) and half-depth (z)
OFFSET_BADGE, OFFSET_LETTER = .012, .045  # letter clears the badge across its flat triangles


def crown_point(u, v):
    """Crown surface: u = angle around (0 = front), v = elevation (0 = base, pi/2 = top)."""
    front = (math.cos(u) + 1) / 2                      # 1 at the front, 0 at the back
    puff = 1 + .16 * math.sin(2 * v) * (.6 + .4 * (1 - front))  # bulges out above the band
    cv, sv = math.cos(v), math.sin(v)
    x = A * math.sin(u) * cv * puff
    z = B * math.cos(u) * cv * puff + .09 * sv
    # Height follows front-to-back position, so the top stays one smooth point:
    # tall front panel (badge), lower puffy back.
    height = .50 + .15 * z / B
    y = height * sv ** .8
    y -= .05 * math.exp(-(x / .12) ** 2) * sv ** 3 * max(0., -z / B)  # soft crease towards the back
    return np.array([x, y, z])


def crown_normal(u, v, eps=1e-4):
    du = crown_point(u + eps, v) - crown_point(u - eps, v)
    dv = crown_point(u, v + eps) - crown_point(u, v - eps)
    n = np.cross(du, dv)
    length = np.linalg.norm(n)
    if length < 1e-9:
        return np.array([0., 1., 0.])
    n /= length
    return n if np.dot(n, crown_point(u, v) - np.array([0, .2, 0])) > 0 else -n


class Part:
    def __init__(self):
        self.vertices, self.faces = [], []

    def add(self, points):
        start = len(self.vertices)
        self.vertices.extend(np.asarray(p, float) for p in points)
        return start

    def grid(self, rows, flip=False, wrap=False):
        """Triangles over a rows x cols grid of points, counter-clockwise facing outward."""
        rows = [list(r) for r in rows]
        cols = len(rows[0])
        start = self.add(p for r in rows for p in r)
        for i in range(len(rows) - 1):
            for j in range(cols - (0 if wrap else 1)):
                k = (j + 1) % cols
                a, b = start + i * cols + j, start + i * cols + k
                c, d = start + (i + 1) * cols + k, start + (i + 1) * cols + j
                for tri in ((a, b, c), (a, c, d)):
                    self.faces.append(tri[::-1] if flip else tri)

    def polygon(self, points, outline, flip=False):
        """Cap a 3D polygon using the triangles of its flat counter-clockwise outline."""
        start = self.add(points)
        for tri in triangulate(outline):
            tri = tuple(start + t for t in tri)
            self.faces.append(tri[::-1] if flip else tri)

    def normals(self):
        normals = np.zeros((len(self.vertices), 3))
        for a, b, c in self.faces:
            n = np.cross(self.vertices[b] - self.vertices[a], self.vertices[c] - self.vertices[a])
            for i in (a, b, c):
                normals[i] += n
        lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        return normals / np.where(lengths < 1e-12, 1, lengths)


def triangulate(polygon):
    """Ear clipping for a simple polygon given counter-clockwise."""
    index = list(range(len(polygon)))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    def inside(p, a, b, c):
        return cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0
    triangles = []
    while len(index) > 3:
        for k in range(len(index)):
            i, j, l = index[k - 1], index[k], index[(k + 1) % len(index)]
            a, b, c = polygon[i], polygon[j], polygon[l]
            if cross(a, b, c) <= 0:
                continue
            if any(inside(polygon[m], a, b, c) for m in index if m not in (i, j, l)):
                continue
            triangles.append((i, j, l))
            index.pop(k)
            break
        else:
            raise ValueError('polygon could not be triangulated')
    triangles.append(tuple(index))
    return triangles


def build():
    red, white = Part(), Part()
    us = np.linspace(0, 2 * math.pi, 72, endpoint=False)
    vs = np.linspace(0, math.pi / 2, 28)

    # Crown: outer shell, inner shell (seen from below), and the rim joining them.
    outer = [[crown_point(u, v) for u in us] for v in vs]
    inner = [[p * np.array([.95, .95, .95]) for p in row] for row in outer]
    red.grid(outer, wrap=True)
    red.grid(inner, flip=True, wrap=True)
    red.grid([inner[0], outer[0]], wrap=True)

    # Brim: a curved visor from the front of the crown band, drooping slightly.
    u_max = math.radians(78)
    ts = np.linspace(-1, 1, 41)
    ss = np.linspace(0, 1, 9)
    def brim_point(t, s, drop=0.):
        u = t * u_max
        base = np.array([A * math.sin(u), .02, B * math.cos(u)])
        reach = .42 * (1 - t * t) ** .6
        direction = np.array([.35 * math.sin(u), 0, math.cos(u)])
        direction /= np.linalg.norm(direction)
        p = base + direction * reach * s
        p[1] -= .07 * s * s + .03 * t * t * s + drop
        return p
    top = [[brim_point(t, s) for t in ts] for s in ss]
    bottom = [[brim_point(t, s, .028) for t in ts] for s in ss]
    red.grid(top, flip=True)
    red.grid(bottom)
    red.grid([top[-1], bottom[-1]], flip=True)

    # Badge and letter follow the crown's front panel.
    v0 = .62
    height_front = crown_point(0, math.pi / 2)[1]
    radius_front = np.linalg.norm(crown_point(0, v0)[[0, 2]])
    def on_crown(x, y, offset):
        u, v = x / radius_front, v0 + y / height_front
        return crown_point(u, v) + crown_normal(u, v) * offset

    ring = [(.20 * math.sin(a), .18 * math.cos(a)) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
    face = [on_crown(x, y, OFFSET_BADGE) for x, y in ring]
    centre = on_crown(0, 0, OFFSET_BADGE)
    start = white.add([centre] + face)
    for k in range(len(face)):
        white.faces.append((start, start + 1 + (k + 1) % len(face), start + 1 + k))
    white.grid([[on_crown(x, y, -.005) for x, y in ring], face], wrap=True, flip=True)

    # Blocky "M" (counter-clockwise outline, in badge units).
    outline = [(-.42, -.40), (-.27, -.40), (-.20, .06), (0, -.20), (.20, .06), (.27, -.40),
               (.42, -.40), (.32, .42), (.16, .42), (0, .15), (-.16, .42), (-.32, .42)]
    scale = .30
    # Outline x maps to -x on the cap, which mirrors it, so its faces are flipped to point out.
    front_pts = [on_crown(-x * scale, y * scale, OFFSET_LETTER) for x, y in outline]
    back_pts = [on_crown(-x * scale, y * scale, OFFSET_BADGE * .5) for x, y in outline]
    red.polygon(front_pts, outline, flip=True)
    red.grid([back_pts, front_pts], wrap=True, flip=True)
    return red, white


def write_obj(part, path, name):
    normals = part.normals()
    lines = [f'# CatNapClub cap: {name}. Generated by StudentModels/make_cap.py', f'o {name}']
    lines += [f'v {x:.6f} {y:.6f} {z:.6f}' for x, y, z in part.vertices]
    lines += [f'vn {x:.6f} {y:.6f} {z:.6f}' for x, y, z in normals]
    lines += [f'f {a + 1}//{a + 1} {b + 1}//{b + 1} {c + 1}//{c + 1}' for a, b, c in part.faces]
    path.write_text('\n'.join(lines) + '\n')


def preview(parts, folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    light = np.array([.4, .8, .6]) / np.linalg.norm([.4, .8, .6])
    folder.mkdir(parents=True, exist_ok=True)
    # Axes are (x, z, y): looking from +Y in matplotlib means looking at the cap's front.
    views = {'front': (12, 90), 'front-left': (20, 55), 'side': (6, 0), 'back': (25, -100), 'top': (75, 90)}
    for label, (elev, azim) in views.items():
        fig = plt.figure(figsize=(6, 5))
        ax = fig.add_subplot(projection='3d')
        # One collection, so matplotlib depth-sorts red and white triangles together.
        tris, shades = [], []
        for part, colour in parts:
            for f in part.faces:
                t = [part.vertices[i] for i in f]
                n = np.cross(t[1] - t[0], t[2] - t[0])
                n = n / (np.linalg.norm(n) or 1)
                shades.append(np.clip(np.array(colour) * (.35 + .65 * max(0, n @ light)), 0, 1))
                tris.append([(p[0], p[2], p[1]) for p in t])  # matplotlib's z is up
        ax.add_collection3d(Poly3DCollection(tris, facecolors=shades, linewidths=0))
        ax.set_xlim(-.6, .6); ax.set_ylim(-.6, 1.0); ax.set_zlim(-.2, .8)
        ax.set_box_aspect((1.2, 1.6, 1.0))
        ax.view_init(elev, azim)
        ax.set_axis_off()
        fig.savefig(folder / f'cap-{label}.png', dpi=110, bbox_inches='tight')
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    red, white = build()
    out = Path(__file__).resolve().parent.parent / 'Assets/StudentWork/Hat'
    out.mkdir(parents=True, exist_ok=True)
    write_obj(red, out / 'CapRed.obj', 'CapRed')
    write_obj(white, out / 'CapWhite.obj', 'CapWhite')
    print(f'CapRed: {len(red.vertices)} vertices, {len(red.faces)} triangles')
    print(f'CapWhite: {len(white.vertices)} vertices, {len(white.faces)} triangles')
    if args.preview:
        preview([(red, (.85, .08, .08)), (white, (.95, .95, .95))], args.preview)


if __name__ == '__main__':
    main()
