"""
Generates assets/power-level-slider.gif
Each Goku transformation plays in full, then slides out left as the next slides in from the right.
"""
from PIL import Image, ImageDraw, ImageFont
import os, sys

# ── Config ────────────────────────────────────────────────────────────────────

CANVAS_W        = 600
CANVAS_H        = 480
BG              = (26, 27, 39)        # tokyonight bg
LABEL_H         = 50                   # height reserved at bottom for label
GIF_H           = CANVAS_H - LABEL_H  # usable height for the sprite
MAX_FRAMES      = 28                   # max frames to take from each source GIF
TRANSITION_STEPS = 14                  # frames for slide-in animation
TRANS_DELAY     = 30                   # ms per transition frame
PAUSE_FRAMES    = 6                    # extra hold frames at end of each GIF
PAUSE_DELAY     = 80                   # ms per hold frame
ASSETS          = "assets"
OUTPUT          = os.path.join(ASSETS, "power-level-slider.gif")

LABEL_COLOR     = (112, 165, 253)      # #70a5fd  tokyonight blue
RANK_COLORS = {
    "SSJ":             (115, 218, 202),   # #73daca  green
    "SSJ2":            (187, 154, 247),   # #bb9af7  purple
    "SSJ3":            (224, 175, 104),   # #e0af68  yellow
    "SSJ4 Full Power": (255, 215,   0),   # gold
    "SSJ God":         (247, 118, 142),   # #f7768e  red/pink
    "SSJ Blue":        (122, 162, 247),   # #7aa2f7  blue
    "SSJ Blue Kaioken":(255, 158, 100),   # #ff9e64  orange
}

GIFS = [
    (os.path.join(ASSETS, "ssj-trans.gif"),          "SSJ"),
    (os.path.join(ASSETS, "ssj2-trans.gif"),         "SSJ2"),
    (os.path.join(ASSETS, "ssj3-trans.gif"),         "SSJ3"),
    (os.path.join(ASSETS, "full-power-ssj4.gif"),    "SSJ4 Full Power"),
    (os.path.join(ASSETS, "ssj-god.gif"),            "SSJ God"),
    (os.path.join(ASSETS, "ssj-blue.gif"),           "SSJ Blue"),
    (os.path.join(ASSETS, "kaioken-blue.gif"),       "SSJ Blue Kaioken"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def fit_into(frame, w, h):
    """Fit a PIL image into w×h canvas, centered, with BG fill."""
    frame = frame.convert("RGBA")
    # Remove near-black background (common in sprite GIFs)
    canvas = Image.new("RGB", (w, h), BG)
    scale  = min(w / frame.width, h / frame.height)
    nw, nh = int(frame.width * scale), int(frame.height * scale)
    frame  = frame.resize((nw, nh), Image.LANCZOS)
    x, y   = (w - nw) // 2, (h - nh) // 2
    canvas.paste(frame, (x, y), frame)
    return canvas


def draw_label(canvas, text, color):
    """Draw a centered label at the bottom of the canvas."""
    draw = ImageDraw.Draw(canvas)
    # Use default PIL font — no external font needed
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw   = bbox[2] - bbox[0]
    th   = bbox[3] - bbox[1]
    tx   = (CANVAS_W - tw) // 2
    ty   = GIF_H + (LABEL_H - th) // 2
    draw.text((tx, ty), text, fill=color, font=font)


def load_gif(path, label):
    """Extract up to MAX_FRAMES from a GIF, fitted to canvas, with label."""
    img    = Image.open(path)
    frames, delays = [], []
    idx    = 0
    try:
        while idx < MAX_FRAMES:
            f = fit_into(img.copy(), CANVAS_W, GIF_H)
            # Add label bar at bottom
            full = Image.new("RGB", (CANVAS_W, CANVAS_H), BG)
            full.paste(f, (0, 0))
            draw_label(full, label, RANK_COLORS.get(label, LABEL_COLOR))
            frames.append(full)
            delays.append(img.info.get("duration", 80))
            img.seek(img.tell() + 1)
            idx += 1
    except EOFError:
        pass
    if not frames:
        raise RuntimeError(f"No frames found in {path}")
    # Pad short GIFs with repeated last frame
    while len(frames) < 8:
        frames.append(frames[-1].copy())
        delays.append(delays[-1])
    return frames, delays


def make_slide_transition(from_frame, to_frame, steps, delay):
    """Slide to_frame in from the right while from_frame exits left."""
    frames, delays = [], []
    W = CANVAS_W
    for i in range(1, steps + 1):
        offset  = int(W * i / steps)
        combined = Image.new("RGB", (W, CANVAS_H), BG)
        # outgoing: crop right portion
        combined.paste(from_frame.crop((offset, 0, W, CANVAS_H)), (0, 0))
        # incoming: crop left portion
        combined.paste(to_frame.crop((0, 0, offset, CANVAS_H)), (W - offset, 0))
        frames.append(combined)
        delays.append(delay)
    return frames, delays


# ── Build ─────────────────────────────────────────────────────────────────────

def build_slider():
    all_frames, all_delays = [], []

    gif_data = []
    for path, label in GIFS:
        if not os.path.exists(path):
            print(f"  SKIP (not found): {path}")
            continue
        print(f"  Loading {label}...")
        frames, delays = load_gif(path, label)
        gif_data.append((label, frames, delays))

    if not gif_data:
        print("ERROR: no source GIFs found.")
        sys.exit(1)

    for idx, (label, frames, delays) in enumerate(gif_data):
        print(f"  Adding {label} ({len(frames)} frames)...")

        # Slide in from right (into first frame)
        if idx == 0:
            # First GIF: just appear (no incoming transition)
            all_frames.append(frames[0])
            all_delays.append(delays[0])
        else:
            prev_last = gif_data[idx - 1][1][-1]
            t_frames, t_delays = make_slide_transition(
                prev_last, frames[0], TRANSITION_STEPS, TRANS_DELAY
            )
            all_frames.extend(t_frames)
            all_delays.extend(t_delays)

        # Play all frames
        all_frames.extend(frames)
        all_delays.extend(delays)

        # Hold on last frame briefly
        for _ in range(PAUSE_FRAMES):
            all_frames.append(frames[-1].copy())
            all_delays.append(PAUSE_DELAY)

    # Slide back to first (loop: last → first)
    t_frames, t_delays = make_slide_transition(
        gif_data[-1][1][-1], gif_data[0][1][0], TRANSITION_STEPS, TRANS_DELAY
    )
    all_frames.extend(t_frames)
    all_delays.extend(t_delays)

    print(f"  Total frames: {len(all_frames)}")

    os.makedirs(ASSETS, exist_ok=True)
    all_frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=all_frames[1:],
        duration=all_delays,
        loop=0,
        optimize=False,
    )
    size_kb = os.path.getsize(OUTPUT) // 1024
    print(f"  Saved {OUTPUT} ({size_kb} KB)")


if __name__ == "__main__":
    print("Generating power level slider...")
    build_slider()
    print("Done.")
