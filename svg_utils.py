import math
import re
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from trimesh.path import Path2D
from trimesh.path.entities import Line, discretize_bezier


_CURVE_SAMPLES = 24


def parse_svg_path_d(d_string: str) -> list:
    """Parse SVG path ``d`` attribute into a list of (command, [params]) tuples."""
    tokens = re.findall(
        r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?",
        d_string,
    )
    commands = []
    i = 0
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            params: list[float] = []
            while i < len(tokens) and not tokens[i].isalpha():
                params.append(float(tokens[i]))
                i += 1
            commands.append((cmd, params))
    return commands


def _sample_svg_arc(
    x1: float, y1: float, rx: float, ry: float, phi_deg: float,
    large_arc: bool, sweep: bool, x2: float, y2: float,
    num_points: int = _CURVE_SAMPLES,
) -> list[tuple[float, float]]:
    """Convert an SVG elliptical arc to sampled line segments.

    Uses the endpoint→center parameterization from the SVG spec
    (https://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes).
    """
    if rx == 0 or ry == 0 or (x1 == x2 and y1 == y2):
        return [(x2, y2)]

    phi = math.radians(phi_deg)
    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)

    dx = (x1 - x2) / 2.0
    dy = (y1 - y2) / 2.0
    x1p = cos_phi * dx + sin_phi * dy
    y1p = -sin_phi * dx + cos_phi * dy

    rx = abs(rx)
    ry = abs(ry)

    # Correct radii if necessary (F.6.6.2)
    lambda_ = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lambda_ > 1.0:
        rx = math.sqrt(lambda_) * rx
        ry = math.sqrt(lambda_) * ry

    # Compute center in transformed space (F.6.5.2)
    numerator = max(
        0.0,
        rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p,
    )
    denominator = rx * rx * y1p * y1p + ry * ry * x1p * x1p

    if denominator == 0:
        return [(x2, y2)]

    factor = math.sqrt(numerator / denominator)
    if large_arc == sweep:
        factor = -factor

    cxp = factor * rx * y1p / ry
    cyp = factor * -ry * x1p / rx

    # Convert center to original space (F.6.5.3)
    cx = cos_phi * cxp - sin_phi * cyp + (x1 + x2) / 2.0
    cy = sin_phi * cxp + cos_phi * cyp + (y1 + y2) / 2.0

    # Compute start and sweep angles (F.6.5.4-6)
    start_angle = math.atan2(
        (y1p - cyp) / ry,
        (x1p - cxp) / rx,
    )
    end_angle = math.atan2(
        (-y1p - cyp) / ry,
        (-x1p - cxp) / rx,
    )

    sweep_angle = end_angle - start_angle
    if sweep and sweep_angle < 0:
        sweep_angle += 2 * math.pi
    elif not sweep and sweep_angle > 0:
        sweep_angle -= 2 * math.pi

    # Sample points along the arc
    num_points = max(2, num_points)
    pts = []
    for k in range(1, num_points - 1):
        t = start_angle + (k / (num_points - 1)) * sweep_angle
        xp = rx * math.cos(t)
        yp = ry * math.sin(t)
        pts.append((
            cos_phi * xp - sin_phi * yp + cx,
            sin_phi * xp + cos_phi * yp + cy,
        ))
    pts.append((x2, y2))
    return pts


