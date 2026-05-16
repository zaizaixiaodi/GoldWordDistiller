"""Merge 3 batches of distillation results, deduplicate, and output summary."""
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).parent

with open(BASE / "distilled_batch_0_69.json", "r", encoding="utf-8") as f:
    batch1 = json.load(f)

# Batch 2 inline data
batch2_gw = [
    {"word":"普通人","aliases":[],"category":"who","source_field":"title","vibe_score":6,"frequency":4,"related_post_ids":["recvjLqZenx6p9","recvjLqZenavKq","recvjLqZCTPVT3","recvjLroaDlHkq"]},
    {"word":"大学生","aliases":[],"category":"who","source_field":"title","vibe_score":5,"frequency":2,"related_post_ids":["recvjLqZenbmA8","recvjLqZenpxFy"]},
    {"word":"低能量的人","aliases":[],"category":"who","source_field":"title","vibe_score":7,"frequency":2,"related_post_ids":["recvjLroaDDQ65","recvjLroaDnohg"]},
    {"word":"强女","aliases":[],"category":"who","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLqZCT81R6"]},
    {"word":"超级个体","aliases":[],"category":"who","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLqZCTZA7K"]},
    {"word":"44岁","aliases":[],"category":"who","source_field":"title","vibe_score":6,"frequency":1,"related_post_ids":["recvjLroaDb5Ii"]},
    {"word":"29岁","aliases":[],"category":"who","source_field":"title","vibe_score":5,"frequency":1,"related_post_ids":["recvjLr03tcecw"]},
    {"word":"下班2小时","aliases":[],"category":"when","source_field":"both","vibe_score":6,"frequency":1,"related_post_ids":["recvjLroaDFvm1"]},
    {"word":"不上班","aliases":[],"category":"pain","source_field":"title","vibe_score":7,"frequency":3,"related_post_ids":["recvjLqZCTlhMq","recvjLr03tcecw","recvjLr03tY6Yw"]},
    {"word":"搞钱","aliases":[],"category":"pain","source_field":"title","vibe_score":7,"frequency":5,"related_post_ids":["recvjLqZenpxFy","recvjLqZenavKq","recvjLqZenh6fQ","recvjLroaDsgo0","recvjLroaDlHkq"]},
    {"word":"搞米","aliases":[],"category":"pain","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLroaDsgo0"]},
    {"word":"翻身","aliases":[],"category":"pain","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLqZenx6p9"]},
    {"word":"低耗能","aliases":["低能耗"],"category":"pain","source_field":"title","vibe_score":7,"frequency":2,"related_post_ids":["recvjLroaDDQ65","recvjLroaDnohg"]},
    {"word":"裸辞","aliases":[],"category":"do","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLr03tcecw"]},
    {"word":"开窍","aliases":[],"category":"do","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLroaDfnEk"]},
    {"word":"手搓","aliases":[],"category":"do","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLqlJdCgpI"]},
    {"word":"避坑","aliases":[],"category":"do","source_field":"title","vibe_score":6,"frequency":1,"related_post_ids":["recvjLroaDprM4"]},
    {"word":"搭便车","aliases":[],"category":"do","source_field":"title","vibe_score":6,"frequency":2,"related_post_ids":["recvjLqZCTPVT3","recvjLroAp5Vcn"]},
    {"word":"人生转机","aliases":[],"category":"twist","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLqZCTlhMq"]},
    {"word":"野路子","aliases":[],"category":"twist","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLqZenX3R8"]},
    {"word":"陌生化","aliases":[],"category":"twist","source_field":"both","vibe_score":8,"frequency":1,"related_post_ids":["recvjLqZCTh9bZ"]},
    {"word":"真人假扮AI","aliases":[],"category":"twist","source_field":"both","vibe_score":9,"frequency":1,"related_post_ids":["recvjLroAp61Rr"]},
    {"word":"黑马属性","aliases":[],"category":"twist","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLroaDfnEk"]},
    {"word":"变态","aliases":[],"category":"twist","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLqZCTQBSr"]},
    {"word":"100w","aliases":["100万"],"category":"number","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLqZCTPVT3"]},
    {"word":"5w","aliases":["5万"],"category":"number","source_field":"both","vibe_score":7,"frequency":1,"related_post_ids":["recvjLroaDDQ65"]},
    {"word":"365天","aliases":[],"category":"number","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLroaDprM4"]},
    {"word":"掏心窝子","aliases":[],"category":"feel","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLr03trQ74"]},
    {"word":"长脑子了","aliases":[],"category":"feel","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLqZenmyux"]},
    {"word":"强女思维","aliases":[],"category":"feel","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLqZCT81R6"]},
    {"word":"来得及","aliases":[],"category":"feel","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLroaDb5Ii"]},
    {"word":"生存系统","aliases":[],"category":"picture","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLroAp5Vcn"]},
    {"word":"双线搞钱","aliases":[],"category":"picture","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLroaDlHkq"]},
    {"word":"小生意","aliases":[],"category":"picture","source_field":"title","vibe_score":5,"frequency":1,"related_post_ids":["recvjLqZCTPVT3"]},
]

