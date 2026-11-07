// theremin_engine.js - converts normalized hand tracking data to musical scales and CC modulation
inlets = 1;
outlets = 2; // outlet 0: [pitch, velocity, duration], outlet 1: [cc_number, value]

// C Minor Pentatonic across 3 octaves (C3 to C5)
var scale = [48, 51, 53, 55, 58, 60, 63, 65, 67, 70, 72, 75, 77, 79, 82, 84];
var currentPitch = 60;
var currentVel = 95;
var lastNote = -1;

function pitch(v) {
    var clamped = Math.max(0.0, Math.min(1.0, Number(v)));
    var idx = Math.floor(clamped * (scale.length - 0.001));
    var note = scale[idx];
    if (note !== currentPitch) {
        currentPitch = note;
    }
}

function velocity(v) {
    currentVel = Math.max(20, Math.min(127, Math.round(Number(v))));
}

function trigger(t) {
    if (Number(t) > 0) {
        outlet(0, currentPitch, currentVel, 350);
    }
}

function note(n, v, d) {
    outlet(0, Number(n), Number(v || currentVel), Number(d || 350));
}

function cutoff(c) {
    var val = Math.floor(Math.max(0.0, Math.min(1.0, Number(c))) * 127);
    outlet(1, 74, val); // CC 74 (Brightness / Filter Cutoff)
}

function modwheel(m) {
    var val = Math.floor(Math.max(0.0, Math.min(1.0, Number(m))) * 127);
    outlet(1, 1, val);  // CC 1 (Modulation Wheel)
}
