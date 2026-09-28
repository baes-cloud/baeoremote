# BæoRemote

A B&O Essence–inspired Sonos controller for a 480×480 round ESP32-S3 knob display
(ST7701S RGB panel, CST816 touch, rotary encoder), running ESPHome 2026.9 + LVGL 9.

## Faces
- **Face A**: gold radial face with an etched Manrope clock, title and artist and a Syne BÆOREMOTE wordmark ([spec](docs/BaeoRemote%20Face%20A%20Spec.pdf)).
- **Nocturne**: smoked glass over a blurred album cover, with a lit volume ring.
- **Night face**: after 3 minutes idle, a dim amber clock on near-black, with the backlight at *Night Brightness*.

Swipe left or right to toggle faces. When Club is on the TV input, the display shows the Plex / Google TV title and poster.

## Controls
| Input | Action |
|---|---|
| Turn | Volume (hold + turn = scrub) |
| Press / double / triple | Play-pause / next / previous |
| Hold | Playlists: Disco, House, MOS, PDM, DFP, **Favourites** (all Sonos favourites), **Albums** (Music Assistant favourites), Ungroup all rooms |

The work-alarm popup comes from the base config and is unchanged.

## Layout
- `rotary-display-1.yaml`: the original device config. It provides the display/SPI setup, alarm popup, numbers and base settings.
- `tt/body.yaml`, `tt/tail.yaml`: the BæoRemote scripts, fonts, sensors and LVGL pages.
- `tt/assemble.py`: splices the two together into `rotary-display-1.new.yaml`, which is generated and git-ignored.
- `ha/rotary_lists.yaml`: the Home Assistant package behind the Favourites / Albums lists (`sensor.rotary_lists` + `script.rotary_play_list`). Add it under `homeassistant: packages:`.
- `docs/`: design spec.

## Build
```bash
cp secrets.example.yaml secrets.yaml   # fill in
python tt/assemble.py
esphome compile rotary-display-1.new.yaml
esphome upload rotary-display-1.new.yaml --device <ip>
```
Deploying to Home Assistant's ESPHome add-on means copying `rotary-display-1.new.yaml` to `/config/esphome/rotary-display-1.yaml`. The add-on's `secrets.yaml` needs the same keys.
