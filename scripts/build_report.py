#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRIO 资源能力分析报告生成器：读取结构化 JSON，输出 Markdown + 精美网页版 HTML。"""
import argparse
import json
import sys

ADV_TYPE = {
    "劣势": ("劣势（无价值）", "#E74C3C"),
    "竞争均势": ("竞争均势（有价值但不稀有）", "#2980B9"),
    "暂时优势": ("暂时优势（可被模仿）", "#F39C12"),
    "未利用优势": ("未利用优势（缺乏组织）", "#E67E22"),
    "持续竞争优势": ("持续竞争优势", "#27AE60"),
    "待确认": ("待确认（四问不全）", "#95A5A6"),
}


def classify(r):
    v, rr, i, o = r.get("V"), r.get("R"), r.get("I"), r.get("O")
    if not v:
        return "劣势"
    if not rr:
        return "竞争均势"
    if not i:
        return "暂时优势"
    if not o:
        return "未利用优势"
    return "持续竞争优势"


def build_md(data):
    org = data.get("org", "未命名组织")
    strat = data.get("strategy_text", "")
    res = data.get("resources", [])
    lines = []
    lines.append("# VRIO 资源能力分析报告\n")
    lines.append(f"**分析对象**：{org}")
    if strat:
        lines.append(f"**关联战略**：{strat}")
    else:
        lines.append("**关联战略**：（未提供，优势解读标注「待提供战略后复核」）")
    lines.append("")
    pending = [r for r in res if r.get("note")]
    if pending:
        lines.append(f"> ⚠️ 共 {len(pending)} 项标注「供参考·待确认」，优势类型未完全判定。\n")
    lines.append("## 一、VRIO 评估矩阵\n")
    lines.append("| 资源/能力 | V | R | I | O | 竞争优势类型 |")
    lines.append("|-----------|---|---|---|---|--------------|")
    for r in res:
        adv = classify(r) if all(r.get(k) for k in ("V", "R", "I", "O")) else "待确认"
        note = " ⚠待确认" if r.get("note") else ""
        lines.append(f"| {r.get('name','')} | {r.get('V','—')} | {r.get('R','—')} | {r.get('I','—')} | {r.get('O','—')} | {adv}{note} |")
    lines.append("")
    lines.append("## 二、竞争优势解读\n")
    for r in res:
        adv = classify(r) if all(r.get(k) for k in ("V", "R", "I", "O")) else "待确认"
        label, _ = ADV_TYPE.get(adv, (adv, "#000"))
        lines.append(f"- **{r.get('name','')}**：{label}")
    lines.append("")
    if pending:
        lines.append("## 三、供参考·待确认项\n")
        for r in pending:
            lines.append(f"- {r.get('name','')}：{r.get('note')}")
        lines.append("")
    return "\n".join(lines)


def build_html(data):
    org = data.get("org", "未命名组织")
    strat = data.get("strategy_text", "")
    res = data.get("resources", [])
    strat_html = f"<p><b>关联战略：</b>{strat}</p>" if strat else \
        "<p><b>关联战略：</b><span class='warn'>未提供，优势解读标注「待提供战略后复核」</span></p>"
    rows = []
    for r in res:
        full = all(r.get(k) for k in ("V", "R", "I", "O"))
        adv = classify(r) if full else "待确认"
        _, color = ADV_TYPE.get(adv, (adv, "#95A5A6"))
        note = "<span class='warn'>⚠ 待确认</span>" if r.get("note") else ""
        rows.append(f"<tr><td>{r.get('name','')}</td><td>{r.get('V','—')}</td><td>{r.get('R','—')}</td>"
                    f"<td>{r.get('I','—')}</td><td>{r.get('O','—')}</td>"
                    f"<td><span class='tag' style='background:{color}'>{adv}</span>{note}</td></tr>")
    rows_html = "".join(rows)
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>VRIO 分析报告 - {org}</title>
<style>
 *{{box-sizing:border-box;font-family:-apple-system,"Microsoft YaHei",sans-serif;color:#2c3e50;}}
 body{{margin:0;background:#f4f6f8;padding:32px;}}
 .wrap{{max-width:960px;margin:0 auto;background:#fff;border-radius:12px;padding:36px;box-shadow:0 4px 20px rgba(0,0,0,.08);}}
 h1{{color:#1a252f;margin-top:0;}}
 .meta{{color:#7f8c8d;font-size:14px;margin:4px 0;}}
 .warn{{color:#e67e22;}}
 .sec{{margin-top:24px;}}
 table{{width:100%;border-collapse:collapse;margin-top:10px;}}
 th,td{{border:1px solid #ecf0f1;padding:9px 10px;font-size:13px;text-align:center;}}
 th{{background:#f8f9fa;}}
 td:first-child{{text-align:left;}}
 .tag{{display:inline-block;color:#fff;font-size:12px;padding:2px 10px;border-radius:10px;}}
</style></head><body><div class="wrap">
<h1>VRIO 资源能力分析报告</h1>
<div class="meta">分析对象：{org}</div>
{strat_html}
<div class="sec"><h2>VRIO 评估矩阵</h2>
<table><tr><th>资源/能力</th><th>V 价值</th><th>R 稀有</th><th>I 难模仿</th><th>O 组织</th><th>竞争优势类型</th></tr>{rows_html}</table></div>
<div class="sec"><p class="warn">判定逻辑：V否→劣势；V是R否→均势；V/R是I否→暂时优势；V/R/I是O否→未利用优势；四项皆是为→持续竞争优势。</p></div>
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--md-out")
    ap.add_argument("--html-out")
    a = ap.parse_args()
    try:
        data = json.load(open(a.input, encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        sys.exit(1)
    md = build_md(data)
    html = build_html(data)
    if a.md_out:
        open(a.md_out, "w", encoding="utf-8").write(md)
    if a.html_out:
        open(a.html_out, "w", encoding="utf-8").write(html)
    if not a.md_out and not a.html_out:
        print(md)
    else:
        print(json.dumps({"status": "success", "md": a.md_out, "html": a.html_out}, ensure_ascii=False))


if __name__ == "__main__":
    main()
