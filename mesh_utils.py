import trimesh
from fontTools.ttLib import TTFont
import numpy as np
from trimesh.path import Path2D
from trimesh.path.entities import Line
import os


def char_to_mesh(
    text_char: str, font_path: str, height: float, scale_factor: float = 1.0
) -> trimesh.Trimesh:
    """
    Generates an extruded 3D STL mesh from a single character using trimesh
    and fontTools for font parsing.

    Args:
        text_char (str): The single character (e.g., 'A') to convert.
        font_path (str): The file path to the .ttf or .otf font file.
        height (float): The desired Z-axis extrusion height (thickness).
        scale_factor (float): The factor by which to scale the character.

    Returns:
        trimesh.Trimesh: The 3D mesh object of the character.
    """

    if len(text_char) != 1:
        print("Error: This function currently supports only single characters.")
        raise ValueError("Input must be a single character.")

    # 1. Load the font file
    absolute_font_path = os.path.abspath(font_path)
    font = TTFont(absolute_font_path)

    # 2. Get the glyph object for the specified character
    cmap = font.getBestCmap()
    glyph_name = cmap.get(ord(text_char))

    if not glyph_name:
        print(f"Error: Character '{text_char}' not found in the font map.")
        raise ValueError(f"Character '{text_char}' not found in font.")

    glyph = font["glyf"][glyph_name]

    # 3. Extract the 2D path vertices and segments
    end_points = glyph.endPtsOfContours

    if not end_points:
        print(f"Error: Glyph for '{text_char}' has no contours to extract.")
        raise ValueError(f"Glyph for '{text_char}' has no contours.")

    path_points = list(zip(glyph.coordinates, glyph.flags))
    points = np.array([p[0] for p in path_points], dtype=np.float64)

    if len(points) == 0:
        print(f"Error: Glyph for '{text_char}' has no points.")
        raise ValueError(f"Glyph for '{text_char}' has no points.")

    # 4. Create a 2D Path in trimesh
    start_point = 0
    paths = []
    for end_point in end_points:
        contour_points = points[start_point : end_point + 1]
        entities = []
        for i in range(len(contour_points) - 1):
            entities.append(Line([i, i + 1]))
        # Close the loop
        if len(contour_points) > 1:
            entities.append(Line([len(contour_points) - 1, 0]))

        paths.append(Path2D(entities=entities, vertices=contour_points))
        start_point = end_point + 1

    path_2d = trimesh.path.util.concatenate(paths)
    path_2d.apply_scale(scale_factor)

    # 5. Extrude the 2D Path into a 3D Mesh
    extruded = path_2d.extrude(height=height)

    return (
        trimesh.util.concatenate(extruded) if isinstance(extruded, list) else extruded
    )
