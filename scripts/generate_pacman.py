"""
Generates assets/pacman-dark.svg and assets/pacman-light.svg
Custom Pac-Man contribution graph using GitHub GraphQL API.
Pac-Man traverses the grid in boustrophedon order eating contribution dots.
"""
import os, json, math, urllib.request

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME     = "svssdeva"
ASSETS_DIR   = "assets"

CELL      = 14     # px per contribution cell
GAP       = 2      # px gap between cells
PAD       = 20     # outer padding
ANIM_DUR  = 20.0   # total animation seconds (one full traversal)

THEMES = {
    "dark": {
        "bg":     "#0d1117",
        "empty":  "#161b22",
        "l1":     "#ffe066",
        "l2":     "#ffd700",
        "l3":     "#ffb300",
        "l4":     "#ff8c00",
        "pac":    "#ffe066",
        "text":   "#8b949e",
    },
    "light": {
        "bg":     "#ffffff",
        "empty":  "#ebedf0",
        "l1":     "#9be9a8",
        "l2":     "#40c463",
        "l3":     "#30a14e",
        "l4":     "#216e39",
        "pac":    "#ffcc00",
        "text":   "#57606a",
    },
}

GQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            contributionCount
            weekday
          }
        }
      }
    }
  }
}
"""


def fetch_contributions():
    payload = json.dumps({"query": GQL_QUERY, "variables": {"login": USERNAME}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "svssdeva-pacman-bot",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    grid = []
    for week in weeks:
        day_counts = [0] * 7
        for day in week["contributionDays"]:
            day_counts[day["weekday"]] = day["contributionCount"]
        grid.append(day_counts)
    return grid


def cell_center(week, day):
    """Return the center (x, y) of a contribution cell."""
    x = PAD + week * (CELL + GAP) + CELL // 2
    y = PAD + day  * (CELL + GAP) + CELL // 2
    return x, y


def boustrophedon_path(num_weeks, num_days=7):
    """Row-by-row alternating direction path through the grid."""
    path = []
    for day in range(num_days):
        weeks = range(num_weeks) if day % 2 == 0 else range(num_weeks - 1, -1, -1)
        for week in weeks:
            path.append((week, day))
    return path


def dot_color(count, theme):
    c = THEMES[theme]
    if count == 0:   return c["empty"]
    if count <= 3:   return c["l1"]
    if count <= 6:   return c["l2"]
    if count <= 9:   return c["l3"]
    return c["l4"]


def pac_open_d(r):
    """SVG path for Pac-Man facing right (+x), mouth open ~35 degrees."""
    angle = math.radians(35 / 2)
    x1 = r * math.cos(angle)
    y1 = r * math.sin(angle)
    # Go from (x1, -y1) around the full arc to (x1, y1), then back to origin
    return (f"M 0 0 L {x1:.3f} {-y1:.3f} "
            f"A {r:.3f} {r:.3f} 0 1 0 {x1:.3f} {y1:.3f} Z")


def pac_closed_d(r):
    """SVG path for Pac-Man facing right, mouth nearly closed (4 degrees)."""
    angle = math.radians(4 / 2)
    x1 = r * math.cos(angle)
    y1 = r * math.sin(angle)
    return (f"M 0 0 L {x1:.3f} {-y1:.3f} "
            f"A {r:.3f} {r:.3f} 0 1 0 {x1:.3f} {y1:.3f} Z")


def generate_svg(grid, theme_name):
    c = THEMES[theme_name]
    num_weeks = len(grid)
    num_days  = 7

    W = PAD * 2 + num_weeks * (CELL + GAP)
    H = PAD * 2 + num_days  * (CELL + GAP) + 18

    path_cells = boustrophedon_path(num_weeks, num_days)
    N = len(path_cells)

    # Map (week, day) → path index for fast lookup
    pos_map = {cell: i for i, cell in enumerate(path_cells)}

    # Build animateMotion path string and keyTimes/keyPoints
    motion_parts = []
    for i, (week, day) in enumerate(path_cells):
        x, y = cell_center(week, day)
        motion_parts.append(f"{'M' if i == 0 else 'L'} {x} {y}")
    motion_path = " ".join(motion_parts)

    # Uniform keyTimes and keyPoints (equal spacing = equal speed since steps equidistant)
    kt = [f"{i / (N - 1):.5f}" for i in range(N)]
    kt_str = ";".join(kt)

    PR = (CELL + GAP) * 0.52   # pac-man radius — just slightly bigger than half-cell
    open_d   = pac_open_d(PR)
    closed_d = pac_closed_d(PR)

    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'xmlns:xlink="http://www.w3.org/1999/xlink" '
               f'width="{W}" height="{H}">')
    out.append(f'<rect width="{W}" height="{H}" fill="{c["bg"]}"/>')

    # ── Contribution dots ───────────────────────────────────────────────────────
    for w_idx, week_days in enumerate(grid):
        for d_idx, count in enumerate(week_days):
            x, y   = cell_center(w_idx, d_idx)
            color  = dot_color(count, theme_name)
            rx_val = 3

            cell_key = (w_idx, d_idx)
            path_pos = pos_map.get(cell_key, -1)

            if count > 0 and path_pos >= 0:
                # Dot disappears when Pac-Man arrives (discrete jump)
                t = path_pos / (N - 1)
                anim = (f'<animate attributeName="opacity" '
                        f'values="1;0" keyTimes="0;{t:.5f}" '
                        f'calcMode="discrete" dur="{ANIM_DUR}s" '
                        f'repeatCount="indefinite"/>')
                out.append(
                    f'<rect x="{x - CELL//2}" y="{y - CELL//2}" '
                    f'width="{CELL}" height="{CELL}" rx="{rx_val}" '
                    f'fill="{color}">{anim}</rect>'
                )
            else:
                out.append(
                    f'<rect x="{x - CELL//2}" y="{y - CELL//2}" '
                    f'width="{CELL}" height="{CELL}" rx="{rx_val}" '
                    f'fill="{color}"/>'
                )

    # ── Motion path (invisible, referenced by animateMotion) ───────────────────
    out.append(f'<path id="pacpath" d="{motion_path}" fill="none" stroke="none"/>')

    # ── Pac-Man ────────────────────────────────────────────────────────────────
    # Eye
    eye_r  = PR * 0.14
    eye_ox = PR * 0.25   # offset from center
    eye_oy = PR * 0.35

    out.append('<g id="pacman">')
    # Body (animated mouth open/close)
    out.append(
        f'<path d="{open_d}" fill="{c["pac"]}">'
        # Mouth animation: open → closed → open every 0.25s
        f'<animate attributeName="d" '
        f'values="{open_d};{closed_d};{open_d}" '
        f'dur="0.25s" repeatCount="indefinite"/>'
        # Motion along path
        f'<animateMotion dur="{ANIM_DUR}s" repeatCount="indefinite" '
        f'rotate="auto" calcMode="linear" '
        f'keyTimes="{kt_str}" keyPoints="{kt_str}">'
        f'<mpath xlink:href="#pacpath"/>'
        f'</animateMotion>'
        f'</path>'
    )
    # Eye (follows Pac-Man — same animateMotion)
    out.append(
        f'<circle cx="{eye_ox:.3f}" cy="{-eye_oy:.3f}" r="{eye_r:.3f}" fill="{c["bg"]}">'
        f'<animateMotion dur="{ANIM_DUR}s" repeatCount="indefinite" '
        f'rotate="auto" calcMode="linear" '
        f'keyTimes="{kt_str}" keyPoints="{kt_str}">'
        f'<mpath xlink:href="#pacpath"/>'
        f'</animateMotion>'
        f'</circle>'
    )
    out.append('</g>')

    # ── Label ──────────────────────────────────────────────────────────────────
    out.append(
        f'<text x="{W // 2}" y="{H - 4}" '
        f'font-family="\'Segoe UI\',sans-serif" font-size="10" '
        f'fill="{c["text"]}" text-anchor="middle">'
        f'Pac-Man Contribution Graph</text>'
    )

    out.append('</svg>')
    return "\n".join(out)


if __name__ == "__main__":
    os.makedirs(ASSETS_DIR, exist_ok=True)

    print("Fetching contribution data...")
    grid = fetch_contributions()
    total = sum(c for week in grid for c in week)
    print(f"  {len(grid)} weeks, {total} total contributions")

    for theme_name in ("dark", "light"):
        svg = generate_svg(grid, theme_name)
        path = os.path.join(ASSETS_DIR, f"pacman-{theme_name}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        size_kb = os.path.getsize(path) // 1024
        print(f"  Generated {path} ({size_kb} KB)")

    print("Done.")
