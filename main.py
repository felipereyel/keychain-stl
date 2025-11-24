import trimesh
from fontTools.ttLib import TTFont
import numpy as np
import argparse
from trimesh.path import Path2D
from trimesh.path.entities import Line
import os


def text_to_stl(text_char, font_path, height, output_path, scale_factor=1.0):
    """
    Generates an extruded 3D STL mesh from a single character using trimesh
    and fontTools for font parsing.

    Args:
        text_char (str): The single character (e.g., 'A') to convert.
        font_path (str): The file path to the .ttf or .otf font file.
        height (float): The desired Z-axis extrusion height (thickness).
        output_path (str): The full path for the output STL file, including directory and filename.
        scale_factor (float): The factor by which to scale the character.
    """

    if len(text_char) != 1:
        print("Error: This function currently supports only single characters.")
        return

    try:
        # 1. Load the font file
        absolute_font_path = os.path.abspath(font_path)
        font = TTFont(absolute_font_path)

        # 2. Get the glyph object for the specified character
        # Convert character to its standard glyph name (e.g., 'A' -> 'uni0041')
        cmap = font.getBestCmap()
        glyph_name = cmap.get(ord(text_char))

        if not glyph_name:
            print(f"Error: Character '{text_char}' not found in the font map.")
            return

        glyph = font["glyf"][glyph_name]

        # 3. Extract the 2D path vertices and segments
        # FontTools provides the raw path data (vertices and curve definitions).
        end_points = glyph.endPtsOfContours

        # Simplified extraction logic: iterate through points, assume simple contours
        if end_points:
            # Reconstruct the 2D path. This is a simplification; complex glyphs
            # (like those with holes) require more detailed processing.
            path_points = list(zip(glyph.coordinates, glyph.flags))

            # Extract simple vertex coordinates from the raw path points
            points = np.array([p[0] for p in path_points], dtype=np.float64)

            # Check for non-empty points before proceeding
            if len(points) == 0:
                print(f"Error: Glyph for '{text_char}' has no points.")
                return

            # FontTools outputs points in font units, we need a 2D path entity
            # For simplicity, we assume one large polygon boundary here.

            # 4. Create a 2D Path in trimesh
            # This is where we create a polygon from the points
            # NOTE: For letters with holes (like 'O', 'P', 'D'), a more complex
            # path construction is needed to define inner and outer boundaries.

            # Create Line entities for the Path2D object
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

            # Apply the scaling factor
            path_2d.apply_scale(scale_factor)

        else:
            print(f"Error: Glyph for '{text_char}' has no contours to extract.")
            return

        # 5. Extrude the 2D Path into a 3D Mesh
        # Trimesh handles the triangulation and extrusion into a watertight solid.
        extruded = path_2d.extrude(height=height)
        if isinstance(extruded, list):
            combined_mesh = trimesh.util.concatenate(extruded)
        else:
            combined_mesh = extruded

        # 6. Save the resulting mesh to an STL file
        combined_mesh.export(output_path)
        print(f"Successfully generated and saved STL to {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    GENERATED_DIR = "generated"
    os.makedirs(GENERATED_DIR, exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Generate 3D STL models of all uppercase and lowercase characters from a font."
    )
    parser.add_argument(
        "--font",
        type=str,
        required=True,
        help="The file path to the .ttf or .otf font file.",
    )
    parser.add_argument(
        "--height",
        type=float,
        default=5.0,
        help="The desired Z-axis extrusion height (thickness).",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="The factor by which to scale the character.",
    )

    args = parser.parse_args()

    for char_code in range(ord("A"), ord("Z") + 1):
        char = chr(char_code)
        output_filename = os.path.join(GENERATED_DIR, f"upper_{char}.stl")
        text_to_stl(char, args.font, args.height, output_filename, args.scale)

    for char_code in range(ord("a"), ord("z") + 1):
        char = chr(char_code)
        output_filename = os.path.join(GENERATED_DIR, f"lower_{char}.stl")
        text_to_stl(char, args.font, args.height, output_filename, args.scale)