# Batch 3 inline data
batch3_gw = [
    {"word":"搞钱","aliases":[],"category":"do","source_field":"title","vibe_score":8,"frequency":12,"related_post_ids":["recvjLB4rePWZE","recvjLB4Ti1Zd0","recvjLB4TiCv6Y","recvjLB4Ti31z8","recvjLB4Tiaw5j","recvjLB5jaYsAD","recvjLB5jaqBN2","recvjLB4reOTzD","recvjLB4re8paZ","recvjLB4TigXMr","recvjLB4reFo10","recvjLB4reInLt"]},
    {"word":"搞到米","aliases":["搞米"],"category":"do","source_field":"title","vibe_score":7,"frequency":2,"related_post_ids":["recvjLB4TiA4we","recvjLB4TiCv6Y"]},
    {"word":"躺赢","aliases":[],"category":"do","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB4Tiaw5j"]},
    {"word":"钱生钱","aliases":[],"category":"picture","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB4rePWZE"]},
    {"word":"野路子","aliases":[],"category":"picture","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB4rePWZE"]},
    {"word":"狠狠搞","aliases":["狠狠"],"category":"do","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB4rePWZE"]},
    {"word":"信息差","aliases":[],"category":"picture","source_field":"title","vibe_score":7,"frequency":2,"related_post_ids":["recvjLB4Tiaw5j","recvjLB5KLH5SC"]},
    {"word":"逆天改命","aliases":[],"category":"feel","source_field":"title","vibe_score":9,"frequency":1,"related_post_ids":["recvjLB6cMZad3"]},
    {"word":"上桌","aliases":[],"category":"do","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB6DKpGAi"]},
    {"word":"空手套白狼","aliases":[],"category":"picture","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB4rePWZE"]},
    {"word":"压舱石","aliases":[],"category":"picture","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB5KLWaCH"]},
    {"word":"安全垫","aliases":[],"category":"picture","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLB5KLMZTI"]},
    {"word":"信息生态位","aliases":[],"category":"picture","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB6DKS2zv"]},
    {"word":"财富天花板","aliases":[],"category":"picture","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLB6DKS2zv"]},
    {"word":"男生思维","aliases":[],"category":"twist","source_field":"both","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB4reOTzD"]},
    {"word":"35岁提前退休","aliases":[],"category":"twist","source_field":"title","vibe_score":8,"frequency":2,"related_post_ids":["recvjLB5KL2MG9","recvjLB5KLrkzC"]},
    {"word":"失去兴趣","aliases":[],"category":"twist","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB5KLH5SC"]},
    {"word":"第一个10w","aliases":[],"category":"number","source_field":"title","vibe_score":7,"frequency":2,"related_post_ids":["recvjLB4Tih090","recvjLB5KLZOgC"]},
    {"word":"10亿","aliases":[],"category":"number","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB4TigXMr"]},
    {"word":"月薪2k","aliases":[],"category":"number","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB5jaqBN2"]},
    {"word":"上海首付","aliases":[],"category":"number","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLB5jaqBN2"]},
    {"word":"100W","aliases":["100w","100万"],"category":"number","source_field":"title","vibe_score":7,"frequency":2,"related_post_ids":["recvjLB5KLZOgC","recvjLB6cMVsbY"]},
    {"word":"fu*k you money","aliases":[],"category":"feel","source_field":"title","vibe_score":9,"frequency":1,"related_post_ids":["recvjLB5KLrkzC"]},
    {"word":"人间清醒","aliases":[],"category":"feel","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLB4reOTzD"]},
    {"word":"赚钱的脑子","aliases":[],"category":"picture","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLB6DKiDpG"]},
    {"word":"资本家思路","aliases":[],"category":"picture","source_field":"title","vibe_score":8,"frequency":1,"related_post_ids":["recvjLB6DKYF7V"]},
    {"word":"无背景无学历","aliases":[],"category":"who","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLB6cMZad3"]},
    {"word":"05女大","aliases":[],"category":"who","source_field":"title","vibe_score":7,"frequency":1,"related_post_ids":["recvjLB4Ti1Zd0"]},
    {"word":"INFP","aliases":[],"category":"who","source_field":"title","vibe_score":6,"frequency":1,"related_post_ids":["recvjLB5jab0Qk"]},
    {"word":"低能量的人","aliases":[],"category":"who","source_field":"title","vibe_score":7,"frequency":2,"related_post_ids":["recvjLB6cMZad3","recvjLroaDDQ65"]},
    {"word":"30岁之前","aliases":[],"category":"when","source_field":"title","vibe_score":6,"frequency":1,"related_post_ids":["recvjLB6cMQo1j"]},
    {"word":"未来三年","aliases":[],"category":"when","source_field":"title","vibe_score":6,"frequency":1,"related_post_ids":["recvjLB6cMBHUr"]},
    {"word":"不要上班","aliases":["不想上班"],"category":"pain","source_field":"title","vibe_score":6,"frequency":2,"related_post_ids":["recvjLB5KL2MG9","recvjLB5KLMZTI"]},
    {"word":"瞎努力","aliases":[],"category":"feel","source_field":"title","vibe_score":6,"frequency":1,"related_post_ids":["recvjLB6DK1d26"]},
]

