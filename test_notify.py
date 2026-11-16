import urllib.request

topic = "your-topic-name"
message = "Hello from your FLEX bot!"

req = urllib.request.Request(
    "https://ntfy.sh/" + topic,
    data=message.encode("utf-8"),
    headers={"User-Agent": "flex-bot"},
    method="POST",
)
urllib.request.urlopen(req)
print("Sent!")