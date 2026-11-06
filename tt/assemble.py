import math, json, sys

# One source, two remotes. Identity comes from the device's own base yaml
# conventions; everything else is shared.
DEVICES = {
    '1': dict(name='rotary-display-1', ap='Rotary-Display-1', addr='10.0.1.122', sec='rotary',
              player='media_player.club', room='CLUB', group_vol='true', has_tv='true', pick_more='true'),
    '2': dict(name='rotary-display-2', ap='Rotary-Display-Bedroom', addr='10.0.1.50', sec='rotary2',
              player='media_player.bedroom_sonos', room='BEDROOM', group_vol='false', has_tv='false', pick_more='false'),
}
old = open('rotary-display-1.yaml').read().split('\n')
def idx(pred, start=0):
    for i in range(start, len(old)):
        if pred(old[i]): return i
    raise SystemExit('marker not found')
L = lambda a, b: '\n'.join(old[a:b])
head = L(0, idx(lambda s: s.startswith('image:')))
assert '\nlogger:\n' in head
head = head.replace('\nlogger:\n', '\nlogger:\n  hardware_uart: UART0\n', 1)
OLD_BOOT = '''  on_boot:
    priority: 800
    then:
      - output.turn_on: lcd_power
      - output.turn_on: display_reset
      - delay: 100ms
      - output.turn_off: display_reset
      - delay: 500ms
'''
assert OLD_BOOT in head
head = head.replace(OLD_BOOT, '''  on_boot:
    - priority: 800
      then:
        - output.turn_on: lcd_power
        - output.turn_on: display_reset
        - delay: 100ms
        - output.turn_off: display_reset
        - delay: 500ms
    # after LVGL is up: paint the face canvases
    - priority: -100
      then:
        - script.execute: paint_vignette
        - script.execute: paint_faces
        - script.execute: {id: paint_bg, live: false}
        - script.execute: apply_offset
        - script.execute: set_face
''')
HEAD = head
a = idx(lambda s: 'WORK ALARM POPUP' in s); b = idx(lambda s: '# --- SCREEN TIMEOUT ---' in s, a)
alarm_scripts = L(a, b)
# BÆOSOUND wordmark: BÆO in Syne Bold, SOUND in Syne Regular (its lightest), one tracked line
def wordmark(y, color, opa='100%', indent='            '):
    lab = lambda txt, f: '{text: "' + txt + '", text_font: ' + f + ', text_letter_space: 7, text_color: ' + color + ', text_opa: ' + opa + '}'
    return (f"{indent}- obj:\n"
            f"{indent}    align: CENTER\n{indent}    y: {y}\n{indent}    width: SIZE_CONTENT\n{indent}    height: SIZE_CONTENT\n"
            f"{indent}    bg_opa: 0\n{indent}    border_width: 0\n{indent}    pad_all: 0\n{indent}    clickable: false\n{indent}    scrollable: false\n"
            f"{indent}    layout: {{type: flex, flex_flow: ROW, flex_align_cross: END, pad_column: 7}}\n"
            f"{indent}    widgets:\n"
            f"{indent}      - label: " + lab('BÆO', 'hk_22') + "\n"
            f"{indent}      - label: " + lab('SOUND', 'hk_22l'))
a = idx(lambda s: s.startswith('  top_layer:')); b = idx(lambda s: s.startswith('  displays:'), a)
top_layer = L(a, b)
# the night clock becomes the Face A night face: dim amber on near-black
k = top_layer.index('          id: grp_night'); k = top_layer.rindex('\n      - obj:\n', 0, k) + 1
AMB1, AMB2 = '0xB8704A', '0xA56444'
top_layer = top_layer[:k] + f"""      - obj:
          id: grp_night
          hidden: true
          align: center
          width: 480
          height: 480
          bg_color: 0x000000
          bg_opa: COVER
          border_width: 0
          radius: 0
          pad_all: 0
          scrollable: false
          scrollbar_mode: "OFF"
          widgets:
            - canvas: {{id: nt_cv, align: TOP_LEFT, x: 0, y: 0, width: 480, height: 480}}
            - label: {{id: nt_title, text: "", align: CENTER, y: -112, width: 320, height: 28, long_mode: DOT, text_align: CENTER, text_font: mr_20, text_color: {AMB2}}}
            - label: {{id: nt_artist, text: "", align: CENTER, y: -86, width: 300, height: 20, long_mode: DOT, text_align: CENTER, text_font: mr_a14, text_letter_space: 3, text_color: {AMB2}}}
            - label: {{id: night_clock_lbl, text: "--:--", align: CENTER, y: 0, text_font: mr_num, text_color: {AMB1}}}
"""
top_layer += '\n' + wordmark(120, AMB2)
a = idx(lambda s: s.startswith('spi:')); b = idx(lambda s: s.startswith('font:'), a)
display = L(a, b)
a = idx(lambda s: s.startswith('text_sensor:')) + 1
b = idx(lambda s: s.strip() == 'id: media_title', a) - 1
alarm_ts = L(a, b)
number = L(idx(lambda s: s.startswith('number:')), len(old))
number = number.replace('number:\n', '''number:
  - platform: template
    id: screen_offset_y
    name: "Screen offset Y"
    icon: "mdi:arrow-up-down"
    entity_category: config
    mode: box
    min_value: -12
    max_value: 12
    step: 1
    initial_value: 4
    optimistic: true
    restore_value: true
    unit_of_measurement: "px"
    on_value:
      then: [{script.execute: apply_offset}]
''', 1)

