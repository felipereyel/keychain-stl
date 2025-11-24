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

To generate STL files for all uppercase and lowercase characters from a font, run the `generator.py` script with the following arguments:

```bash
uv run generator.py --font <path_to_font_file> --height <extrusion_height> --scale <scale_factor>
```

**Arguments:**
*   `--font`: The file path to the .ttf or .otf font file (e.g., `fonts/pacifico.ttf`). (Required)
*   `--height`: The desired Z-axis extrusion height (thickness) in millimeters. (Default: 5.0)
*   `--scale`: The factor by which to scale the character. (Default: 1.0)

**Example:**

```bash
uv run generator.py --font fonts/pacifico.ttf --height 10 --scale 1.0
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
*   `--spacing`: The spacing between characters, as a fraction of the character width. (Default: 0.1)
*   `--stagger`: The amount to add to the height of even-indexed characters. (Default: 0.0)

**Example:**

```bash
uv run name_generator.py --name Gemini --font fonts/pacifico.ttf --height 10 --scale 1.0 --spacing 0.1 --stagger 5.0
```

This will generate `Gemini.stl` in the `generated/` directory.