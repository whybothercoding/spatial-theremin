# Spatial Theremin 🖐️🎵

An expressive, touchless computer vision musical instrument and gesture controller for Ableton Live. Built for creative technologists, performers, and workshop makers.

Combines high-speed webcam hand tracking (**MediaPipe Hands**) with a native Max for Live MIDI Effect (**`Spatial_Theremin.amxd`**) via bidirectional OSC.

---

## Architecture Overview

```
 [ Webcam ] 
     │ (60 FPS Hand Landmarks)
     ▼
 [ Web HUD (Chrome/Safari) ] ──(WebSocket)──► [ Node Bridge (server.js) ]
 (MediaPipe Hands Tracking)                       │
                                                  │ OSC UDP :8765 (Gestures & Notes)
                                                  ▼
                                       [ Ableton Live 12 / Max for Live ]
                                       [ Spatial_Theremin.amxd (MIDI Effect) ]
                                                  │
                                                  │ OSC UDP :8001 (Feedback: Scale/Root/Hold)
                                                  ▼
                                       [ Web HUD UI Sync ]
```

---

## Features

- **8-Note Tactile Ladder**: 8 wide, confident vertical rungs (1 to 1.5 octave span) for stable mid-air note targeting without accidental neighbor triggers.
- **Dual Performance Modes**:
  - **Theremin Mode**: Continuous melodic glissando. Glide your finger vertically across rungs. Notes sustain for the `Duration` knob setting (50ms–4000ms), or ring continuously when **Hold** is ON.
  - **Pinch Trigger Mode**: Physical strike mechanic. Strike a note by pinching index and thumb. **Hold the pinch to sustain** the note; release the pinch to cut the note (or hold indefinitely with **Hold** ON).
- **True Note Hold**: Bidirectional toggle synchronized in real-time between the Web HUD and the Live device GUI.
- **Scale & Key Engine**:
  - **6 Scales**: Minor Pentatonic, Major Pentatonic, Hirajoshi, Dorian, Blues, Whole Tone.
  - **Root Key**: C through B semitones.
  - **Octave Dial**: -1 (Bass / 2nd Octave), 0 (Default / 3rd Octave Center), +1 (Lead / 4th Octave), +2 (High / 5th Octave).
- **2D Gesture Modulation Mapping**:
  - **Hand X (Horizontal)**: Map to up to 2 Live controls simultaneously (e.g., Filter Cutoff & Resonance).
  - **Hand Y (Vertical)**: Map to up to 2 Live controls simultaneously (e.g., Reverb Wet & Delay Feedback).
  - Each mapping slot features its own **Map**, **Unmap (✕)**, and independent **Min %** / **Max %** range dials.

---

## Quick Start Guide

### 1. Start the Vision Server
In your terminal, navigate to the project directory and start the Node bridge:

```bash
cd /Users/theo.dev/Documents/misc/my-ableton/devices/spatial-theremin/vision
node server.js
```

*(Or as a background one-liner that automatically opens your browser):*
```bash
node /Users/theo.dev/Documents/misc/my-ableton/devices/spatial-theremin/vision/server.js & open http://127.0.0.1:8080
```

### 2. Open the Web HUD
- Open **[http://127.0.0.1:8080](http://127.0.0.1:8080)** in Chrome, Brave, or Edge.
- Allow webcam permissions when prompted.
- You will see the mirrored camera view, the glowing 8-note pitch ladder on the right, and live coordinate readouts below.

### 3. Load the Device in Ableton Live
1. Open Ableton Live.
2. In the Live Browser, navigate to:
   ```text
   User Library ──► Presets ──► MIDI Effects ──► Max MIDI Effect ──► Spatial_Theremin.amxd
   ```
3. Drag **`Spatial_Theremin.amxd`** onto any MIDI Track containing an instrument (e.g., Drift, Analog, Wavetable, or Simpler).

### 4. Play!
- **Theremin Mode**: Move your right index finger up and down. Watch the laser guide align with the note boxes on screen and hear notes play in Live.
- **Pinch Mode**: Switch the bottom button to **Pinch Trigger**. Bring your thumb and index finger together to strike and hold notes.
- **Modulation**: Move your hand horizontally (left/right) to sweep any parameter mapped to **Hand X**.

---

## Parameter Mapping Guide

To control synth filters, delay feedback, or any third-party VST parameter with hand movement:

1. On the Max device, look at the **HAND X MAP** or **HAND Y MAP** sections.
2. Click the **Map** button for slot **X1** (it will turn yellow and say `Mapping...`).
3. Click any knob, slider, or parameter in Ableton Live (e.g., Filter Cutoff).
4. The button turns off and displays the parameter name (e.g., `Freq`).
5. Adjust **Min X1** and **Max X1** to restrict the gesture range (e.g., Min 20%, Max 75%).
6. To disconnect, click the **✕** unmap button.

---

## Technical Specifications

| Parameter | Value |
| :--- | :--- |
| **HTTP Web HUD** | `http://127.0.0.1:8080` |
| **OSC Out (to Live)** | UDP `127.0.0.1:8765` |
| **OSC In (Feedback from Live)** | UDP `127.0.0.1:8001` |
| **MIDI Output** | Channel 1 Note On/Off (Vel: 1–127) |
| **Tracking Engine** | MediaPipe Hands (WebAssembly / WebGL, ~60 FPS) |
| **Compiler Script** | `python3 build_theremin.py` |
| **Target AMXD** | Standalone native Max MIDI Effect (`.amxd`) |
