"""Re-render the Anki 介紹 covers from the 147-Data design canvas layout (1600x900)."""
import asyncio, html, os, sys
from playwright.async_api import async_playwright

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

# page id, two big chars, line 1 (cream), line 2 (accent), tag, side text, background
COVERS = [
    ("cba3f1e365f48255b54601347e55d77b", "開始", "七個步驟上手 Anki，", "下載、匯入，就能開始刷題。", "《Anki 極簡教學》", "新手必看", "#45743C"),
    ("2853f1e365f48273be6181350dc6ed1a", "間隔", "記不住就按重來，", "記得住就交給時間。", "《間隔複習介紹》", "學習階段・畢業間隔", "#47699D"),
    ("5723f1e365f4830cb9d481db188bd07a", "挑選", "考前衝刺，", "只挑你要的卡片複習。", "《只複習特定卡片》", "自訂學習", "#985656"),
    ("6db3f1e365f482538ecb017e4df19556", "插件", "讀書計畫、熱圖、快捷鍵，", "三個外掛讓 Anki 更好用。", "《推薦的 add-ons》", "實用附加元件", "#357274"),
    ("5bf3f1e365f4820baffe01cc93bdfd9b", "排程", "考試排程顯示在 Anki 首頁，", "一鍵同步 Google 行事曆。", "《Exam Calendar 使用手冊》", "安裝與同步", "#7A5C97"),
    ("a073f1e365f48345ba8801bd4afea52b", "下載", "電腦、手機、平板、網頁，", "該下載哪一個版本？", "《Anki 各平台介紹》", "各平台下載指南", "#586A7D"),
    ("7673f1e365f4826ea0ea81b47152cf84", "雲端", "牌組、附加元件、更新日誌，", "全部在這個資料夾下載。", "《Anki 字卡》", "Google Drive 快速進入", "#8A4F6B"),
    # not on the canvas: same style, new copy
    ("3f73f1e365f4811b9ec8dfeb09eca809", "卡片", "一張卡片，", "就是一個要記住的問題。", "《卡片是什麼》", "基本觀念", "#6B7A45"),
    ("3f73f1e365f481a184c0f9eca7560e98", "筆記", "一則筆記，", "可以產生好幾張卡片。", "《筆記是什麼》", "基本觀念", "#4F6D8C"),
    ("3f73f1e365f481a99fd2f810fa03752c", "牌組", "把卡片分門別類，", "一個牌組就是一份題庫。", "《牌組（題組）是什麼》", "基本觀念", "#8C5A3C"),
    ("3f73f1e365f481c7b3e1c254cd09d44d", "題型", "問答、克漏字、圖片遮擋，", "決定卡片長什麼樣子。", "《筆記類型（題型）是什麼》", "基本觀念", "#5C5470"),
]

TEMPLATE = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>
body{{margin:0}}
.f{{font-family:'Noto Serif CJK TC','Noto Serif TC',serif}}
</style></head><body>
<div class="f" style="width:1600px;height:900px;box-sizing:border-box;position:relative;overflow:hidden;background:{bg};color:#F5EFC9;display:flex;align-items:center;gap:65px;padding:0 100px 0 130px">
<div style="display:flex;flex-direction:column;flex-shrink:0;font-size:165px;line-height:1.02;font-weight:700;color:#E9B949"><div>{c1}</div><div>{c2}</div></div>
<div style="display:flex;flex-direction:column">
<div style="font-size:85px;font-weight:700;line-height:1.35;letter-spacing:3px;white-space:nowrap;color:#F5EFC9">{l1}</div>
<div style="font-size:85px;font-weight:700;line-height:1.35;letter-spacing:3px;white-space:nowrap;color:#E9B949">{l2}</div>
<div style="display:flex;align-items:center;gap:28px;margin-top:55px">
<div style="background:#E9B949;color:{bg};font-size:42px;font-weight:700;padding:7px 17px;white-space:nowrap">{tag}</div>
<div style="font-size:38px;font-weight:400;letter-spacing:2px;white-space:nowrap;color:#F5EFC9">{side}</div>
</div></div>
<div style="position:absolute;right:60px;bottom:60px;font-family:'DejaVu Serif',serif;font-style:italic;font-size:32px;color:#F5EFC9;opacity:0.8">Linyi</div>
</div></body></html>"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        pg = await b.new_page(viewport={"width": 1600, "height": 900})
        for pid, big, l1, l2, tag, side, bg in COVERS:
            e = html.escape
            await pg.set_content(TEMPLATE.format(bg=bg, c1=e(big[0]), c2=e(big[1]), l1=e(l1), l2=e(l2), tag=e(tag), side=e(side)))
            # shrink the two title lines if they overflow the frame
            await pg.evaluate("""() => {
              const box = document.querySelector('.f');
              const col = box.children[1];
              let s = 85;
              while (box.scrollWidth > 1600 && s > 50) { s -= 3;
                col.children[0].style.fontSize = s + 'px'; col.children[1].style.fontSize = s + 'px'; }
            }""")
            await pg.screenshot(path=os.path.join(OUT, pid + ".png"))
        await b.close()

asyncio.run(main())
print("done")
