#!/usr/bin/env python3
"""build_theremin.py - build the upgraded Spatial Theremin M4L device (.amxd) with 8-note tactile ladder and bulletproof Hold & Mode state engine."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M4L_COMMON = os.path.join(HERE, "..", "finishing-kit", "m4l")
if M4L_COMMON not in sys.path:
    sys.path.insert(0, M4L_COMMON)

import amxd

USER_LIBRARY_MIDI = "/Volumes/Libraries/MY_MUSIC/_ABLETON/User Library/Presets/MIDI Effects/Max MIDI Effect"

def box(id_, maxclass, rect, **kw):
    b = {"id": id_, "maxclass": maxclass, "patching_rect": rect}
    b.update(kw)
    return {"box": b}

def newobj(id_, text, rect, inlets=1, outlets=1, outlettype=None, **kw):
    if outlettype is None:
        outlettype = [""]
    return box(id_, "newobj", rect, text=text, numinlets=inlets, numoutlets=outlets, outlettype=outlettype, **kw)

def message(id_, text, rect, inlets=2, outlets=1, **kw):
    return box(id_, "message", rect, text=text, numinlets=inlets, numoutlets=outlets, outlettype=[""], **kw)

def live_dial(id_, name, rect, pres, lo=0.0, hi=1.0, init=0.5, unitstyle=1, shortname=None):
    if shortname is None:
        shortname = name
    valueof = {
        "parameter_longname": name,
        "parameter_shortname": shortname,
        "parameter_type": 0,
        "parameter_mmin": lo,
        "parameter_mmax": hi,
        "parameter_initial": [init],
        "parameter_initial_enable": 1,
        "parameter_unitstyle": unitstyle,
        "parameter_speedlim": 0.0
    }
    return box(id_, "live.dial", rect, numinlets=1, numoutlets=2, outlettype=["", "float"],
               parameter_enable=1, varname=name, presentation=1, presentation_rect=pres,
               saved_attribute_attributes={"valueof": valueof})

def live_pct_dial(id_, name, rect, pres, init=0.0):
    valueof = {
        "parameter_longname": name,
        "parameter_shortname": name.split()[-1],
        "parameter_type": 0,
        "parameter_mmin": 0.0,
        "parameter_mmax": 100.0,
        "parameter_initial": [init],
        "parameter_initial_enable": 1,
        "parameter_unitstyle": 5, # %
        "parameter_speedlim": 0.0
    }
    return box(id_, "live.dial", rect, numinlets=1, numoutlets=2, outlettype=["", "float"],
               parameter_enable=1, varname=name, presentation=1, presentation_rect=pres,
               saved_attribute_attributes={"valueof": valueof})

def live_toggle_btn(id_, name, text_off, text_on, rect, pres, shortname="Map"):
    valueof = {
        "parameter_longname": name,
        "parameter_shortname": shortname,
        "parameter_type": 2,
        "parameter_mmax": 1.0,
        "parameter_enum": ["off", "on"]
    }
    return box(id_, "live.text", rect, numinlets=1, numoutlets=2, outlettype=["", "float"],
               parameter_enable=1, varname=name, presentation=1, presentation_rect=pres,
               text=text_off, texton=text_on, mode=1,
               saved_attribute_attributes={"valueof": valueof})

def live_unmap_btn(id_, name, rect, pres):
    valueof = {
        "parameter_longname": name,
        "parameter_shortname": "✕",
        "parameter_type": 2,
        "parameter_mmax": 1.0,
        "parameter_enum": ["off", "on"]
    }
    return box(id_, "live.text", rect, numinlets=1, numoutlets=2, outlettype=["", "float"],
               parameter_enable=1, varname=name, presentation=1, presentation_rect=pres,
               text="✕", texton="✕", mode=0,
               saved_attribute_attributes={"valueof": valueof})

def live_menu(id_, name, rect, pres, items, init=0):
    valueof = {
        "parameter_longname": name,
        "parameter_shortname": name,
        "parameter_type": 2,
        "parameter_mmax": float(len(items) - 1),
        "parameter_enum": items,
        "parameter_initial": [init],
        "parameter_initial_enable": 1
    }
    return box(id_, "live.menu", rect, numinlets=1, numoutlets=3, outlettype=["", "", ""],
               parameter_enable=1, varname=name, presentation=1, presentation_rect=pres,
               saved_attribute_attributes={"valueof": valueof})

def live_button(id_, name, rect, pres):
    valueof = {
        "parameter_longname": name,
        "parameter_shortname": name,
        "parameter_type": 2,
        "parameter_mmax": 1.0,
        "parameter_enum": ["off", "on"]
    }
    return box(id_, "live.text", rect, numinlets=1, numoutlets=2, outlettype=["", "float"],
               parameter_enable=1, varname=name, presentation=1, presentation_rect=pres,
               text=name, texton=name, mode=0,
               saved_attribute_attributes={"valueof": valueof})

def comment(id_, text, rect, pres=None, fontsize=10.0, fontface=0):
    kw = {"fontsize": fontsize, "fontface": fontface}
    if pres:
        kw.update({"presentation": 1, "presentation_rect": pres})
    return box(id_, "comment", rect, text=text, numinlets=1, numoutlets=0, **kw)

def build_device():
    with open(os.path.join(M4L_COMMON, "spike_a_trim.json")) as f:
        p = json.load(f)

    pt = p["patcher"]
    pt["rect"] = [100.0, 100.0, 1250.0, 850.0]
    pt["openrect"] = [0.0, 0.0, 815.0, 135.0]
    pt["devicewidth"] = 815.0
    pt["description"] = "Spatial Theremin - Tactile 8-Note Instrument with Multi-Mapping & True Note Hold"

    # Confident 8-Note Scales (1 to 1.5 octave tactile span)
    SCALES = [
        "0 3 5 7 10 12 15 17",  # Min Pent
        "0 2 4 7 9 12 14 16",   # Maj Pent
        "0 2 3 7 8 12 14 15",   # Hirajoshi
        "0 2 3 5 7 9 10 12",    # Dorian
        "0 3 5 6 7 10 12 15",   # Blues
        "0 2 4 6 8 10 12 14"    # Whole Tone
    ]
    SCALE_NAMES = ["Min Pent", "Maj Pent", "Hirajoshi", "Dorian", "Blues", "Whole Tone"]
    ROOT_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

    boxes = [
        # MIDI Pass-through
        newobj("obj-1", "midiin", [30.0, 30.0, 48.0, 20.0], inlets=0, outlets=1, outlettype=["int"]),
        newobj("obj-2", "midiout", [30.0, 720.0, 56.0, 20.0], inlets=1, outlets=0, outlettype=[]),

        # UDP Receive on port 8765
        newobj("obj-3", "udpreceive 8765", [200.0, 30.0, 115.0, 20.0], inlets=1, outlets=1, outlettype=[""]),

        # Route OSC: Pitch (Y), Trigger, Velocity, Cutoff (X), Set Scale, Set Root, Set Octave, Set Hold, Gate, Mode
        newobj("obj-4", "route /theremin/pitch /theremin/trigger /theremin/velocity /theremin/cutoff /theremin/set_scale /theremin/set_root /theremin/set_octave /theremin/set_hold /theremin/gate /theremin/mode",
               [200.0, 70.0, 600.0, 20.0], inlets=1, outlets=11, outlettype=[""] * 11),

        # Initialization
        newobj("obj-8", "loadbang", [50.0, 110.0, 55.0, 20.0], inlets=0, outlets=1, outlettype=["bang"]),
        newobj("obj-9", "live.thisdevice", [50.0, 140.0, 85.0, 20.0], inlets=1, outlets=2, outlettype=["bang", ""]),

        # Scale Selection Engine
        live_menu("obj-10", "Scale", [50.0, 180.0, 90.0, 18.0], pres=[8.0, 36.0, 84.0, 18.0], items=SCALE_NAMES, init=0),
        newobj("obj-11", "sel 0 1 2 3 4 5", [50.0, 220.0, 110.0, 20.0], inlets=1, outlets=7, outlettype=["bang", "bang", "bang", "bang", "bang", "bang", ""]),
        message("obj-12", SCALES[0], [50.0, 260.0, 160.0, 20.0]),
        message("obj-13", SCALES[1], [50.0, 285.0, 160.0, 20.0]),
        message("obj-14", SCALES[2], [50.0, 310.0, 160.0, 20.0]),
        message("obj-15", SCALES[3], [50.0, 335.0, 160.0, 20.0]),
        message("obj-16", SCALES[4], [50.0, 360.0, 160.0, 20.0]),
        message("obj-17", SCALES[5], [50.0, 385.0, 160.0, 20.0]),

        # Root Key Selector (0..11 semitone offset)
        live_menu("obj-18", "Root", [150.0, 180.0, 50.0, 18.0], pres=[96.0, 36.0, 44.0, 18.0], items=ROOT_NAMES, init=0),

        # OSC Feedback to Web HUD (:8001)
        message("obj-61", "/theremin/scale $1", [50.0, 580.0, 115.0, 20.0]),
        message("obj-62", "/theremin/root $1", [50.0, 610.0, 110.0, 20.0]),
        newobj("obj-65", "i", [50.0, 635.0, 30.0, 20.0], inlets=2, outlets=1, outlettype=["int"]),
        message("obj-64", "/theremin/octave $1", [50.0, 660.0, 120.0, 20.0]),
        message("obj-66", "/theremin/hold $1", [50.0, 685.0, 110.0, 20.0]),
        newobj("obj-63", "udpsend 127.0.0.1 8001", [50.0, 710.0, 130.0, 20.0], inlets=1, outlets=0, outlettype=[]),

        # 1. Pitch Quantization: scale 0..1 to index 0..7 (8 notes) -> zl.lookup
        newobj("obj-20", "scale 0. 1. 0. 7.999", [200.0, 110.0, 115.0, 20.0], inlets=5, outlets=1, outlettype=["float"]),
        newobj("obj-21", "i", [200.0, 140.0, 30.0, 20.0], inlets=2, outlets=1, outlettype=["int"]),
        newobj("obj-21_clip", "clip 0 7", [200.0, 165.0, 50.0, 20.0], inlets=3, outlets=1, outlettype=["int"]),
        newobj("obj-22", "zl.lookup", [200.0, 420.0, 65.0, 20.0], inlets=2, outlets=2, outlettype=["", ""]),

        # Transposition Chain: zl.lookup -> + 36 (base C2, centered on 3rd octave) -> + Root -> + (Octave * 12)
        newobj("obj-23", "+ 36", [200.0, 460.0, 40.0, 20.0], inlets=2, outlets=1, outlettype=["int"]),
        newobj("obj-24", "+ 0", [200.0, 490.0, 35.0, 20.0], inlets=2, outlets=1, outlettype=["int"]),
        newobj("obj-25", "+ 0", [200.0, 520.0, 35.0, 20.0], inlets=2, outlets=1, outlettype=["int"]),
        newobj("obj-26", "* 12", [260.0, 490.0, 38.0, 20.0], inlets=2, outlets=1, outlettype=["int"]),

        # Pitch & Velocity Storage (cold inlets update without firing)
        newobj("obj-27", "i 48", [200.0, 560.0, 40.0, 20.0], inlets=2, outlets=1, outlettype=["int"]),
        newobj("obj-28", "i 95", [280.0, 560.0, 40.0, 20.0], inlets=2, outlets=1, outlettype=["int"]),

        # 2. Trigger Logic
        newobj("obj-29", "sel 1", [285.0, 110.0, 40.0, 20.0], inlets=2, outlets=2, outlettype=["bang", ""]),

        # 3. Centralized Bulletproof Hold & Mode Manager
        live_toggle_btn("obj-75", "Hold", "Hold", "HOLD", [300.0, 140.0, 45.0, 20.0], pres=[186.0, 86.0, 46.0, 26.0], shortname="Hold"),
        message("obj-75_set", "set $1", [300.0, 165.0, 45.0, 20.0]), # visual update without firing outlet
        newobj("obj-73", "t i i", [350.0, 140.0, 40.0, 20.0], inlets=1, outlets=2, outlettype=["int", "int"]), # router for set_hold from UI
        newobj("obj-74", "t i i", [350.0, 165.0, 40.0, 20.0], inlets=1, outlets=2, outlettype=["int", "int"]), # router for hold from device
        newobj("obj-90", "t i b", [250.0, 110.0, 35.0, 20.0], inlets=1, outlets=2, outlettype=["int", "bang"]), # router for mode
        newobj("obj-91", "t i i i i", [300.0, 195.0, 65.0, 20.0], inlets=1, outlets=4, outlettype=["int", "int", "int", "int"]), # central hold dispatcher

        newobj("obj-76", "i 1", [250.0, 140.0, 30.0, 20.0], inlets=2, outlets=1, outlettype=["int"]), # Mode storage: 1=Theremin, 0=Pinch
        newobj("obj-77", "expr ($i1 == 1) && ($i2 == 0)", [250.0, 175.0, 170.0, 20.0], inlets=2, outlets=1, outlettype=["int"]), # 1 if Theremin decay mode
        newobj("obj-78", "gate 1 1", [250.0, 205.0, 60.0, 20.0], inlets=2, outlets=1, outlettype=[""]), # Gate for delay scheduling
        newobj("obj-79", "delay 350", [250.0, 235.0, 65.0, 20.0], inlets=2, outlets=1, outlettype=["bang"]),
        message("obj-80", "stop", [320.0, 235.0, 35.0, 20.0]),
        newobj("obj-81", "sel 0", [380.0, 140.0, 40.0, 20.0], inlets=2, outlets=2, outlettype=["bang", ""]), # pinch release gate==0
        newobj("obj-82", "== 0", [380.0, 175.0, 35.0, 20.0], inlets=2, outlets=1, outlettype=["int"]), # Hold OFF check for pinch release
        newobj("obj-83", "gate 1 1", [380.0, 205.0, 60.0, 20.0], inlets=2, outlets=1, outlettype=[""]), # Pinch release cutoff gate
        newobj("obj-84", "sel 0", [300.0, 230.0, 40.0, 20.0], inlets=2, outlets=2, outlettype=["bang", ""]), # Cutoff when Hold turned OFF

        # Note Generation & Active Sounding Pitch Engine
        newobj("obj-85", "i 0", [200.0, 300.0, 40.0, 20.0], inlets=2, outlets=1, outlettype=["int"]), # Active sounding pitch storage (0=silence)
        newobj("obj-85_check", "sel 0", [200.0, 325.0, 50.0, 20.0], inlets=1, outlets=2, outlettype=["bang", ""]), # Drop 0 silence, pass non-zero pitch
        newobj("obj-85_reset", "t i b", [200.0, 350.0, 45.0, 20.0], inlets=1, outlets=2, outlettype=["int", "bang"]), # Cut note and reset buffer to 0
        message("obj-85_zero", "0", [250.0, 350.0, 25.0, 20.0]), # Reset active pitch buffer to 0
        newobj("obj-86", "pack 0 0", [200.0, 380.0, 60.0, 20.0], inlets=2, outlets=1, outlettype=[""]), # Note-off pack
        newobj("obj-87", "pack 0 95", [280.0, 380.0, 65.0, 20.0], inlets=2, outlets=1, outlettype=[""]), # Note-on pack
        newobj("obj-89", "t i i", [200.0, 590.0, 40.0, 20.0], inlets=1, outlets=2, outlettype=["int", "int"]), # Single-shot pitch splitter
        newobj("obj-88", "t b b b b b", [200.0, 260.0, 75.0, 20.0], inlets=1, outlets=5, outlettype=["bang"] * 5),

        # 4. Gesture Position Monitor Dials (Hand X & Hand Y)
        newobj("obj-33", "scale 0. 1. 0 127", [450.0, 110.0, 105.0, 20.0], inlets=5, outlets=1, outlettype=["float"]),
        newobj("obj-34", "i", [450.0, 140.0, 30.0, 20.0], inlets=2, outlets=1, outlettype=["int"]),
        live_dial("obj-35", "Hand X", [450.0, 170.0, 44.0, 48.0], pres=[8.0, 74.0, 44.0, 48.0], lo=0.0, hi=127.0, init=64.0, unitstyle=0, shortname="Hand X"),

        newobj("obj-40", "scale 0. 1. 0 127", [620.0, 110.0, 105.0, 20.0], inlets=5, outlets=1, outlettype=["float"]),
        newobj("obj-41", "i", [620.0, 140.0, 30.0, 20.0], inlets=2, outlets=1, outlettype=["int"]),
        live_dial("obj-42", "Hand Y", [620.0, 170.0, 44.0, 48.0], pres=[56.0, 74.0, 44.0, 48.0], lo=0.0, hi=127.0, init=64.0, unitstyle=0, shortname="Hand Y"),

        # 5. Midiformat on MIDI channel 1
        newobj("obj-50", "midiformat 1", [200.0, 720.0, 110.0, 20.0], inlets=7, outlets=1, outlettype=["int"]),

        # Musical Performance Dials
        live_dial("obj-52", "Octave", [860.0, 170.0, 44.0, 48.0], pres=[146.0, 24.0, 42.0, 48.0], lo=-1.0, hi=2.0, init=0.0, unitstyle=0, shortname="Oct"),
        live_dial("obj-51", "Duration", [800.0, 170.0, 44.0, 48.0], pres=[192.0, 24.0, 42.0, 48.0], lo=50.0, hi=4000.0, init=350.0, unitstyle=2, shortname="Dur"),
        live_dial("obj-53", "Volume", [920.0, 170.0, 44.0, 48.0], pres=[238.0, 24.0, 42.0, 48.0], lo=1.0, hi=127.0, init=95.0, unitstyle=0, shortname="Vol"),

        # Manual Test Button
        live_button("obj-54", "TEST", [980.0, 170.0, 45.0, 20.0], pres=[238.0, 86.0, 42.0, 26.0]),

        # Presentation UI Headers & Labels
        comment("obj-55", "SPATIAL THEREMIN", [30.0, 720.0, 140.0, 20.0], pres=[8.0, 6.0, 130.0, 16.0], fontsize=11.0, fontface=1),
        comment("obj-56", "OSC :8765", [30.0, 745.0, 100.0, 20.0], pres=[142.0, 6.0, 70.0, 14.0], fontsize=9.0),
        comment("obj-57", "SCALE", [30.0, 770.0, 60.0, 15.0], pres=[8.0, 23.0, 50.0, 12.0], fontsize=8.0, fontface=1),
        comment("obj-58", "ROOT", [30.0, 790.0, 50.0, 15.0], pres=[96.0, 23.0, 40.0, 12.0], fontsize=8.0, fontface=1),
        comment("obj-59", "GESTURE MONITOR", [30.0, 810.0, 140.0, 15.0], pres=[106.0, 78.0, 76.0, 14.0], fontsize=8.5, fontface=1),
        comment("obj-60", "Hand X & Y", [30.0, 830.0, 140.0, 15.0], pres=[106.0, 94.0, 76.0, 12.0], fontsize=7.5),

        # Section 2 Header: Hand X Map
        comment("obj-70", "HAND X MAP (HORIZONTAL)", [300.0, 800.0, 180.0, 15.0], pres=[290.0, 6.0, 165.0, 14.0], fontsize=8.5, fontface=1),
        comment("obj-71", "Map to up to 2 Live controls", [300.0, 820.0, 180.0, 15.0], pres=[290.0, 20.0, 165.0, 12.0], fontsize=7.5),

        # Section 3 Header: Hand Y Map
        comment("obj-72", "HAND Y MAP (VERTICAL)", [550.0, 800.0, 180.0, 15.0], pres=[556.0, 6.0, 165.0, 14.0], fontsize=8.5, fontface=1),
        comment("obj-73_lbl", "Map to up to 2 Live controls", [550.0, 820.0, 180.0, 15.0], pres=[556.0, 20.0, 165.0, 12.0], fontsize=7.5),
    ]

    # Slot builder helper
    def add_slot(prefix, base_id, py_base, map_pres, lbl_pres, min_pres, max_pres, unm_pres):
        b = []
        b.append(live_toggle_btn(f"obj-{base_id}", f"Map {prefix}", "Map", "Mapping...", [py_base, 100.0, 45.0, 20.0], pres=map_pres))
        b.append(message(f"obj-{base_id+1}", "mapping $1", [py_base, 130.0, 70.0, 20.0]))
        b.append(newobj(f"obj-{base_id+2}", "live.map", [py_base, 160.0, 60.0, 20.0], inlets=1, outlets=5, outlettype=["", "", "", "int", ""]))
        b.append(newobj(f"obj-{base_id+3}", "live.remote~ @normalized 1", [py_base, 190.0, 150.0, 20.0], inlets=2, outlets=2, outlettype=["", ""]))
        b.append(newobj(f"obj-{base_id+4}", "prepend set", [py_base, 220.0, 75.0, 20.0], inlets=1, outlets=1, outlettype=[""]))
        b.append(comment(f"obj-{base_id+5}", "[Unmapped]", [py_base, 250.0, 100.0, 20.0], pres=lbl_pres, fontsize=8.5))
        b.append(live_unmap_btn(f"obj-{base_id+6}", f"Unmap {prefix}", [py_base, 280.0, 25.0, 20.0], pres=unm_pres))
        b.append(message(f"obj-{base_id+7}", "unmap", [py_base, 310.0, 50.0, 20.0]))
        b.append(message(f"obj-{base_id+8}", "id 0", [py_base, 335.0, 40.0, 20.0]))
        b.append(message(f"obj-{base_id+9}", "set [Unmapped]", [py_base, 360.0, 95.0, 20.0]))
        b.append(message(f"obj-{base_id+10}", "0", [py_base, 385.0, 30.0, 20.0]))
        b.append(live_pct_dial(f"obj-{base_id+11}", f"Min {prefix}", [py_base, 410.0, 44.0, 44.0], pres=min_pres, init=0.0))
        b.append(live_pct_dial(f"obj-{base_id+12}", f"Max {prefix}", [py_base, 460.0, 44.0, 44.0], pres=max_pres, init=100.0))
        b.append(newobj(f"obj-{base_id+13}", "expr $f1 * (($f3 - $f2) * 0.01) + ($f2 * 0.01)", [py_base, 510.0, 240.0, 20.0], inlets=3, outlets=1, outlettype=["float"]))
        b.append(newobj(f"obj-{base_id+14}", "clip 0. 1.", [py_base, 540.0, 65.0, 20.0], inlets=3, outlets=1, outlettype=["float"]))
        return b

    # Slot X1
    boxes.extend(add_slot("X1", 100, 700.0,
                          map_pres=[290.0, 38.0, 40.0, 20.0],
                          lbl_pres=[334.0, 40.0, 96.0, 16.0],
                          min_pres=[434.0, 28.0, 38.0, 44.0],
                          max_pres=[476.0, 28.0, 38.0, 44.0],
                          unm_pres=[518.0, 38.0, 18.0, 20.0]))

    # Slot X2
    boxes.extend(add_slot("X2", 120, 850.0,
                          map_pres=[290.0, 84.0, 40.0, 20.0],
                          lbl_pres=[334.0, 86.0, 96.0, 16.0],
                          min_pres=[434.0, 74.0, 38.0, 44.0],
                          max_pres=[476.0, 74.0, 38.0, 44.0],
                          unm_pres=[518.0, 84.0, 18.0, 20.0]))

    # Slot Y1
    boxes.extend(add_slot("Y1", 140, 1000.0,
                          map_pres=[556.0, 38.0, 40.0, 20.0],
                          lbl_pres=[600.0, 40.0, 96.0, 16.0],
                          min_pres=[700.0, 28.0, 38.0, 44.0],
                          max_pres=[742.0, 28.0, 38.0, 44.0],
                          unm_pres=[784.0, 38.0, 18.0, 20.0]))

    # Slot Y2
    boxes.extend(add_slot("Y2", 160, 1150.0,
                          map_pres=[556.0, 84.0, 40.0, 20.0],
                          lbl_pres=[600.0, 86.0, 96.0, 16.0],
                          min_pres=[700.0, 74.0, 38.0, 44.0],
                          max_pres=[742.0, 74.0, 38.0, 44.0],
                          unm_pres=[784.0, 84.0, 18.0, 20.0]))

    pt["boxes"] = boxes

    cords = [
        # Pass incoming MIDI through
        (["obj-1", 0], ["obj-2", 0]),

        # UDP -> Route
        (["obj-3", 0], ["obj-4", 0]),

        # Inbound set_scale / set_root / set_octave / set_hold / gate / mode from Web UI
        (["obj-4", 4], ["obj-10", 0]), # set_scale -> Scale live.menu
        (["obj-4", 5], ["obj-18", 0]), # set_root -> Root live.menu
        (["obj-4", 6], ["obj-52", 0]), # set_octave -> Octave live.dial
        (["obj-4", 7], ["obj-73", 0]), # set_hold -> t i i router
        (["obj-4", 8], ["obj-81", 0]), # gate -> sel 0 (pinch release detector)
        (["obj-4", 9], ["obj-90", 0]), # mode -> t i b router

        # Loadbang / Thisdevice init -> default Min Pent (obj-12) & initialize Mode engine
        (["obj-8", 0], ["obj-12", 0]),
        (["obj-9", 0], ["obj-12", 0]),
        (["obj-8", 0], ["obj-76", 0]), # evaluate expr on load

        # Scale menu -> sel 0..5 -> message -> zl.lookup right inlet
        (["obj-10", 0], ["obj-11", 0]),
        (["obj-11", 0], ["obj-12", 0]),
        (["obj-11", 1], ["obj-13", 0]),
        (["obj-11", 2], ["obj-14", 0]),
        (["obj-11", 3], ["obj-15", 0]),
        (["obj-11", 4], ["obj-16", 0]),
        (["obj-11", 5], ["obj-17", 0]),

        (["obj-12", 0], ["obj-22", 1]),
        (["obj-13", 0], ["obj-22", 1]),
        (["obj-14", 0], ["obj-22", 1]),
        (["obj-15", 0], ["obj-22", 1]),
        (["obj-16", 0], ["obj-22", 1]),
        (["obj-17", 0], ["obj-22", 1]),

        # Outbound scale/root/octave changes to Web HUD via UDP :8001
        (["obj-10", 0], ["obj-61", 0]), # Scale menu -> /theremin/scale $1
        (["obj-61", 0], ["obj-63", 0]), # /theremin/scale -> udpsend 8001
        (["obj-18", 0], ["obj-62", 0]), # Root menu -> /theremin/root $1
        (["obj-62", 0], ["obj-63", 0]), # /theremin/root -> udpsend 8001

        # Octave dial -> int object -> /theremin/octave $1 (fixes float bug!)
        (["obj-52", 0], ["obj-65", 0]),
        (["obj-65", 0], ["obj-64", 0]),
        (["obj-64", 0], ["obj-63", 0]),

        # Hold UI & Device Synchronization:
        # 1. From Web UI: obj-73 (t i i)
        (["obj-73", 1], ["obj-75_set", 0]), # set $1 updates obj-75 visually WITHOUT firing outlet!
        (["obj-75_set", 0], ["obj-75", 0]),
        (["obj-73", 0], ["obj-91", 0]),     # updates central hold dispatcher

        # 2. From Ableton Device: obj-75 -> obj-74 (t i i)
        (["obj-75", 0], ["obj-74", 0]),
        (["obj-74", 1], ["obj-66", 0]),     # sends /theremin/hold $1 to Web HUD
        (["obj-66", 0], ["obj-63", 0]),     # udpsend 8001
        (["obj-74", 0], ["obj-91", 0]),     # updates central hold dispatcher

        # Central Hold Dispatcher: obj-91 (t i i i i)
        (["obj-91", 3], ["obj-77", 1]),     # sets Hold ($i2) in expr
        (["obj-91", 2], ["obj-76", 0]),     # bangs Mode storage (i 1) to force expr recalculation!
        (["obj-91", 1], ["obj-82", 0]),     # sends Hold to == 0 (pinch release gate control)
        (["obj-91", 0], ["obj-84", 0]),     # sends Hold to sel 0 (cut active note when Hold turned OFF)

        # Mode Router: obj-90 (t i b)
        (["obj-90", 1], ["obj-76", 0]),     # sets & outputs Mode ($i1) in expr
        (["obj-90", 0], ["obj-85", 0]),     # bangs active_pitch to cut note on mode change

        # Mode storage (obj-76) into expr ($i1) (HOT inlet):
        (["obj-76", 0], ["obj-77", 0]),
        (["obj-77", 0], ["obj-78", 0]),     # Expr result -> gate 1 1 control (delay schedule gate)

        # Hold toggle cutoffs:
        (["obj-82", 0], ["obj-83", 0]),     # == 0 -> gate 1 1 control (pinch release gate)
        (["obj-84", 0], ["obj-85", 0]),     # sel 0 bangs active_pitch for note-off!

        # Pinch release cutoff:
        (["obj-81", 0], ["obj-83", 1]),     # gate 0 bang -> gate 1 1 inlet 1
        (["obj-83", 0], ["obj-85", 0]),     # pinch release bangs active_pitch for note-off!

        # Active pitch note-off chain: obj-85 -> obj-85_check (sel 0) -> obj-85_reset (t i b) -> pack 0 0
        (["obj-85", 0], ["obj-85_check", 0]),
        (["obj-85_check", 1], ["obj-85_reset", 0]), # if non-zero pitch, proceed to note-off
        (["obj-85_reset", 1], ["obj-85_zero", 0]),  # outlet 1 (bang): bangs message "0"
        (["obj-85_zero", 0], ["obj-85", 1]),        # "0" into obj-85 cold inlet (resets active pitch to 0)
        (["obj-85_reset", 0], ["obj-86", 0]),       # outlet 0 (int): pitch into pack 0 0 -> midiformat

        # Scale/Root/Octave changes cut ringing note so no hanging pitch across scales
        (["obj-10", 0], ["obj-85", 0]),
        (["obj-18", 0], ["obj-85", 0]),
        (["obj-52", 0], ["obj-85", 0]),

        # Route Pitch (Y) -> Scale -> int -> clip -> zl.lookup left inlet (hot)
        (["obj-4", 0], ["obj-20", 0]),
        (["obj-20", 0], ["obj-21", 0]),
        (["obj-21", 0], ["obj-21_clip", 0]),
        (["obj-21_clip", 0], ["obj-22", 0]),

        # Transposition arithmetic:
        (["obj-22", 0], ["obj-23", 0]),
        (["obj-23", 0], ["obj-24", 0]),
        (["obj-18", 0], ["obj-24", 1]),     # Root offset
        (["obj-24", 0], ["obj-25", 0]),
        (["obj-52", 0], ["obj-26", 0]),     # Octave dial -> * 12
        (["obj-26", 0], ["obj-25", 1]),
        (["obj-25", 0], ["obj-27", 1]),     # Pitch storage (cold)

        # Route Velocity -> i 95 right inlet (COLD)
        (["obj-4", 2], ["obj-28", 1]),
        (["obj-53", 0], ["obj-28", 1]),     # Volume Dial updates velocity

        # Trigger routing into obj-88 (t b b b b b):
        (["obj-4", 1], ["obj-29", 0]),      # /theremin/trigger -> sel 1
        (["obj-29", 0], ["obj-88", 0]),     # sel 1 -> t b b b b b
        (["obj-54", 0], ["obj-88", 0]),     # Test button -> t b b b b b

        # obj-88 sequence (executes right-to-left: outlet 4 to 0):
        (["obj-88", 4], ["obj-80", 0]),     # 1st: stop scheduled delay
        (["obj-80", 0], ["obj-79", 0]),
        (["obj-88", 3], ["obj-85", 0]),     # 2nd: bang active_pitch for note-off of old note
        (["obj-88", 2], ["obj-28", 0]),     # 3rd: bang stored velocity
        (["obj-28", 0], ["obj-87", 1]),     # velocity into note_on_pack inlet 1
        (["obj-88", 1], ["obj-27", 0]),     # 4th: bang stored pitch -> obj-89 (t i i)
        (["obj-27", 0], ["obj-89", 0]),
        (["obj-89", 1], ["obj-85", 1]),     # store new pitch into active_pitch buffer (cold)
        (["obj-89", 0], ["obj-87", 0]),     # fire pitch into note_on_pack inlet 0 (HOT note-on!)
        (["obj-88", 0], ["obj-78", 1]),     # 5th: pass bang into delay gate (only fires if Theremin & Hold OFF)
        (["obj-78", 0], ["obj-79", 0]),     # schedule delay timer

        # Duration dial into delay inlet 1
        (["obj-51", 0], ["obj-79", 1]),

        # Delay timer fires note-off after Duration ms:
        (["obj-79", 0], ["obj-85", 0]),

        # Note-off pack execution:
        (["obj-86", 0], ["obj-50", 0]),     # note-off -> midiformat 1 inlet 0

        # Note-on pack execution:
        (["obj-87", 0], ["obj-50", 0]),     # note-on -> midiformat 1 inlet 0

        # Hand X Position Dial:
        (["obj-4", 3], ["obj-33", 0]),  # Cutoff (X) float -> scale 0..127
        (["obj-33", 0], ["obj-34", 0]),
        (["obj-34", 0], ["obj-35", 0]), # Hand X dial

        # Hand Y Position Dial:
        (["obj-4", 0], ["obj-40", 0]),  # Pitch (Y) float -> scale 0..127
        (["obj-40", 0], ["obj-41", 0]),
        (["obj-41", 0], ["obj-42", 0]), # Hand Y dial

        # Midiformat to midiout
        (["obj-50", 0], ["obj-2", 0])
    ]

    # Wire all 4 mapping slots
    def wire_slot(base_id, input_source):
        return [
            # Map button -> message mapping $1 -> live.map
            ([f"obj-{base_id}", 0], [f"obj-{base_id+1}", 0]),
            ([f"obj-{base_id+1}", 0], [f"obj-{base_id+2}", 0]),

            # live.map outlet 1 (id) -> live.remote~ inlet 1
            ([f"obj-{base_id+2}", 1], [f"obj-{base_id+3}", 1]),

            # live.map outlet 2 (name) -> prepend set -> comment
            ([f"obj-{base_id+2}", 2], [f"obj-{base_id+4}", 0]),
            ([f"obj-{base_id+4}", 0], [f"obj-{base_id+5}", 0]),

            # live.map outlet 3 (mapping finished 0) -> turn off Map toggle button
            ([f"obj-{base_id+2}", 3], [f"obj-{base_id}", 0]),

            # Unmap button triggers 4 messages:
            ([f"obj-{base_id+6}", 0], [f"obj-{base_id+7}", 0]),  # unmap -> live.map
            ([f"obj-{base_id+7}", 0], [f"obj-{base_id+2}", 0]),
            ([f"obj-{base_id+6}", 0], [f"obj-{base_id+8}", 0]),  # id 0 -> live.remote~
            ([f"obj-{base_id+8}", 0], [f"obj-{base_id+3}", 1]),
            ([f"obj-{base_id+6}", 0], [f"obj-{base_id+9}", 0]),  # set [Unmapped] -> label
            ([f"obj-{base_id+9}", 0], [f"obj-{base_id+5}", 0]),
            ([f"obj-{base_id+6}", 0], [f"obj-{base_id+10}", 0]), # 0 -> Map button
            ([f"obj-{base_id+10}", 0], [f"obj-{base_id}", 0]),

            # Gesture input -> expr inlet 0
            (input_source, [f"obj-{base_id+13}", 0]),

            # Min / Max dials -> expr inlets 1 & 2
            ([f"obj-{base_id+11}", 0], [f"obj-{base_id+13}", 1]),
            ([f"obj-{base_id+12}", 0], [f"obj-{base_id+13}", 2]),

            # expr -> clip -> live.remote~ inlet 0
            ([f"obj-{base_id+13}", 0], [f"obj-{base_id+14}", 0]),
            ([f"obj-{base_id+14}", 0], [f"obj-{base_id+3}", 0]),
        ]

    # Hand X gesture input: obj-4 outlet 3 (float 0.0 to 1.0)
    cords.extend(wire_slot(100, ["obj-4", 3])) # X1
    cords.extend(wire_slot(120, ["obj-4", 3])) # X2

    # Hand Y gesture input: obj-4 outlet 0 (float 0.0 to 1.0)
    cords.extend(wire_slot(140, ["obj-4", 0])) # Y1
    cords.extend(wire_slot(160, ["obj-4", 0])) # Y2

    pt["lines"] = [{"patchline": {"source": s, "destination": d}} for s, d in cords]

    param_names = [
        "Scale", "Root", "Octave", "Duration", "Volume",
        "Hand X", "Hand Y", "TEST", "Hold",
        "Map X1", "Min X1", "Max X1", "Unmap X1",
        "Map X2", "Min X2", "Max X2", "Unmap X2",
        "Map Y1", "Min Y1", "Max Y1", "Unmap Y1",
        "Map Y2", "Min Y2", "Max Y2", "Unmap Y2"
    ]
    pt["parameters"] = {
        "obj-10": ["Scale", "Scale", 0],
        "obj-18": ["Root", "Root", 0],
        "obj-35": ["Hand X", "Hand X", 0],
        "obj-42": ["Hand Y", "Hand Y", 0],
        "obj-51": ["Duration", "Dur", 0],
        "obj-52": ["Octave", "Oct", 0],
        "obj-53": ["Volume", "Vol", 0],
        "obj-54": ["TEST", "Test", 0],
        "obj-75": ["Hold", "Hold", 0],

        "obj-100": ["Map X1", "Map X1", 0],
        "obj-106": ["Unmap X1", "Unmap X1", 0],
        "obj-111": ["Min X1", "Min X1", 0],
        "obj-112": ["Max X1", "Max X1", 0],

        "obj-120": ["Map X2", "Map X2", 0],
        "obj-126": ["Unmap X2", "Unmap X2", 0],
        "obj-131": ["Min X2", "Min X2", 0],
        "obj-132": ["Max X2", "Max X2", 0],

        "obj-140": ["Map Y1", "Map Y1", 0],
        "obj-146": ["Unmap Y1", "Unmap Y1", 0],
        "obj-151": ["Min Y1", "Min Y1", 0],
        "obj-152": ["Max Y1", "Max Y1", 0],

        "obj-160": ["Map Y2", "Map Y2", 0],
        "obj-166": ["Unmap Y2", "Unmap Y2", 0],
        "obj-171": ["Min Y2", "Min Y2", 0],
        "obj-172": ["Max Y2", "Max Y2", 0],

        "parameterbanks": {
            "0": {
                "index": 0,
                "name": "",
                "parameters": param_names
            }
        }
    }
    return p

def main():
    dev = build_device()
    data = amxd.build(dev, kind="midi")

    local_out = os.path.join(HERE, "Spatial_Theremin.amxd")
    with open(local_out, "wb") as f:
        f.write(data)
    print(f"wrote {local_out} ({len(data)} bytes, standalone native MIDI effect)")

    if os.path.isdir(USER_LIBRARY_MIDI):
        user_out = os.path.join(USER_LIBRARY_MIDI, "Spatial_Theremin.amxd")
        with open(user_out, "wb") as f:
            f.write(data)
        print(f"wrote {user_out}")

if __name__ == "__main__":
    main()