def _sample_commands(commands: list) -> list[np.ndarray]:
    """Convert SVG path commands to a list of contour point arrays.

    Each contour is a ``(N, 2)`` float64 array.  Relative commands are
    converted to absolute.  Curves (C, Q, A) are sampled to line segments.
    """
    contours: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    cx, cy = 0.0, 0.0  # current absolute position
    scx, scy = 0.0, 0.0  # subpath start (for Z)

    def _abs(x, y, rel):
        return (cx + x, cy + y) if rel else (x, y)

    def _append(pt):
        nonlocal cx, cy
        current.append(pt)
        cx, cy = pt

    i = 0
    while i < len(commands):
        cmd, params = commands[i]
        rel = cmd.islower()
        cmd = cmd.upper()

        if cmd == "M":
            if current:
                contours.append(np.array(current, dtype=np.float64))
            current = []
            x, y = params[0], params[1]
            pt = _abs(x, y, rel)
            scx, scy = pt
            _append(pt)
            # implicit L for remaining params (polyline)
            for j in range(2, len(params), 2):
                pt = _abs(params[j], params[j + 1], rel)
                _append(pt)

        elif cmd == "Z":
            if current and (current[0][0] != cx or current[0][1] != cy):
                _append((scx, scy))
            contours.append(np.array(current, dtype=np.float64))
            current = []
            cx, cy = scx, scy

        elif cmd == "L":
            for j in range(0, len(params), 2):
                pt = _abs(params[j], params[j + 1], rel)
                _append(pt)

        elif cmd == "H":
            for v in params:
                x = cx + v if rel else v
                _append((x, cy))

        elif cmd == "V":
            for v in params:
                y = cy + v if rel else v
                _append((cx, y))

        elif cmd == "C":
            for j in range(0, len(params), 6):
                p1 = _abs(params[j], params[j + 1], rel)
                p2 = _abs(params[j + 2], params[j + 3], rel)
                pe = _abs(params[j + 4], params[j + 5], rel)
                pts = discretize_bezier(
                    np.array([(cx, cy), p1, p2, pe], dtype=np.float64),
                    count=_CURVE_SAMPLES,
                )
                for pt in pts[1:]:
                    _append((float(pt[0]), float(pt[1])))

        elif cmd == "S":
            for j in range(0, len(params), 4):
                # reflected control point
                if len(current) >= 2:
                    prev = current[-2]
                    rcx = 2 * cx - prev[0]
                    rcy = 2 * cy - prev[1]
                else:
                    rcx, rcy = cx, cy
                p2 = _abs(params[j], params[j + 1], rel)
                pe = _abs(params[j + 2], params[j + 3], rel)
                pts = discretize_bezier(
                    np.array([(cx, cy), (rcx, rcy), p2, pe], dtype=np.float64),
                    count=_CURVE_SAMPLES,
                )
                for pt in pts[1:]:
                    _append((float(pt[0]), float(pt[1])))

        elif cmd == "Q":
            for j in range(0, len(params), 4):
                p1 = _abs(params[j], params[j + 1], rel)
                pe = _abs(params[j + 2], params[j + 3], rel)
                # Quadratic → cubic bezier for discretize_bezier
                qpts = discretize_bezier(
                    np.array(
                        [
                            (cx, cy),
                            ((cx + 2 * p1[0]) / 3, (cy + 2 * p1[1]) / 3),
                            ((2 * p1[0] + pe[0]) / 3, (2 * p1[1] + pe[1]) / 3),
                            pe,
                        ],
                        dtype=np.float64,
                    ),
                    count=_CURVE_SAMPLES,
                )
                for pt in qpts[1:]:
                    _append((float(pt[0]), float(pt[1])))

        elif cmd == "T":
            for j in range(0, len(params), 2):
                # reflected control point from previous Q/T
                if len(current) >= 2:
                    prev = current[-2]
                    p1 = (2 * cx - prev[0], 2 * cy - prev[1])
                else:
                    p1 = (cx, cy)
                pe = _abs(params[j], params[j + 1], rel)
                qpts = discretize_bezier(
                    np.array(
                        [
                            (cx, cy),
                            ((cx + 2 * p1[0]) / 3, (cy + 2 * p1[1]) / 3),
                            ((2 * p1[0] + pe[0]) / 3, (2 * p1[1] + pe[1]) / 3),
                            pe,
                        ],
                        dtype=np.float64,
                    ),
                    count=_CURVE_SAMPLES,
                )
                for pt in qpts[1:]:
                    _append((float(pt[0]), float(pt[1])))

        elif cmd == "A":
            for j in range(0, len(params), 7):
                rx, ry, x_rot, large, sweep, xe, ye = params
                large = bool(large)
                sweep = bool(sweep)
                pe = _abs(xe, ye, rel)
                arc_pts = _sample_svg_arc(
                    cx, cy, rx, ry, x_rot, large, sweep, pe[0], pe[1]
                )
                for pt in arc_pts:
                    _append(pt)

        i += 1

    if current:
        contours.append(np.array(current, dtype=np.float64))

    return contours


