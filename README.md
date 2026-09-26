# Inversion Universal

Animated inversion-style glow for every weapon in PAYDAY 2, applied to the local player's first-person weapons only.

Made by [Siuna](https://steamcommunity.com/profiles/76561199075375622).

<img width="2560" height="1440" alt="Inversion Universal" src="https://github.com/user-attachments/assets/7fee8cf0-5bf1-4aa8-861a-a3f1956cf0c7" />

https://github.com/user-attachments/assets/19883a24-2f3f-43f6-8b1d-69ca8cdbf6f4

The preview shows the 1.0 pink. The default glow is now dark green (`#12FF4D` at 0.8 brightness), and the color can be changed in `tools/build.py` (see [Customization](#customization)).

## Requirements

- [SuperBLT](https://superblt.znix.xyz/)
- [BeardLib](https://modworkshop.net/mod/14924)

## Installation

1. Download the repository (Code → Download ZIP).
2. Extract it to `PAYDAY 2/mods/`. The folder name does not matter.

This is a BLT mod, not a `mod_overrides` pack. If you have version 1.x installed, delete `PAYDAY 2/assets/mod_overrides/Inversion Universal` first.

## Scope

| Applied | Not applied |
| --- | --- |
| Your own weapons, first person | Teammates, bots, enemies, lobby characters |
| Every vanilla weapon part (1,766 material configs) | Melee weapons and throwables |
|  | Custom weapons added by other mods |
|  | VR |

An equipped weapon skin is replaced by the effect. The animated material has no cosmetic layers for the skin to render onto.

## How it works

Weapon parts in PAYDAY 2 have several material config variants, and the game picks one by context:

| Variant | Used for |
| --- | --- |
| `<unit>` | First person, no skin |
| `<unit>_cc` | First person, with a skin |
| `<unit>_thq` / `<unit>_cc_thq` | Third person (other players, bots) |

The animated material uses the `DEPTH_SCALING` render flag. This flag is meant for first-person viewmodels: it compresses the depth range so the weapon does not clip into walls. On a third-person weapon, the same compression makes the model render on top of the world.

Version 1.x overrode all four variants of every part through `mod_overrides`. As a result the effect appeared on every weapon in the game, and third-person weapons were visible through walls.

Version 2 overrides no game files. The animated material configs are registered under their own path (`units/mods/inversion_universal/materials/`) through BeardLib. A post-hook on `NewRaycastWeaponBase:_update_materials` then swaps them onto the parts of weapons where `is_npc()` is false, which means the local player's weapons only. Each part is looked up by the Idstring of its vanilla material config (`part_data.material_config`, falling back to `part_data.unit`). This matches how the game resolves it, including parts that point at another part's config. The hook also clears the weapon's cosmetic material list, so the skin system does not try to paint the animated materials.

## Repository layout

```
mod.txt                          BLT manifest, registers the Lua hook
main.xml                         BeardLib file registration          (generated)
material_configs.txt             vanilla configs that are replaced   (generated)
lua/inversion_universal.lua      material swap hook
assets/units/mods/inversion_universal/
    inversion_df.texture         base color                          (generated)
    inversion_il.texture         glow                                (generated)
    materials/*.material_config  one per weapon part                 (generated)
src/
    animated.txt                 animated material names and scroll direction
    static.xml                   non-animated materials (scope glass, reticles, ...)
    parts.txt                    per part: vanilla config path, material group, material list
    glow_pattern.png             grayscale glow pattern, tinted with GLOW_COLOR
tools/build.py                   generates the textures, materials/, main.xml and material_configs.txt
```

The generated files are committed so the mod can be installed directly from the ZIP. Do not edit them by hand. They are overwritten on every build.

## Building

Requires Python 3.10 or newer and Pillow.

```
pip install pillow
python tools/build.py
```

The script validates the sources before writing anything. It fails on unknown material references, unknown scroll directions, invalid colors, output filename collisions, and names defined as both animated and static.

## Customization

Global settings are at the top of `tools/build.py`:

| Setting | Default | Effect |
| --- | --- | --- |
| `GLOW_COLOR` | `#12FF4D` | Color of the brightest parts of the glow pattern |
| `GLOW_BRIGHTNESS` | `0.8` | Multiplier on `GLOW_COLOR`. `1.0` uses the color as is |
| `BASE_COLOR` | `#000000` | Unlit surface color under the glow |
| `SCROLL_SPEED` | `0.08` | UV units per second |
| `GLOW_MULTIPLIER` | `5` | `il_multiplier`, in-game glow intensity |
| `GLOW_BLOOM` | `1.0` | `il_bloom` |

The glow texture is `src/glow_pattern.png` multiplied by `GLOW_COLOR` and `GLOW_BRIGHTNESS`. To use a different pattern, replace that file with any grayscale image whose width and height are powers of two. White areas take the full glow color and black areas stay dark. The closest match to the original 1.0 pink is `GLOW_COLOR = "#FF24BD"` with `GLOW_BRIGHTNESS = 1.0`.

Per-material scroll direction is set in `src/animated.txt`. The eight directions (`n`, `ne`, `e`, `se`, `s`, `sw`, `w`, `nw`) are defined in `DIRECTIONS` in `tools/build.py`.

To cover a new weapon part, add a line to `src/parts.txt`. Add any new material names to `src/animated.txt` or `src/static.xml`, then rebuild.

## Changelog

### 2.1
- Glow color, glow brightness and base color are settings in `tools/build.py` (`GLOW_COLOR`, `GLOW_BRIGHTNESS`, `BASE_COLOR`). The build generates both textures from `src/glow_pattern.png`.
- Default glow changed from pink to dark green.
- The build now requires Pillow.

### 2.0
- Moved from `mod_overrides` to a BLT/BeardLib mod. No game files are overridden.
- The effect is limited to the local player's first-person weapons.
- Fixed third-person weapons rendering through walls.
- Removed the duplicated `_cc` / `_thq` / `_cc_thq` variants and the 175 non-weapon material configs (melee, throwables, poses, obsolete paths). 7,769 files reduced to 1,766.
- Materials are generated from `src/` by `tools/build.py`.

### 1.0
- Initial release.
