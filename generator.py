import argparse
import os

from mesh_utils import char_to_mesh


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
        char_to_mesh(char, args.font, args.height, args.scale).export(output_filename)
        print(f"Successfully generated and saved STL to {output_filename}")

    for char_code in range(ord("a"), ord("z") + 1):
        char = chr(char_code)
        output_filename = os.path.join(GENERATED_DIR, f"lower_{char}.stl")
        char_to_mesh(char, args.font, args.height, args.scale).export(output_filename)
        print(f"Successfully generated and saved STL to {output_filename}")