# pick-to-play: three little LPs (vinyl drawn with LVGL shapes, cover art as the label)
def lp(pid, x, d, sc, opa, which, shadow):
    I = '                    '
    rings = [d - 10 - 12 * k for k in range(8) if d - 10 - 12 * k > d * 0.6]
    out = [f"{I}- obj:", f"{I}    id: {pid}", f"{I}    align: CENTER", f"{I}    x: {x}", f"{I}    y: 4",
           f"{I}    width: {d}", f"{I}    height: {d}", f"{I}    radius: {d // 2}", f"{I}    bg_color: 0x0B0B0C",
           f"{I}    bg_opa: COVER", f"{I}    border_width: 1", f"{I}    border_color: 0x34343A", f"{I}    pad_all: 0",
           f"{I}    scrollable: false", f"{I}    opa: {opa}"]
    if shadow:
        out += [f"{I}    shadow_width: 34", f"{I}    shadow_color: 0x000000", f"{I}    shadow_opa: 55%", f"{I}    shadow_ofs_y: 6"]
    out += [f"{I}    on_click: [{{script.execute: {{id: pick_tap, which: {which}}}}}]", f"{I}    widgets:"]
    for r in rings:
        out.append(f"{I}      - obj: {{align: CENTER, width: {r}, height: {r}, radius: {r // 2}, bg_opa: 0, border_width: 1, border_color: 0xFFFFFF, border_opa: 7%, pad_all: 0, clickable: false, scrollable: false}}")
    w = int(d * 0.16)
    for a0 in (205, 25):   # soft sheen across the grooves
        out.append(f"{I}      - arc: {{align: CENTER, width: {d - 8}, height: {d - 8}, start_angle: {a0}, end_angle: {a0 + 40}, value: 0, adjustable: false, clickable: false, arc_width: {w}, arc_color: 0xFFFFFF, arc_opa: 6%, arc_rounded: false, indicator: {{arc_opa: 0}}, knob: {{bg_opa: 0}}}}")
    out.append(f"{I}      - image: {{id: {pid}_cv, src: cv_pdm_london, align: CENTER, scale: {sc}, clickable: false}}")
    h = max(4, int(d * 0.035)) // 2 * 2
    out.append(f"{I}      - obj: {{align: CENTER, width: {h}, height: {h}, radius: {h // 2}, bg_color: 0x0B0B0C, border_width: 1, border_color: 0x55555C, pad_all: 0, clickable: false}}")
    return '\n'.join(out)

PICKER = '\n'.join([
    '              - obj:', '                  id: pk_grp', '                  hidden: true', '                  align: CENTER',
    '                  width: 480', '                  height: 480', '                  bg_opa: 0', '                  border_width: 0',
    '                  pad_all: 0', '                  scrollable: false', '                  clickable: false', '                  widgets:',
    lp('pk_l', -152, 108, 0.58, '45%', -1, False), lp('pk_r', 152, 108, 0.58, '45%', 1, False),
    lp('pk_c', 0, 176, 1.0, '100%', 0, True)])

