import math, json
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
a = idx(lambda s: 'WORK ALARM POPUP' in s); b = idx(lambda s: '# --- SCREEN TIMEOUT ---' in s, a)
alarm_scripts = L(a, b)
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
            - label: {{text: "BÆOREMOTE", align: CENTER, y: 120, text_font: hk_22, text_letter_space: 7, text_color: {AMB2}}}"""
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

ROOMS = ["media_player.club", "media_player.living_room_sonos", "media_player.office_sonos",
         "media_player.bathroom_sonos", "media_player.bedroom_sonos"]
arr = '{' + ', '.join('"%s"' % r for r in ROOMS) + '}'
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
              - label: {{id: noc_clk, text: "--:--", align: TOP_MID, y: 70, text_font: hk_clock, text_letter_space: 3, text_color: 0xE9EDF2, text_opa: 75%}}
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
              - label: {{text: "BÆOREMOTE", align: CENTER, y: 122, text_font: hk_22, text_letter_space: 7, text_color: 0xE9EDF2, text_opa: 70%}}"""
caps = ''.join(dict.fromkeys(" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789·:-'&.,!?()/" + "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝàáâãäåæçèéêëìíîïñòóôõöøùúûüýÿßŒœ’…"))
latin = ''.join(chr(c) for c in range(0x20, 0x7f)) + 'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝàáâãäåæçèéêëìíîïñòóôõöøùúûüýÿßŒœ‘’“”–—·…'
latin_y = json.dumps(latin, ensure_ascii=False)

body = open('tt/body.yaml').read()
tail = open('tt/tail.yaml').read()
body = (body.replace('@@ALARM_SCRIPTS@@', alarm_scripts)
            .replace('@@ROOM_ENTS_ARR@@', arr))
tail = (tail.replace('@@FACES@@', faces).replace('@@CAPS@@', json.dumps(caps, ensure_ascii=False)).replace('@@LATIN@@', latin_y).replace('@@ALARM_TEXT_SENSORS@@', alarm_ts)
            .replace('@@ROOM_ENTS_ARR@@', arr).replace('@@TOP_LAYER@@', top_layer))
out = head + '\n' + body + '\n' + display + '\n' + tail + '\n' + number + '\n'
assert '@@' not in out, [l for l in out.split('\n') if '@@' in l]
open('rotary-display-1.new.yaml', 'w').write(out)
print(len(out.split('\n')), 'lines')