# Merge
all_gw = batch1["gold_words"] + batch2_gw + batch3_gw
merged = {}
for g in all_gw:
    key = g["word"]
    if key in merged:
        existing = merged[key]
        existing_ids = set(existing.get("related_post_ids", []))
        new_ids = set(g.get("related_post_ids", []))
        existing["related_post_ids"] = list(existing_ids | new_ids)
        existing["vibe_score"] = max(existing["vibe_score"], g["vibe_score"])
        existing["frequency"] = existing.get("frequency", 0) + g.get("frequency", 0)
        existing_aliases = set(existing.get("aliases", []))
        new_aliases = set(g.get("aliases", []))
        existing["aliases"] = list(existing_aliases | new_aliases)
        if len(g.get("vibe_reason", "")) > len(existing.get("vibe_reason", "")):
            existing["vibe_reason"] = g["vibe_reason"]
        if existing["source_field"] != g["source_field"]:
            existing["source_field"] = "both"
    else:
        merged[key] = dict(g)

final_gw = sorted(merged.values(), key=lambda x: (-x["vibe_score"], -x["frequency"]))

result = {"gold_words": final_gw, "patterns": batch1["patterns"], "total_source_posts": 200}
with open(BASE / "distilled_merged.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# Summary
cats = Counter(g["category"] for g in final_gw)
print(f"=== Merged Gold Words ===")
print(f"Total unique: {len(final_gw)}")
print(f"\nBy category:")
for c, n in cats.most_common():
    print(f"  {c:10s}: {n}")

print(f"\nTOP 30 (by vibe_score, then frequency):")
for g in final_gw[:30]:
    print(f"  {g['word']:16s} [{g['category']:8s}|{g['source_field']:5s}] vibe={g['vibe_score']} freq={g['frequency']}")

vibe_dist = Counter()
for g in final_gw:
    if g["vibe_score"] >= 8:
        vibe_dist["8-10"] += 1
    elif g["vibe_score"] >= 6:
        vibe_dist["6-7"] += 1
    elif g["vibe_score"] >= 4:
        vibe_dist["4-5"] += 1
    else:
        vibe_dist["3"] += 1
print(f"\nvibe_score distribution:")
for k, v in sorted(vibe_dist.items()):
    print(f"  {k}: {v}")
