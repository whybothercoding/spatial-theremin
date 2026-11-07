// server.js - lightweight standalone HTTP & WebSocket bridge to Ableton OSC
// Zero external npm dependencies (uses native Node.js http, crypto, dgram)
const http = require('http');
const crypto = require('crypto');
const dgram = require('dgram');
const fs = require('fs');
const path = require('path');

const HTTP_PORT = 8080;
const OSC_PORT = 8765;       // Send to Ableton M4L
const FEEDBACK_PORT = 8001;   // Receive from Ableton M4L
const OSC_HOST = '127.0.0.1';

const udpClient = dgram.createSocket('udp4');
const feedbackServer = dgram.createSocket('udp4');

let currentScale = 0;
let currentRoot = 0;
let currentOctave = 0; // Default: 3rd octave
let currentHold = 0;   // 0: Normal / decay, 1: Note Hold active
let currentMode = 1;   // 1: Theremin, 0: Pinch Trigger

function oscFloat(address, val) {
    let addr = Buffer.from(address + '\0');
    while (addr.length % 4 !== 0) addr = Buffer.concat([addr, Buffer.from([0])]);
    let tags = Buffer.from(',f\0\0');
    let data = Buffer.alloc(4);
    data.writeFloatBE(Number(val) || 0.0, 0);
    return Buffer.concat([addr, tags, data]);
}

function oscInt(address, val) {
    let addr = Buffer.from(address + '\0');
    while (addr.length % 4 !== 0) addr = Buffer.concat([addr, Buffer.from([0])]);
    let tags = Buffer.from(',i\0\0');
    let data = Buffer.alloc(4);
    data.writeInt32BE(Number(val) || 0, 0);
    return Buffer.concat([addr, tags, data]);
}

// Robust OSC Packet Parser supporting both Float (f) and Int (i) type tags
function parseOsc(buffer) {
    let nullIdx = buffer.indexOf(0);
    if (nullIdx === -1) return null;
    const address = buffer.slice(0, nullIdx).toString('utf-8');

    let tagOffset = nullIdx + 1;
    while (tagOffset % 4 !== 0) tagOffset++;

    let val = null;
    if (tagOffset < buffer.length && buffer[tagOffset] === 0x2C) { // ','
        let tagNull = buffer.indexOf(0, tagOffset);
        let tags = buffer.slice(tagOffset, tagNull !== -1 ? tagNull : tagOffset + 4).toString('utf-8');
        let dataOffset = (tagNull !== -1 ? tagNull + 1 : tagOffset + 4);
        while (dataOffset % 4 !== 0) dataOffset++;

        if (dataOffset + 4 <= buffer.length) {
            const firstTag = tags[1];
            if (firstTag === 'f') {
                val = Math.round(buffer.readFloatBE(dataOffset));
            } else if (firstTag === 'i') {
                val = buffer.readInt32BE(dataOffset);
            }
        }
    }

    if (val === null && buffer.length >= 4) {
        val = buffer.readInt32BE(buffer.length - 4);
    }
    return { address, value: val };
}

function sendOsc(buffer) {
    udpClient.send(buffer, 0, buffer.length, OSC_PORT, OSC_HOST);
}

// Track active WebSocket clients
const activeSockets = new Set();

function broadcastWs(obj) {
    const json = JSON.stringify(obj);
    const payload = Buffer.from(json);
    let header;
    if (payload.length < 126) {
        header = Buffer.from([0x81, payload.length]);
    } else {
        header = Buffer.alloc(4);
        header[0] = 0x81;
        header[1] = 126;
        header.writeUInt16BE(payload.length, 2);
    }
    const frame = Buffer.concat([header, payload]);
    for (const s of Array.from(activeSockets)) {
        if (s.destroyed || !s.writable) {
            activeSockets.delete(s);
            continue;
        }
        s.write(frame, (err) => {
            if (err) {
                activeSockets.delete(s);
                try { s.destroy(); } catch (e) {}
            }
        });
    }
}

// HTTP Server serving index.html
const server = http.createServer((req, res) => {
    if (req.url === '/' || req.url === '/index.html') {
        const html = fs.readFileSync(path.join(__dirname, 'index.html'));
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(html);
    } else {
        res.writeHead(404);
        res.end('Not found');
    }
});

