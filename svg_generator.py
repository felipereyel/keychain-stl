import argparse
import os

from svg_utils import svg_to_mesh


if __name__ == "__main__":
    os.makedirs("generated", exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Generate a 3D STL model from an SVG file."
    )
    parser.add_argument(
        "--svg",
        type=str,
        required=True,
        help="The file path to the SVG file.",
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
        help="The factor by which to scale the SVG.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Output filename (saved in generated/). "
            "Defaults to the SVG filename with .stl extension."
        ),
    )
    parser.add_argument(
        "--border-width",
        type=float,
        default=0.0,
        help="Width of the border ring around the shape (0 = no border).",
    )
    parser.add_argument(
        "--border-height",
        type=float,
        default=None,
        help=(
            "Extrusion height of the border ring. "
            "Defaults to half of --height."
        ),
    )

    args = parser.parse_args()

    output = args.output or os.path.splitext(os.path.basename(args.svg))[0] + ".stl"
    output_path = os.path.join("generated", output)

    svg_to_mesh(
        args.svg,
        args.height,
        args.scale,
        border_width=args.border_width,
        border_height=args.border_height,
    ).export(output_path)
    print(f"Successfully generated and saved STL to {output_path}")
