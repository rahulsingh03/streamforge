import WebSocket from "ws";
import dotenv from "dotenv";

dotenv.config();

const APP_KEY = process.env.REVERB_KEY;
const REVERB_IP = process.env.REVERB_IP;
const REVERB_PORT = process.env.REVERB_PORT;
const VIDEO_ID = 4;

const wsUrl = `ws://${REVERB_IP}:${REVERB_PORT}/app/${APP_KEY}?protocol=7&client=js&version=8.4.0&flash=false`;

console.log("Connecting:", wsUrl);

const ws = new WebSocket(wsUrl);

ws.on("open", () => {
    console.log("✅ Connected to Reverb");

    const channel = `video.${VIDEO_ID}`;

    ws.send(JSON.stringify({
        event: "pusher:subscribe",
        data: {
            channel: channel
        }
    }));

    ws.send(JSON.stringify({
        event: "pusher:subscribe",
        data: {
            channel: "video.5"
        }
    }));

    console.log("📡 Subscribed to:", channel);
});

ws.on("message", (data) => {
    const msg = data.toString();

    try {
        const parsed = JSON.parse(msg);

        if (parsed.event === 'pusher:ping') {
            ws.send(JSON.stringify({
                event: 'pusher:pong',
            }));
            console.log("✅ Ping sent");
            return;
        }

        if (parsed.event === "progress.updated") {
            console.log("🔥 Progress Event Received:", parsed.data);
        }
    } catch (e) { }
});

ws.on("close", () => console.log("❌ Disconnected"));
ws.on("error", (err) => console.log("❌ Error:", err.message));