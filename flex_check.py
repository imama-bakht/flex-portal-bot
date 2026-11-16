import re
import sys
import json
import os
import urllib.request
from playwright.sync_api import sync_playwright

topic = "your-topic-name"
save_file = "flex_saved_v2.json"
att_courses = ["BA3002", "BA4002", "MG4011"]
marks_courses = ["BA3002", "BA4002", "BA4091", "MG4011"]
sections = ["Assignment", "Sessional-I", "Sessional-II", "Grand Total Marks"]
skip_columns = ["average", "class average", "standard deviation", "std dev", "minimum", "maximum", "min", "max"]

course_names = {}


def notify(message, title="FLEX update"):
    req = urllib.request.Request(
        "https://ntfy.sh/" + topic,
        data=message.encode("utf-8"),
        headers={"User-Agent": "flex-bot", "Title": title},
        method="POST",
    )
    urllib.request.urlopen(req)


def logged_out(page):
    return page.locator("input[type=password]:visible").count() > 0


def go_to(page, name):
    pattern = re.compile(r"^\s*" + re.escape(name) + r"\s*$")
    page.locator("a:visible").filter(has_text=pattern).first.click()
    page.wait_for_timeout(3000)


def remember_name(code, text):
    found = re.search(r"^" + re.escape(code) + r"-(.*)$", text, re.MULTILINE)
    if found:
        name = re.sub(r"\s*\(.*?\)\s*$", "", found.group(1).strip())
        course_names[code] = name


def course_label(code):
    if code in course_names:
        return course_names[code] + " (" + code + ")"
    return code


def read_attendance(page):
    data = {}
    for code in att_courses:
        tab = page.get_by_text(code, exact=True).locator("visible=true")
        if tab.count() == 0:
            continue
        tab.first.click()
        page.wait_for_timeout(1500)
        text = page.inner_text("body")
        remember_name(code, text)
        percent = re.search(r"Attendance Pecentage:\s*([\d.]+)%", text)
        marks = re.findall(r"^\d+\s+\d{2}-\w{3}-\d{4}\s+[\d.]+\s+(\w)", text, re.MULTILINE)
        data[code] = {
            "percent": percent.group(1) if percent else "not found",
            "lectures": len(marks),
            "absent": marks.count("A"),
        }
    return data


def read_marks(page):
    data = {}
    for code in marks_courses:
        tab = page.get_by_text(code, exact=True).locator("visible=true")
        if tab.count() == 0:
            continue
        tab.first.click()
        page.wait_for_timeout(1500)
        remember_name(code, page.inner_text("body"))
        for name in sections:
            try:
                pattern = re.compile(r"^\s*" + re.escape(name) + r"\s*$")
                found = page.locator("button:visible").filter(has_text=pattern)
                if found.count() == 0:
                    continue
                button = found.first
                target = button.get_attribute("data-target")
                if button.get_attribute("aria-expanded") == "false":
                    button.click(timeout=5000)
                    page.wait_for_timeout(1000)
                pane = page.locator("[id='" + target[1:] + "']")
                rows = pane.locator("tr").evaluate_all(
                    "rows => rows.map(r => Array.from(r.querySelectorAll('th,td')).map(c => c.textContent.replace(/\\s+/g, ' ').trim()))"
                )
                rows = [r for r in rows if any(r)]
                if rows:
                    data[code + " | " + name] = rows
            except Exception:
                pass
    return data


def my_part(rows):
    if not rows:
        return []
    header = rows[0]
    keep = [i for i, h in enumerate(header) if h.lower() not in skip_columns]
    return [[row[i] if i < len(row) else "" for i in keep] for row in rows[1:]]


def describe(key, rows):
    code, section = key.split(" | ")
    if len(rows) < 2:
        return section + ": nothing added yet"
    header = rows[0]
    has_label = header[0].strip().endswith("#")
    lines = []
    for row in rows[1:]:
        if has_label:
            label = row[0]
            start = 1
            if label.isdigit():
                label = "row " + label
            lines.append(section + ", " + label + ":")
        else:
            start = 0
            lines.append(section + ":")
        for i in range(start, len(row)):
            value = row[i]
            if value == "":
                continue
            if value == "-":
                value = "not marked yet"
            name = header[i] if i < len(header) else "Column " + str(i)
            lines.append("   " + name + ": " + value)
    return "\n".join(lines)


# ---------- main part ----------

try:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")

        page = None
        for pg in browser.contexts[0].pages:
            if "flexstudent.nu.edu.pk" in pg.url:
                page = pg
                break

        if page is None or logged_out(page):
            notify("Please open the FLEX Chrome window and log in again.", "FLEX bot needs you")
            print("Not logged in. Sent a message to the phone.")
            raise SystemExit

        go_to(page, "Attendance")
        if logged_out(page):
            notify("Please log in to FLEX again.", "FLEX bot needs you")
            print("Logged out. Sent a message to the phone.")
            raise SystemExit
        new_att = read_attendance(page)

        go_to(page, "Marks")
        if logged_out(page):
            notify("Please log in to FLEX again.", "FLEX bot needs you")
            print("Logged out. Sent a message to the phone.")
            raise SystemExit
        new_marks = read_marks(page)

except SystemExit:
    raise
except Exception as e:
    print("Problem:", str(e).split("\n")[0])
    try:
        notify("The bot could not reach the FLEX Chrome window. Is it open?", "FLEX bot problem")
    except Exception:
        pass
    raise SystemExit

print("Read", len(new_att), "attendance courses and", len(new_marks), "marks sections.")

if len(sys.argv) > 1 and sys.argv[1] == "preview":
    for key, rows in new_marks.items():
        print(course_label(key.split(" | ")[0]))
        print(describe(key, rows))
        print()
    raise SystemExit

if os.path.exists(save_file):
    with open(save_file, "r", encoding="utf-8") as f:
        old = json.load(f)
    first_run = False
else:
    old = {"attendance": {}, "marks": {}}
    first_run = True

messages = []

if not first_run:
    for code, new in new_att.items():
        before = old["attendance"].get(code)
        if before is not None and before != new:
            messages.append(
                "Attendance - " + course_label(code) + "\n"
                + "   Percentage: " + before["percent"] + "% to " + new["percent"] + "%\n"
                + "   Absent: " + str(before["absent"]) + " to " + str(new["absent"]) + "\n"
                + "   Lectures: " + str(before["lectures"]) + " to " + str(new["lectures"])
            )

    for key, new_rows in new_marks.items():
        before = old["marks"].get(key)
        label = course_label(key.split(" | ")[0])
        if before is None:
            if len(new_rows) > 1:
                messages.append("New marks - " + label + "\n" + describe(key, new_rows))
        elif my_part(before) != my_part(new_rows):
            messages.append("Marks updated - " + label + "\n" + describe(key, new_rows))

saved = {
    "attendance": {**old["attendance"], **new_att},
    "marks": {**old["marks"], **new_marks},
}
with open(save_file, "w", encoding="utf-8") as f:
    json.dump(saved, f)

if first_run:
    notify("FLEX bot is set up. From now on it will tell you when attendance or marks change.", "FLEX bot")
    print("First run. Saved today's numbers and sent a message.")
elif messages:
    notify("\n\n".join(messages))
    print("UPDATES FOUND:")
    for m in messages:
        print(m)
        print()
else:
    print("No updates today.")