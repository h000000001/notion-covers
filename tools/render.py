import json, sys, os
from urllib.parse import urlparse
from PIL import Image, ImageDraw, ImageFont

SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SERIF_R = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
if not os.path.exists(SERIF_R):
    SERIF_R = SERIF_B
TC = 1  # TC face index inside the .ttc (SC=0? we look it up below)

def face_index(path, want="TC"):
    for i in range(10):
        try:
            f = ImageFont.truetype(path, 20, index=i)
        except Exception:
            break
        if want in " ".join(f.getname()):
            return i
    return 0

IB = face_index(SERIF_B)
IR = face_index(SERIF_R)
ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"
if not os.path.exists(ITALIC):
    ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Italic.ttf"

CREAM = "#FFFFFF"
ACCENT = "#FFE14D"
CAT = {  # big category -> (bg, two vertical chars)
    "學習": ("#45743C", "學習"),
    "知識": ("#47699D", "知識"),
    "生涯": ("#9A5440", "生涯"),
    "工具": ("#5E4C86", "工具"),
    "生活": ("#2E6B6A", "生活"),
    "興趣/娛樂": ("#5C4716", "興趣"),
}

def category(tags):
    s = set(tags)
    if "個人成長文章" in s: return "生涯"
    if "生活與政府查詢" in s: return "生活"
    if s & {"影音音樂","遊戲","社群媒體","小說閱讀","騎車"}: return "興趣/娛樂"
    if s & {"設計與簡報","實用工具","筆記與專注工具","Notion","AI","Anki","Heptabase"}: return "工具"
    if s & {"國內免費課程","國外課程與知識庫","付費課程平台","語言學習","打字練習"}: return "學習"
    if s & {"電子書與閱讀","新聞與知識媒體","推薦部落格"}: return "知識"
    return "知識"

def split_name(name):
    """Split into (main, sub): text in （） or after ： becomes the sub line."""
    for open_, close in (("（", "）"), ("【", "】")):
        if open_ in name and name.endswith(close):
            i = name.index(open_)
            return name[:i].strip(), name[i+1:-1].strip()
    if "：" in name:
        a, b = name.split("：", 1)
        return a.strip(), b.strip()
    return name.strip(), ""

import re as _re, sys as _sys, logging as _lg, warnings as _w
_w.filterwarnings("ignore")
_sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "vendor", "jieba-0.42.1"))
import jieba as _jb
_jb.setLogLevel(_lg.ERROR)
for _w2 in ["針灸學","視覺化","電子書","中英文","開放式","番茄鐘","心智圖","流程圖","時間戳","縮網址","找室友","租金補貼","房屋稅籍","就學貸款","研究所","長期主義者","財務自由","複習計畫","模版","公版書","圖書館","持續下去","影響我最多","思維模式","數學公式","圖片加連結","自訂網域","日期公式","程式碼","打字射擊","英文文法"]:
    _jb.add_word(_w2, freq=200000)
_GLUE = set("的之了")
_P = "，。、；：？！）」』》,.;:?!"

def _tokens(text):
    """Word-level tokens: latin words stay whole, Chinese is split into words, and
    particles / punctuation stick to the word before them so lines break where people pause."""
    out = []
    for part in _re.findall(r"[A-Za-z0-9.\-'&*+/]+ ?|\s+|[^A-Za-z0-9\s]+", text):
        if _re.match(r"[A-Za-z0-9]", part) or part.isspace():
            out.append(part)
        else:
            out.extend(_jb.cut(part))
    merged = []
    for t in out:
        if merged and (t in _GLUE or (t and t[0] in _P)):
            merged[-1] += t
        else:
            merged.append(t)
    return merged

def wrap(draw, text, font, maxw):
    lines, cur = [], ""
    for t in _tokens(text):
        if draw.textlength((cur + t).rstrip(), font=font) <= maxw or not cur.strip():
            cur += t
        else:
            lines.append(cur.rstrip())
            cur = t.lstrip()
    if cur.strip():
        lines.append(cur.rstrip())
    return [l for l in lines if l]

def _is_latin(t):
    return bool(_re.match(r"[A-Za-z0-9]", t.strip() or "-"))

def best_two(draw, text, font, maxw):
    """Pick the most natural two-line split.
    Prefer: after punctuation > at a Latin/Chinese boundary > balanced word break.
    Avoid: splitting a run of Latin words (brand names) or a number from its classifier."""
    toks = _tokens(text)
    best = None
    for i in range(1, len(toks)):
        a, b = "".join(toks[:i]).rstrip(), "".join(toks[i:]).strip()
        if not a or not b:
            continue
        wa, wb = draw.textlength(a, font=font), draw.textlength(b, font=font)
        if wa > maxw or wb > maxw:
            continue
        prev, nxt = toks[i-1], toks[i]
        score = abs(wa - wb)
        if a[-1] in _P:
            score -= 10000
        if _is_latin(prev) and _is_latin(nxt) and not prev.strip().isdigit():
            score += 5000          # don't cut "Study With / Me"
        if prev.strip() and prev.strip()[-1].isdigit():
            score += 5000          # keep "12 種" together
        if _is_latin(prev) != _is_latin(nxt):
            score -= 300           # natural pause between English name and Chinese
        if best is None or score < best[0]:
            best = (score, [a, b])
    global LAST_PENALTY
    LAST_PENALTY = best[0] >= 4000 if best else False
    return best[1] if best else None
