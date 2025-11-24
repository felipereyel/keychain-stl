import argparse
import os
import trimesh
from typing import List

from mesh_utils import char_to_mesh


def name_to_stl(
    name: str,
    font_path: str,
    height: float,
    scale_factor: float,
    spacing: float,
) -> trimesh.Trimesh:
    """
    Generates a single combined mesh for a given name.

    Args:
        name (str): The name or word to generate.
        font_path (str): The file path to the .ttf or .otf font file.
        height (float): The desired Z-axis extrusion height (thickness).
        scale_factor (float): The factor by which to scale the characters.
        spacing (float): The spacing between characters, as a fraction of the character width.

    Returns:
        trimesh.Trimesh: The combined 3D mesh object of the name, or None if generation fails.
    """
    meshes: List[trimesh.Trimesh] = []
    x_offset: float = 0.0

    for char in name:
        mesh = char_to_mesh(char, font_path, height, scale_factor)

        # Get the character width to determine the offset for the next character
        char_width = mesh.bounds[1, 0] - mesh.bounds[0, 0]

        # Translate the mesh to its correct position
        translation_matrix = trimesh.transformations.translation_matrix(
            [x_offset, 0, 0]
        )
        mesh.apply_transform(translation_matrix)

        meshes.append(mesh)

        # Update the x-offset for the next character
        x_offset += char_width + (char_width * spacing)

    if not meshes:
        print("Error: No valid meshes were generated. Cannot create STL file.")
        raise ValueError("No valid meshes generated.")

    # Combine all character meshes into a single mesh
    return trimesh.util.concatenate(meshes)


if __name__ == "__main__":
    GENERATED_DIR: str = "generated"
    os.makedirs(GENERATED_DIR, exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Generate a single 3D STL model for a given name."
    )

    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="The name or word to generate.",
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
        default=0.03,
        help="The factor by which to scale the characters.",
    )
    parser.add_argument(
        "--spacing",
        type=float,
        default=-0.1,
        help="The spacing between characters, as a fraction of the character width.",
    )

    args: argparse.Namespace = parser.parse_args()

    output_filename = f"{args.name}.stl"
    output_path = os.path.join(GENERATED_DIR, output_filename)

    name_to_stl(args.name, args.font, args.height, args.scale, args.spacing).export(
        output_path
    )

    print(f"Successfully generated and saved STL to {output_path}")
