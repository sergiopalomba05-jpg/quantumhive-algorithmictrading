import { SpritesheetData } from "./types";

// Design_01 (🎨) — QuantumHive Agent
export const spritesheetData: SpritesheetData = {
  "meta": { "image": "/ai-town/assets/agent-sprites.png", "size": { "w": 576, "h": 128 } },
  "frames": {
    "down": { "frame": {"x":288,"y":0,"w":32,"h":32} },
    "down2": { "frame": {"x":320,"y":0,"w":32,"h":32} },
    "down3": { "frame": {"x":352,"y":0,"w":32,"h":32} },
    "left": { "frame": {"x":288,"y":32,"w":32,"h":32} },
    "left2": { "frame": {"x":320,"y":32,"w":32,"h":32} },
    "left3": { "frame": {"x":352,"y":32,"w":32,"h":32} },
    "right": { "frame": {"x":288,"y":64,"w":32,"h":32} },
    "right2": { "frame": {"x":320,"y":64,"w":32,"h":32} },
    "right3": { "frame": {"x":352,"y":64,"w":32,"h":32} },
    "up": { "frame": {"x":288,"y":96,"w":32,"h":32} },
    "up2": { "frame": {"x":320,"y":96,"w":32,"h":32} },
    "up3": { "frame": {"x":352,"y":96,"w":32,"h":32} },
  },
  "animations": {
    "down": ['down', 'down2', 'down3'],
    "left": ['left', 'left2', 'left3'],
    "right": ['right', 'right2', 'right3'],
    "up": ['up', 'up2', 'up3'],
  },
};