faces = f"""        # ── BÆO III · Nocturne
        - obj:
            id: grp_noc
            hidden: true
            align: CENTER
            width: 480
            height: 480
            radius: 0
            bg_color: 0x050506
            bg_opa: COVER
            border_width: 0
            pad_all: 0
            scrollable: false
            scrollbar_mode: "OFF"
            widgets:
              - canvas: {{id: noc_bg, align: TOP_LEFT, x: 0, y: 0, width: 480, height: 480, image_opa: 70%}}
              - canvas: {{id: noc_vig, align: TOP_LEFT, x: 0, y: 0, width: 480, height: 480, transparent: true}}
              - arc: {{id: noc_glow, align: CENTER, width: 462, height: 462, rotation: 270, start_angle: 0, end_angle: 360, min_value: 0, max_value: 100, value: 30, adjustable: false, clickable: false, arc_width: 12, arc_opa: 0, indicator: {{arc_width: 12, arc_color: 0xE9EDF2, arc_opa: 14%, arc_rounded: true}}, knob: {{bg_opa: 0}}}}
              - arc: {{id: noc_ring, align: CENTER, width: 462, height: 462, rotation: 270, start_angle: 0, end_angle: 360, min_value: 0, max_value: 100, value: 30, adjustable: false, clickable: false, arc_width: 2, arc_color: 0xFFFFFF, arc_opa: 12%, indicator: {{arc_width: 2, arc_color: 0xF2F4F7, arc_rounded: true}}, knob: {{bg_opa: 0}}}}
              # track progress: a faint hairline just inside the glass, hidden for radio / TV
              - arc: {{id: noc_prog, hidden: true, align: CENTER, width: 432, height: 432, rotation: 270, start_angle: 0, end_angle: 360, min_value: 0, max_value: 1000, value: 0, adjustable: false, clickable: false, arc_width: 1, arc_color: 0xFFFFFF, arc_opa: 6%, indicator: {{arc_width: 1, arc_color: 0xE9EDF2, arc_opa: 38%, arc_rounded: false}}, knob: {{bg_opa: 0}}}}
              - label: {{id: noc_clk, text: "--:--", align: TOP_MID, y: 70, text_font: hk_clock, text_letter_space: 3, text_color: 0xE9EDF2, text_opa: 75%}}
              - label: {{id: noc_room, text: "", align: TOP_MID, y: 124, width: 300, long_mode: DOT, text_align: CENTER, text_font: hk_16, text_letter_space: 4, text_color: 0xE9EDF2, text_opa: 45%}}
              - obj:
                  align: CENTER
                  y: 0
                  width: 350
                  height: SIZE_CONTENT
                  bg_opa: 0
                  border_width: 0
                  pad_all: 0
                  clickable: false
                  scrollable: false
                  layout: {{type: flex, flex_flow: COLUMN, flex_align_main: CENTER, flex_align_cross: CENTER, flex_align_track: CENTER, pad_row: 6}}
                  widgets:
                    - label: {{id: noc_title, text: "", width: 350, long_mode: WRAP, text_align: CENTER, text_font: hk_32, text_color: 0xF6F6F4}}
                    - label: {{id: noc_artist, text: "", width: 320, long_mode: DOT, text_align: CENTER, text_font: hk_16, text_letter_space: 4, text_color: 0xE9EDF2, text_opa: 75%}}
              - label: {{id: noc_num, hidden: true, text: "", align: CENTER, text_font: mr_num, text_color: 0xF6F6F4}}
"""
faces += '\n' + PICKER
faces += '\n' + wordmark(122, '0xE9EDF2', '70%', '              ')
caps = ''.join(dict.fromkeys(" +ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789·:-'&.,!?()/" + "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝàáâãäåæçèéêëìíîïñòóôõöøùúûüýÿßŒœ’…"))
latin = ''.join(chr(c) for c in range(0x20, 0x7f)) + 'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝàáâãäåæçèéêëìíîïñòóôõöøùúûüýÿßŒœ‘’“”–—·…'
latin_y = json.dumps(latin, ensure_ascii=False)

def build(key):
    d = DEVICES[key]
    head = HEAD
    for old_s, new_s in [('friendly_name: rotary-display-1', 'friendly_name: ' + d['name']),
                         ('  name: rotary-display-1', '  name: ' + d['name']),
                         ('ssid: "Rotary-Display-1"', 'ssid: "%s"' % d['ap']),
                         ('use_address: 10.0.1.122', 'use_address: ' + d['addr']),
                         ('!secret rotary_api_key', '!secret %s_api_key' % d['sec']),
                         ('!secret rotary_ota_password', '!secret %s_ota_password' % d['sec']),
                         ('!secret rotary_ap_password', '!secret %s_ap_password' % d['sec'])]:
        assert old_s in head, old_s
        head = head.replace(old_s, new_s)
    head = head.replace('substitutions:\n', 'substitutions:\n' + ''.join(
        '  %s: "%s"\n' % (k, d[v]) for k, v in [('player', 'player'), ('room_name', 'room'),
                                              ('group_vol', 'group_vol'), ('has_tv', 'has_tv'), ('pick_more', 'pick_more')]), 1)
    body = open('tt/body.yaml').read().replace('@@ALARM_SCRIPTS@@', alarm_scripts)
    tail = (open('tt/tail.yaml').read().replace('@@FACES@@', faces).replace('@@CAPS@@', json.dumps(caps, ensure_ascii=False))
            .replace('@@LATIN@@', latin_y).replace('@@ALARM_TEXT_SENSORS@@', alarm_ts).replace('@@TOP_LAYER@@', top_layer))
    out = head + '\n' + body + '\n' + display + '\n' + tail + '\n' + number + '\n'
    assert '@@' not in out, [l for l in out.split('\n') if '@@' in l]
    fn = d['name'] + '.new.yaml'
    open(fn, 'w').write(out)
    print(fn, len(out.split('\n')), 'lines')

for key in (sys.argv[1:] or sorted(DEVICES)):
    build(key)
