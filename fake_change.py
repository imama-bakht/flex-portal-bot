import json

with open("flex_saved_v2.json", "r", encoding="utf-8") as f:
    data = json.load(f)

data["marks"]["BA3002 | Sessional-II"][1][2] = "10"
data["attendance"]["BA3002"]["percent"] = "90.00"
data["attendance"]["BA3002"]["absent"] = 2

with open("flex_saved_v2.json", "w", encoding="utf-8") as f:
    json.dump(data, f)

print("Done. The bot now remembers wrong numbers on purpose.")