def _parse_points_attr(el) -> np.ndarray | None:
    """Parse a ``points`` attribute (polygon/polyline) into a (N,2) array."""
    pts_str = el.get("points")
    if not pts_str:
        return None
    tokens = pts_str.strip().replace(",", " ").split()
    coords = [float(t) for t in tokens]
    pts = list(zip(coords[::2], coords[1::2]))
    if len(pts) < 3:
        return None
    return np.array(pts, dtype=np.float64)


def _rect_to_contours(el) -> list[np.ndarray]:
    x = float(el.get("x", 0))
    y = float(el.get("y", 0))
    w = float(el.get("width", 0))
    h = float(el.get("height", 0))
    rx_str = el.get("rx")
    ry_str = el.get("ry")

    if rx_str is None and ry_str is None:
        rx = ry = 0.0
    else:
        rx = float(rx_str) if rx_str is not None else float(ry_str or 0)
        ry = float(ry_str) if ry_str is not None else float(rx_str or 0)
        rx = max(0, min(rx, w / 2)) if w > 0 else 0
        ry = max(0, min(ry, h / 2)) if h > 0 else 0

    if w <= 0 or h <= 0:
        return []

    # Simple rectangle
    if rx <= 0 or ry <= 0:
        return [
            np.array(
                [[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.float64
            )
        ]

    # Rounded rectangle – build contour from straight segments + arc corners
    pts: list[tuple[float, float]] = [(x + rx, y), (x + w - rx, y)]

    # Top-right corner (clockwise sweep)
    arc = _sample_svg_arc(x + w - rx, y, rx, ry, 0, False, True, x + w, y + ry)
    pts.extend(arc)

    pts.append((x + w, y + h - ry))

    # Bottom-right corner
    arc = _sample_svg_arc(x + w, y + h - ry, rx, ry, 0, False, True, x + w - rx, y + h)
    pts.extend(arc)

    pts.append((x + rx, y + h))

    # Bottom-left corner
    arc = _sample_svg_arc(x + rx, y + h, rx, ry, 0, False, True, x, y + h - ry)
    pts.extend(arc)

    pts.append((x, y + ry))

    # Top-left corner
    arc = _sample_svg_arc(x, y + ry, rx, ry, 0, False, True, x + rx, y)
    pts.extend(arc)

    return [np.array(pts, dtype=np.float64)]


def _ellipse_to_contours(el) -> list[np.ndarray]:
    cx = float(el.get("cx", 0))
    cy = float(el.get("cy", 0))
    rx = float(el.get("rx", 0))
    ry = float(el.get("ry", 0))

    if rx <= 0 or ry <= 0:
        return []

    n = _CURVE_SAMPLES * 2
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return [np.array(pts, dtype=np.float64)]


def _circle_to_contours(el) -> list[np.ndarray]:
    r = float(el.get("r", 0))
    if r <= 0:
        return []
    # Reuse ellipse logic
    el.set("rx", str(r))
    el.set("ry", str(r))
    return _ellipse_to_contours(el)


def _contours_to_mesh(
    contours: list[np.ndarray],
    height: float,
    scale_factor: float = 1.0,
) -> trimesh.Trimesh:
    """Build a ``Path2D`` from contour arrays and extrude it."""
    paths = []
    for contour in contours:
        if len(contour) < 3:
            continue
        # Strip trailing duplicate-close point (some contours have it from Z)
        if len(contour) > 3 and np.array_equal(contour[0], contour[-1]):
            contour = contour[:-1]
            if len(contour) < 3:
                continue
        entities = []
        for k in range(len(contour) - 1):
            entities.append(Line([k, k + 1]))
        entities.append(Line([len(contour) - 1, 0]))
        paths.append(Path2D(entities=entities, vertices=contour))

    if not paths:
        raise ValueError("No valid contours (min 3 points)")

    path_2d = trimesh.path.util.concatenate(paths)
    path_2d.apply_scale(scale_factor)

    extruded = path_2d.extrude(height=height)
    return (
        trimesh.util.concatenate(extruded) if isinstance(extruded, list) else extruded
    )


def _shapely_to_contours(geom) -> list[np.ndarray]:
    """Convert a shapely geometry to contour arrays (exterior + holes)."""
    import shapely

    contours: list[np.ndarray] = []
    gid = shapely.get_type_id(geom)

    if gid == 3:  # Polygon
        contours.append(np.array(geom.exterior.coords, dtype=np.float64))
        for interior in geom.interiors:
            contours.append(np.array(interior.coords, dtype=np.float64))
    elif gid == 6:  # MultiPolygon
        for poly in geom.geoms:
            contours.extend(_shapely_to_contours(poly))
    elif gid == 7:  # GeometryCollection
        for g in geom.geoms:
            contours.extend(_shapely_to_contours(g))

    return contours


def _make_border_mesh(
    contours: list[np.ndarray],
    border_width: float,
    border_height: float,
    scale_factor: float = 1.0,
) -> trimesh.Trimesh | None:
    """Create a solid baseplate mesh from the buffered union of *contours*.

    The baseplate fills the entire buffered area (no inner hole) so the
    resulting mesh is a simple manifold without seam issues.
    """
    from shapely import Polygon, union_all

    polygons = [Polygon(c) for c in contours if len(c) >= 3]
    if not polygons:
        return None

    shape = union_all(polygons) if len(polygons) > 1 else polygons[0]
    expanded = shape.buffer(border_width, resolution=_CURVE_SAMPLES // 2)

    if expanded.is_empty:
        return None

    border_contours = _shapely_to_contours(expanded)
    return (
        _contours_to_mesh(border_contours, border_height, scale_factor)
        if border_contours
        else None
    )


def _extract_contours(root: ET.Element) -> list[np.ndarray]:
    """Extract all closed contour arrays from SVG elements under *root*."""
    ns = {"svg": "http://www.w3.org/2000/svg"}
    contours: list[np.ndarray] = []

    for local_tag in ("path", "rect", "circle", "ellipse", "polygon", "polyline"):
        elems = root.findall(f".//svg:{local_tag}", ns) + root.findall(
            f".//{local_tag}"
        )
        for el in elems:
            if local_tag == "path":
                d = el.get("d")
                if not d:
                    continue
                cmds = parse_svg_path_d(d)
                contours.extend(_sample_commands(cmds))
            elif local_tag == "rect":
                contours.extend(_rect_to_contours(el))
            elif local_tag == "circle":
                contours.extend(_circle_to_contours(el))
            elif local_tag == "ellipse":
                contours.extend(_ellipse_to_contours(el))
            elif local_tag in ("polygon", "polyline"):
                contour = _parse_points_attr(el)
                if contour is not None:
                    contours.append(contour)

    return contours


def svg_to_mesh(
    svg_path: str,
    height: float,
    scale_factor: float = 1.0,
    border_width: float = 0.0,
    border_height: float | None = None,
) -> trimesh.Trimesh:
    """Convert an SVG file to an extruded 3D mesh.

    Supports ``<path>``, ``<rect>``, ``<circle>``, ``<ellipse>``,
    ``<polygon>``, and ``<polyline>`` elements.

    When *border_width* > 0 a border ring is generated around the
    combined shape and extruded at *border_height* (defaults to
    ``height / 2``).  The border sits at z=0 alongside the main shape,
    creating a stepped outline.

    Args:
        svg_path: Path to the SVG file.
        height: Extrusion thickness (Z-axis) for the main shape.
        scale_factor: Uniform scale applied before extrusion.
        border_width: Offset distance for the outer border (0 = no border).
        border_height: Extrusion height for the border ring.  Defaults to
                       ``height / 2`` when *border_width* > 0.

    Returns:
        A closed ``trimesh.Trimesh`` ready for STL export.
    """
    tree = ET.parse(svg_path)
    root = tree.getroot()

    all_contours = _extract_contours(root)

    if not all_contours:
        raise ValueError(f"No drawable elements found in {svg_path}")

    meshes: list[trimesh.Trimesh] = []

    if border_width > 0:
        bh = height / 2 if border_height is None else border_height

        border = _make_border_mesh(all_contours, border_width, bh, scale_factor)
        if border is not None:
            meshes.append(border)

        inner_h = height - bh
        if inner_h > 0:
            inner = _contours_to_mesh(all_contours, inner_h, scale_factor)
            inner.apply_transform(
                trimesh.transformations.translation_matrix([0, 0, bh])
            )
            meshes.append(inner)
    else:
        meshes.append(_contours_to_mesh(all_contours, height, scale_factor))

    return trimesh.util.concatenate(meshes) if len(meshes) > 1 else meshes[0]