// Minimal RFC 6455 WebSocket Server Implementation
server.on('upgrade', (req, socket, head) => {
    if (req.headers['upgrade'] !== 'websocket') {
        socket.destroy();
        return;
    }

    // Attach error handlers immediately to prevent unhandled EPIPE crashes
    socket.on('error', (err) => {
        activeSockets.delete(socket);
        try { socket.destroy(); } catch (e) {}
    });
    socket.on('close', () => {
        activeSockets.delete(socket);
    });
    socket.on('end', () => {
        activeSockets.delete(socket);
    });

    const key = req.headers['sec-websocket-key'];
    const hash = crypto.createHash('sha1')
        .update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11')
        .digest('base64');

    const headers = [
        'HTTP/1.1 101 Switching Protocols',
        'Upgrade: websocket',
        'Connection: Upgrade',
        `Sec-WebSocket-Accept: ${hash}`
    ];
    socket.write(headers.join('\r\n') + '\r\n\r\n');

    activeSockets.add(socket);
    console.log('[WebSocket] Client connected! Total:', activeSockets.size);

    // Send initial state immediately
    setTimeout(() => {
        if (!socket.destroyed && socket.writable) {
            broadcastWs({
                type: "scale_state",
                scale: currentScale,
                root: currentRoot,
                octave: currentOctave,
                hold: currentHold
            });
        }
    }, 100);

    socket.on('data', (buffer) => {
        if (buffer.length < 2) return;
        const isMasked = (buffer[1] & 0x80) !== 0;
        let payloadLen = buffer[1] & 0x7F;
        let offset = 2;
        if (payloadLen === 126) {
            payloadLen = buffer.readUInt16BE(2);
            offset = 4;
        } else if (payloadLen === 127) {
            return;
        }
        if (!isMasked) return;
        const mask = buffer.slice(offset, offset + 4);
        offset += 4;
        const payload = buffer.slice(offset, offset + payloadLen);
        for (let i = 0; i < payload.length; i++) {
            payload[i] ^= mask[i % 4];
        }
        
        try {
            const msg = JSON.parse(payload.toString('utf-8'));
            if (msg.type === 'gesture') {
                if (typeof msg.pitch === 'number') {
                    sendOsc(oscFloat('/theremin/pitch', msg.pitch));
                }
                if (typeof msg.cutoff === 'number') {
                    sendOsc(oscFloat('/theremin/cutoff', msg.cutoff));
                }
                if (typeof msg.modwheel === 'number') {
                    sendOsc(oscFloat('/theremin/modwheel', msg.modwheel));
                }
                if (typeof msg.gate === 'number') {
                    sendOsc(oscInt('/theremin/gate', msg.gate));
                }
                if (msg.trigger) {
                    sendOsc(oscInt('/theremin/velocity', msg.velocity || 100));
                    sendOsc(oscInt('/theremin/trigger', 1));
                }
            } else if (msg.type === 'set_scale') {
                currentScale = Number(msg.scale) || 0;
                sendOsc(oscInt('/theremin/set_scale', currentScale));
                broadcastWs({ type: "scale_state", scale: currentScale, root: currentRoot, octave: currentOctave, hold: currentHold });
                console.log(`[UI -> ABLETON] Set Scale: ${currentScale}`);
            } else if (msg.type === 'set_root') {
                currentRoot = Number(msg.root) || 0;
                sendOsc(oscInt('/theremin/set_root', currentRoot));
                broadcastWs({ type: "scale_state", scale: currentScale, root: currentRoot, octave: currentOctave, hold: currentHold });
                console.log(`[UI -> ABLETON] Set Root: ${currentRoot}`);
            } else if (msg.type === 'set_octave') {
                currentOctave = (typeof msg.octave === 'number') ? msg.octave : (parseInt(msg.octave, 10) || 0);
                sendOsc(oscInt('/theremin/set_octave', currentOctave));
                broadcastWs({ type: "scale_state", scale: currentScale, root: currentRoot, octave: currentOctave, hold: currentHold });
                console.log(`[UI -> ABLETON] Set Octave: ${currentOctave}`);
            } else if (msg.type === 'set_hold') {
                currentHold = msg.hold ? 1 : 0;
                sendOsc(oscInt('/theremin/set_hold', currentHold));
                broadcastWs({ type: "scale_state", scale: currentScale, root: currentRoot, octave: currentOctave, hold: currentHold });
                console.log(`[UI -> ABLETON] Set Hold: ${currentHold}`);
            } else if (msg.type === 'set_mode') {
                currentMode = msg.mode ? 1 : 0;
                sendOsc(oscInt('/theremin/mode', currentMode));
                console.log(`[UI -> ABLETON] Set Mode: ${currentMode === 1 ? 'Theremin' : 'Pinch Trigger'}`);
            }
        } catch (e) {}
    });
});

// Parse OSC packets coming from Ableton M4L (:8001)
feedbackServer.on('message', (buffer) => {
    try {
        const parsed = parseOsc(buffer);
        if (!parsed) return;
        const { address, value } = parsed;

        if (address === '/theremin/scale') {
            currentScale = value !== null ? value : 0;
            console.log(`[ABLETON -> UI] Scale changed: ${currentScale}`);
            broadcastWs({ type: "scale_state", scale: currentScale, root: currentRoot, octave: currentOctave, hold: currentHold });
        } else if (address === '/theremin/root') {
            currentRoot = value !== null ? value : 0;
            console.log(`[ABLETON -> UI] Root changed: ${currentRoot}`);
            broadcastWs({ type: "scale_state", scale: currentScale, root: currentRoot, octave: currentOctave, hold: currentHold });
        } else if (address === '/theremin/octave') {
            currentOctave = value !== null ? value : 0;
            console.log(`[ABLETON -> UI] Octave changed: ${currentOctave}`);
            broadcastWs({ type: "scale_state", scale: currentScale, root: currentRoot, octave: currentOctave, hold: currentHold });
        } else if (address === '/theremin/hold') {
            currentHold = value ? 1 : 0;
            console.log(`[ABLETON -> UI] Hold changed: ${currentHold}`);
            broadcastWs({ type: "scale_state", scale: currentScale, root: currentRoot, octave: currentOctave, hold: currentHold });
        }
    } catch (e) {}
});

feedbackServer.on('error', (err) => {
    console.error('Feedback Server Error:', err);
});

feedbackServer.bind(FEEDBACK_PORT, OSC_HOST, () => {
    console.log(`  Feedback Receiver active on :${FEEDBACK_PORT} (M4L -> Web HUD)`);
});

server.listen(HTTP_PORT, () => {
    console.log(`\n======================================================`);
    console.log(`  SPATIAL THEREMIN VISION SERVER ACTIVE`);
    console.log(`  HTTP Web HUD: http://127.0.0.1:${HTTP_PORT}`);
    console.log(`  Streaming OSC -> 127.0.0.1:${OSC_PORT} (Ableton M4L)`);
    console.log(`======================================================\n`);
});