LAST_PENALTY = False

def fit(draw, text, maxw, maxlines, start, minsize, path, idx):
    size = start
    while size >= minsize:
        f = ImageFont.truetype(path, size, index=idx)
        lines = wrap(draw, text, f, maxw)
        if len(lines) <= maxlines and all(draw.textlength(l, font=f) <= maxw * 1.04 for l in lines):
            return f, lines
        size -= 4
    f = ImageFont.truetype(path, minsize, index=idx)
    lines = wrap(draw, text, f, maxw)[:maxlines]
    lines[-1] = lines[-1][:-1] + "…"
    return f, lines

def render(item, out):
    W, H = 1600, 900
    CREAM, ACC = "#F5EFC9", "#E9B949"
    cat = category(item["tags"])
    bg, big = CAT[cat]
    bg = item.get("bg") or bg
    big = item.get("kw") or big
    detail = [t for t in item["tags"] if t not in ("大學", "高中")]
    detail = detail[0] if detail else cat
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    FB = lambda size: ImageFont.truetype(SERIF_B, size, index=IB)
    FR = lambda size: ImageFont.truetype(SERIF_R, size, index=IR)
    BIG, GAP = 210, 70
    maxw = W - 110 - BIG - GAP - 70
    main, sub = split_name(item["name"])
    if not sub:
        sub = item["domain"]
    # title: line(s) of the name in cream, then the sub line in accent, same size
    size = 124
    while True:
        f = FB(size)
        lm = wrap(d, main, f, maxw)
        bad = False
        if len(lm) == 2:
            lm = best_two(d, main, f, maxw) or lm
            bad = LAST_PENALTY
        ls = wrap(d, sub, f, maxw)
        if len(ls) == 2:
            ls = best_two(d, sub, f, maxw) or ls
            bad = bad or LAST_PENALTY
        ok = len(lm) + len(ls) <= 3 and all(d.textlength(l, font=f) <= maxw * 1.03 for l in lm + ls)
        ok = ok and size * 1.42 * (len(lm) + len(ls)) + 64 + 98 <= H * 0.80   # keep clear margins top and bottom
        if (ok and not (bad and size > 96)) or size <= 72: break
        size -= 4
    lm, ls = lm[:2], ls[:max(1, 3 - len(lm[:2]))]
    ftag = FB(64)
    tag = f"《{detail}》"
    tw = d.textlength(tag, font=ftag)
    lh = size * 1.42
    TAGH, TGAP = 98, 64
    block_h = lh * (len(lm) + len(ls)) + TGAP + TAGH
    x0 = 110                      # fixed position for the category characters on every cover
    rx = x0 + BIG + GAP
    # big vertical characters, centred on the text block
    fbig = FB(BIG)
    by = (H - (BIG * 2 + 10)) / 2 - BIG * 0.08
    for ch in big[:2]:
        d.text((x0, by), ch, font=fbig, fill=ACC); by += BIG + 10
    y = (H - block_h) / 2
    for ln in lm:
        d.text((rx, y), ln, font=f, fill=CREAM); y += lh
    for ln in ls:
        d.text((rx, y), ln, font=f, fill=ACC); y += lh
    y += TGAP - (lh - size) * 0.2
    d.rectangle([rx, y, rx + tw + 46, y + TAGH], fill=ACC)
    d.text((rx + 23, y + 6), tag, font=ftag, fill=bg)
    fi = ImageFont.truetype(ITALIC, 36)
    sw = d.textlength("Linyi", font=fi)
    d.text((W - 60 - sw, H - 60 - 42), "Linyi", font=fi, fill="#E4DDBA")
    img = img.resize((1200, 675), Image.LANCZOS)
    img.save(out, optimize=True)

if __name__ == "__main__":
    items = json.load(open(sys.argv[1], encoding="utf-8"))
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    only = sys.argv[3:]  # optional ids
    kws = [l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "keywords.txt"), encoding="utf-8") if l.strip()]
    assert len(kws) == len(items), (len(kws), len(items))
    for it, kw in zip(items, kws):
        it["kw"] = kw
    for it in items:
        if only and it["id"] not in only:
            continue
        it["domain"] = urlparse(it["url"]).netloc.replace("www.", "")
        render(it, os.path.join(outdir, it["id"] + ".png"))
    print("done")
