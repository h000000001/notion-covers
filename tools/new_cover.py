"""Make one cover in the 學習工具 style.

usage:
  python3 new_cover.py OUT.png "名稱（作者或來源）" 關鍵字 細項標籤 [背景色] [網域]

  關鍵字   two characters shown vertically on the left, e.g. 筆記
  細項標籤 text inside the yellow box, e.g. 實用工具 / 模板 / 官方資源
  背景色   optional hex; defaults to the category colour of the 細項標籤
           Notion tab #3A3633, Heptabase tab #2A4A6B
  網域     optional second line when the name has no （…） part
"""
import sys
import render

out, name, kw, tag = sys.argv[1:5]
bg = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] else None
domain = sys.argv[6] if len(sys.argv) > 6 else ""
render.render({"id": "x", "name": name, "url": "", "tags": [tag], "domain": domain, "kw": kw, "bg": bg}, out)
print(out)
