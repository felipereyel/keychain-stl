# keychain-stl

generate STL files to 3d print keychain with your name

## Fonts

To add a new font from [Google Fonts](https://fonts.google.com/), use the `make add-font` command with the font's slug.

```bash
make add-font slug=<font-slug>
```

**Example:**

To add the "Pacifico" font, find its slug on Google Fonts (it's `pacifico` in `https://fonts.google.com/specimen/Pacifico`) and run:

```bash
make add-font slug=pacifico
```

This will download the font, extract the `.ttf` file, rename it to `pacifico.ttf`, and move it to the `fonts/` directory.

## Usage

To generate STL files for all uppercase and lowercase characters from a font, run the `letters_generator.py` script with the following arguments:

```bash
uv run letters_generator.py --font <path_to_font_file> --height <extrusion_height> --scale <scale_factor>
```

**Arguments:**
*   `--font`: The file path to the .ttf or .otf font file (e.g., `fonts/pacifico.ttf`). (Required)
*   `--height`: The desired Z-axis extrusion height (thickness) in millimeters. (Default: 5.0)
*   `--scale`: The factor by which to scale the character. (Default: 1.0)

**Example:**

```bash
uv run letters_generator.py --font fonts/pacifico.ttf --height 10 --scale 1.0
```

This will generate `upper_A.stl` through `lower_z.stl` in the `generated/` directory.

## Name Generation

To generate a single STL file for a given name, run the `name_generator.py` script with the following arguments:

```bash
uv run name_generator.py --name <name> --font <path_to_font_file> --height <extrusion_height> --scale <scale_factor> --spacing <spacing> --stagger <stagger>
```

**Arguments:**
*   `--name`: The name or word to generate. (Required)
*   `--font`: The file path to the .ttf or .otf font file. (Required)
*   `--height`: The desired Z-axis extrusion height (thickness) in millimeters. (Default: 5.0)
*   `--scale`: The factor by which to scale the characters. (Default: 1.0)
*   `--spacing`: The spacing between characters, as a fraction of the character width. (Default: -0.1)
*   `--stagger`: The amount to add to the height of even-indexed characters. (Default: 0.0)

**Example:**

```bash
uv run name_generator.py --name Gemini --font fonts/pacifico.ttf --height 10 --scale 1.0 --spacing 0.1 --stagger 5.0
```

This will generate `Gemini.stl` in the `generated/` directory.

## SVG Generation

To generate an STL file from an SVG file, run the `svg_generator.py` script:

```bash
uv run svg_generator.py --svg <path_to_svg> --height <extrusion_height> --scale <scale_factor> --output <output_filename>
```

**Arguments:**
*   `--svg`: The file path to the SVG file. (Required)
*   `--height`: The desired Z-axis extrusion height (thickness) in millimeters. (Default: 5.0)
*   `--scale`: The factor by which to scale the SVG. (Default: 1.0)
*   `--output`: Output filename (saved in `generated/`). Defaults to the SVG filename with `.stl` extension.
*   `--border-width`: Width of the border (baseplate) around the shape in SVG units. (Default: 0.0)
*   `--border-height`: Extrusion height of the border. Defaults to half of `--height`.

When `--border-width > 0`, the output is a stepped two-layer model:
- A **baseplate** at half height that extends `border-width` beyond the shape
- The **main shape** rises from the baseplate to the full height

> **Note:** The baseplate fills any interior holes in the SVG (e.g., the counter of a letter "A" or "O"). Without a border, those holes remain open as through-holes.

**Examples:**

```bash
# Generate from alien.svg, scale up 10x
uv run svg_generator.py --svg alien.svg --scale 10

# Custom height and output name
uv run svg_generator.py --svg alien.svg --height 3 --scale 8 --output keychain.stl

# With a 3mm border at default half-height
uv run svg_generator.py --svg alien.svg --scale 10 --border-width 3

# With a 3mm border at custom 2mm height
uv run svg_generator.py --svg alien.svg --scale 10 --border-width 3 --border-height 2
```

**Supported SVG elements:** `<path>`, `<rect>`, `<circle>`, `<ellipse>`, `<polygon>`, `<polyline>`

**Path commands:** `M`/`m`, `L`/`l`, `H`/`h`, `V`/`v`, `C`/`c`, `S`/`s`, `Q`/`q`, `T`/`t`, `A`/`a`, `Z`/`z`

Curves (beziers and arcs) are automatically sampled to line segments during extrusion.