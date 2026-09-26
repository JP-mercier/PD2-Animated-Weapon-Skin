"""Generate everything PAYDAY 2 loads from the sources in src/.

Sources:
    src/animated.txt       <material name> <scroll direction>, for every material that gets the animated glow
    src/static.xml         materials kept as they are (scope glass, red dots, ...), referenced by id
    src/parts.txt          <vanilla material config> <material group or -> <material>..., one line per weapon part
    src/glow_pattern.png   grayscale glow pattern, tinted with GLOW_COLOR

Outputs (committed so the repo installs straight from a ZIP; don't edit them by hand):
    assets/units/mods/inversion_universal/inversion_df.texture   base color
    assets/units/mods/inversion_universal/inversion_il.texture   glow
    assets/units/mods/inversion_universal/materials/*.material_config
    material_configs.txt   read by lua/inversion_universal.lua
    main.xml               BeardLib file registration

Usage (requires Pillow: pip install pillow):
    python tools/build.py
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

# ---- Colors -----------------------------------------------------------------------------------
GLOW_COLOR = "#12FF4D"   # color of the brightest parts of the pattern
GLOW_BRIGHTNESS = 0.8    # 1.0 = GLOW_COLOR as is, lower is darker
BASE_COLOR = "#000000"   # unlit surface under the glow

# ---- Animation and glow -----------------------------------------------------------------------
SCROLL_SPEED = 0.08      # UV units per second
GLOW_MULTIPLIER = 5      # in-game glow intensity (il_multiplier)
GLOW_BLOOM = 1.0         # il_bloom

# Scroll direction in UV space (u, v), scaled by SCROLL_SPEED.
DIRECTIONS = {
    "e": (1, 0), "w": (-1, 0), "n": (0, 1), "s": (0, -1),
    "ne": (0.7, 0.7), "nw": (-0.7, 0.7), "se": (0.7, -0.7), "sw": (-0.7, -0.7),
}
# -----------------------------------------------------------------------------------------------

NAMESPACE = "units/mods/inversion_universal"
DIFFUSE = f"{NAMESPACE}/inversion_df"
SELF_ILLUMINATION = f"{NAMESPACE}/inversion_il"
RENDER_TEMPLATE = "generic:DEPTH_SCALING:DIFFUSE_TEXTURE:DIFFUSE_UVANIM:SELF_ILLUMINATION:SELF_ILLUMINATION_BLOOM:SELF_ILLUMINATION_UVANIM"
BASE_SIZE = 32

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
ASSETS = ROOT / "assets"
MATERIALS = ASSETS / NAMESPACE / "materials"
TEXTURES = [DIFFUSE, SELF_ILLUMINATION]


def parse_color(value):
    hex_digits = value.lstrip("#")
    if len(hex_digits) != 6:
        raise ValueError(f"expected a color like #12FF4D, got {value!r}")
    return tuple(int(hex_digits[i:i + 2], 16) for i in (0, 2, 4))


def save_texture(image, path):
    # PAYDAY 2 textures are DDS files with a .texture extension. DXT5, no mipmaps, like the originals.
    image.convert("RGBA").save(ASSETS / f"{path}.texture", "DDS", pixel_format="DXT5")


def build_textures(glow_color, base_color):
    pattern = Image.open(SRC / "glow_pattern.png").convert("L")
    glow = Image.merge("RGB", [
        pattern.point(lambda v, c=channel: min(255, round(v * c / 255 * GLOW_BRIGHTNESS)))
        for channel in glow_color
    ])
    save_texture(glow, SELF_ILLUMINATION)
    save_texture(Image.new("RGB", (BASE_SIZE, BASE_SIZE), base_color), DIFFUSE)


def number(value):
    return f"{round(value, 6):g}"


def animated_material(name, direction):
    u, v = DIRECTIONS[direction]
    material = ET.Element("material", name=name, render_template=RENDER_TEMPLATE, version="2")
    ET.SubElement(material, "diffuse_texture", file=DIFFUSE)
    ET.SubElement(material, "self_illumination_texture", file=SELF_ILLUMINATION)
    ET.SubElement(material, "variable", name="uv_speed", value=f"{number(u * SCROLL_SPEED)} {number(v * SCROLL_SPEED)} 0", type="vector3")
    ET.SubElement(material, "variable", name="il_bloom", value=str(GLOW_BLOOM), type="float")
    ET.SubElement(material, "variable", name="il_multiplier", value=str(GLOW_MULTIPLIER), type="scalar")
    return material


def static_material(source):
    material = ET.Element("material", {k: v for k, v in source.attrib.items() if k != "id"})
    for child in source:
        material.append(ET.Element(child.tag, {k: DIFFUSE if v == "$diffuse" else v for k, v in child.attrib.items()}))
    return material


def read_lines(path):
    return [line.split() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")]


def main():
    errors = []

    animated = {}
    for fields in read_lines(SRC / "animated.txt"):
        name, direction = fields
        if direction not in DIRECTIONS:
            errors.append(f"animated.txt: {name}: unknown direction {direction!r}")
        animated[name] = direction

    static = {el.get("id"): el for el in ET.parse(SRC / "static.xml").getroot()}
    for ambiguous in sorted(static.keys() & animated.keys()):
        errors.append(f"{ambiguous!r} is both an animated name and a static id")

    parts = read_lines(SRC / "parts.txt")
    names = [fields[0].rsplit("/", 1)[1] for fields in parts]
    for duplicate in sorted({n for n in names if names.count(n) > 1}):
        errors.append(f"parts.txt: two parts would both write {duplicate}.material_config")
    for vanilla, _, *materials in parts:
        for ref in materials:
            if ref not in animated and ref not in static:
                errors.append(f"parts.txt: {vanilla}: unknown material {ref!r}")

    colors = {}
    for setting in ("GLOW_COLOR", "BASE_COLOR"):
        try:
            colors[setting] = parse_color(globals()[setting])
        except ValueError as e:
            errors.append(f"{setting}: {e}")

    if errors:
        sys.exit("\n".join(errors))

    build_textures(colors["GLOW_COLOR"], colors["BASE_COLOR"])

    MATERIALS.mkdir(parents=True, exist_ok=True)
    for old in MATERIALS.glob("*.material_config"):
        old.unlink()

    for name, (vanilla, group, *materials) in zip(names, parts):
        root = ET.Element("materials", version="3")
        if group != "-":
            root.set("group", group)
        for ref in materials:
            root.append(animated_material(ref, animated[ref]) if ref in animated else static_material(static[ref]))
        ET.indent(root, "\t")
        (MATERIALS / f"{name}.material_config").write_text(ET.tostring(root, encoding="unicode") + "\n", newline="\n")

    (ROOT / "material_configs.txt").write_text("".join(f"{fields[0]}\n" for fields in parts), newline="\n")

    lines = ['<table name="Inversion Universal">', '\t<AddFiles directory="assets">']
    lines += [f'\t\t<texture path="{tex}" force="true"/>' for tex in TEXTURES]
    lines += [f'\t\t<material_config path="{NAMESPACE}/materials/{name}"/>' for name in sorted(names)]
    lines += ["\t</AddFiles>", "</table>", ""]
    (ROOT / "main.xml").write_text("\n".join(lines), newline="\n")

    print(f"glow {GLOW_COLOR} x {GLOW_BRIGHTNESS}, base {BASE_COLOR}")
    print(f"{len(names)} material configs, {len(animated)} animated materials, {len(static)} static materials")


if __name__ == "__main__":
    main()
