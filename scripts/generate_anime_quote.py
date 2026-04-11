import os
import datetime

ASSETS_DIR = "assets"
OUTPUT_FILE = os.path.join(ASSETS_DIR, "anime-quote.svg")

QUOTES = [
    {"quote": "Hard work is worthless for those that don't believe in themselves.", "character": "Naruto Uzumaki", "anime": "Naruto"},
    {"quote": "Power comes in response to a need, not a desire.", "character": "Goku", "anime": "Dragon Ball Z"},
    {"quote": "The only ones who should kill are those who are prepared to be killed.", "character": "Lelouch vi Britannia", "anime": "Code Geass"},
    {"quote": "If you don't take risks, you can't create a future.", "character": "Monkey D. Luffy", "anime": "One Piece"},
    {"quote": "It's not the face that makes someone a monster. It's the choices they make with their lives.", "character": "Naruto Uzumaki", "anime": "Naruto"},
    {"quote": "Whatever you lose, you'll find it again. But what you throw away you'll never get back.", "character": "Kenshin Himura", "anime": "Rurouni Kenshin"},
    {"quote": "People's lives don't end when they die. It ends when they lose faith.", "character": "Itachi Uchiha", "anime": "Naruto"},
    {"quote": "A lesson without pain is meaningless. That's because no one can gain without sacrificing something.", "character": "Edward Elric", "anime": "Fullmetal Alchemist"},
    {"quote": "Knowing what it feels to be in pain, is exactly why we try to be kind to others.", "character": "Jiraiya", "anime": "Naruto"},
    {"quote": "The world isn't perfect. But it's there for us, doing the best it can. That's what makes it so damn beautiful.", "character": "Roy Mustang", "anime": "Fullmetal Alchemist"},
    {"quote": "I'll leave tomorrow's problems to tomorrow's me.", "character": "Saitama", "anime": "One Punch Man"},
    {"quote": "Fear is not evil. It tells you what your weakness is. And once you know your weakness, you can become stronger as well as kinder.", "character": "Gildarts Clive", "anime": "Fairy Tail"},
    {"quote": "If you can't find a reason to fight, then you shouldn't be fighting.", "character": "Akame", "anime": "Akame ga Kill"},
    {"quote": "We are all like fireworks: we climb, we shine, and always go our separate ways and become further apart.", "character": "Hitsugaya Toshiro", "anime": "Bleach"},
    {"quote": "The only way to truly escape the mundane is for you to constantly be evolving.", "character": "Gojo Satoru", "anime": "Jujutsu Kaisen"},
    {"quote": "No matter how hard or impossible it is, never lose sight of your goal.", "character": "Monkey D. Luffy", "anime": "One Piece"},
    {"quote": "It's okay not to be okay as long as you are not giving up.", "character": "Karen Aijou", "anime": "Revue Starlight"},
    {"quote": "Those who cannot acknowledge themselves will eventually fail.", "character": "Itachi Uchiha", "anime": "Naruto Shippuden"},
    {"quote": "Even if I'm worthless and carry demon blood... I want to move forward with my own strength.", "character": "Inuyasha", "anime": "Inuyasha"},
    {"quote": "If nobody cares to accept you and wants you in this world, accept yourself and you will see that you don't need them and their selfish ideas.", "character": "Alibaba Saluja", "anime": "Magi"},
    {"quote": "To know sorrow is not terrifying. What is terrifying is to know you can't go back to happiness you could have.", "character": "Matsumoto Rangiku", "anime": "Bleach"},
    {"quote": "Every journey begins with a single step. We just have to have patience.", "character": "Mifune", "anime": "Naruto Shippuden"},
    {"quote": "If you just submit yourself to fate, then that's the end of it.", "character": "Kirito", "anime": "Sword Art Online"},
    {"quote": "You can't sit around envying other people's worlds. You have to go out and change your own.", "character": "Shinichi Izumi", "anime": "Parasyte"},
    {"quote": "Sometimes it's necessary to do unnecessary things.", "character": "Kanade Jinguuji", "anime": "The Fruit of Grisaia"},
    {"quote": "A dropout will beat a genius through hard work.", "character": "Rock Lee", "anime": "Naruto"},
    {"quote": "When you hit the point of no return, that's the moment it truly becomes a journey.", "character": "Gekko Moriah", "anime": "One Piece"},
    {"quote": "If you wanna make people dream, you've gotta start by believing in that dream yourself.", "character": "Seiya Kanie", "anime": "Amagi Brilliant Park"},
    {"quote": "Simplicity is the easiest path to true beauty.", "character": "Seika Ijima", "anime": "Maid Sama"},
    {"quote": "If you don't like your destiny, don't accept it.", "character": "Naruto Uzumaki", "anime": "Naruto"},
]


def fetch_quote():
    day_of_year = datetime.datetime.utcnow().timetuple().tm_yday
    return QUOTES[day_of_year % len(QUOTES)]


def escape_xml(s):
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&apos;")
    )


def word_wrap(text, max_chars=52):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_svg(quote, character, anime):
    quote = escape_xml(quote[:160] + ("\u2026" if len(quote) > 160 else ""))
    character = escape_xml(character[:50])
    anime = escape_xml(anime[:60])

    lines = word_wrap(quote)
    line_h = 22
    quote_block_h = len(lines) * line_h
    total_h = quote_block_h + 112

    tspans = "".join(
        f'<tspan x="34" dy="{line_h if i > 0 else 0}">{ln}</tspan>'
        for i, ln in enumerate(lines)
    )

    attr_y = quote_block_h + 68
    anime_y = attr_y + 18
    footer_y = total_h - 10

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="{total_h}" '
        f'viewBox="0 0 600 {total_h}">\n'
        f'  <rect width="600" height="{total_h}" rx="12" fill="#1a1b27"/>\n'
        f'  <rect x="1" y="1" width="598" height="{total_h - 2}" rx="11" fill="none" '
        f'stroke="#70a5fd" stroke-width="1" opacity="0.35"/>\n'
        f'  <text x="16" y="36" font-size="20">\U0001f338</text>\n'
        f'  <text x="562" y="36" font-size="20">\U0001f338</text>\n'
        f'  <text x="22" y="52" font-family="Georgia,serif" font-size="44" '
        f'fill="#70a5fd" opacity="0.3">\u201c</text>\n'
        f'  <text font-family="\'Segoe UI\',Arial,sans-serif" font-size="14" '
        f'fill="#c0caf5" x="34" y="58">{tspans}</text>\n'
        f'  <text x="34" y="{attr_y}" font-family="\'Segoe UI\',Arial,sans-serif" '
        f'font-size="13" fill="#70a5fd">\u2014 {character}</text>\n'
        f'  <text x="34" y="{anime_y}" font-family="\'Segoe UI\',Arial,sans-serif" '
        f'font-size="11" fill="#565f89" font-style="italic">{anime}</text>\n'
        f'  <text x="590" y="{footer_y}" font-family="\'Segoe UI\',Arial,sans-serif" '
        f'font-size="9" fill="#3b4261" text-anchor="end">updated daily</text>\n'
        f'</svg>'
    )


if __name__ == "__main__":
    os.makedirs(ASSETS_DIR, exist_ok=True)
    q = fetch_quote()
    svg = generate_svg(q["quote"], q["character"], q["anime"])
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Generated: {q['character']} \u2014 {q['anime']}")
