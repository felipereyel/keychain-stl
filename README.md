# keychain-stl

generate STL files to 3d print keychain with your name

## Fonts

Download fonts [here](https://gwfh.mranftl.com/fonts/oi?subsets=latin) and save into fonts folder 

```
    curl https://gwfh.mranftl.com/api/fonts/oi?download=zip&subsets=latin&variants=regular&formats=ttf -o fonts/oi.zip
    unzip fonts/oi.zip -d fonts/oi/
```

## Usage

To generate STL files for all uppercase and lowercase characters from a font, run the `generator.py` script with the following arguments:

```bash
uv run generator.py --font <path_to_font_file> --height <extrusion_height> --scale <scale_factor>
```

**Arguments:**
*   `--font`: The file path to the .ttf or .otf font file (e.g., `fonts/pacifico/pacifico-v23-latin-regular.ttf`). (Required)
*   `--height`: The desired Z-axis extrusion height (thickness) in millimeters. (Default: 5.0)
*   `--scale`: The factor by which to scale the character. (Default: 1.0)

**Example:**

```bash
uv run generator.py --font fonts/pacifico/pacifico-v23-latin-regular.ttf --height 10 --scale 1.0
```

This will generate `upper_A.stl` through `lower_z.stl` in the `generated/` directory.