import cv2
import pytesseract
import pandas as pd
import re
import glob
from datetime import datetime, timedelta

# -------- OCR ----------
def extract_text(image_path):
    img = cv2.imread(image_path)
    text = pytesseract.image_to_string(img)
    return text

# -------- Helpers ----------
def parse_source(text, filename=""):
    s = (text + " " + filename).lower()

    sources = {
        "facebook marketplace": ["facebook marketplace", "fb marketplace"],
        "olx": ["olx"],
        "quikr": ["quikr", "quickr"],
        "99acres": ["99acres", "99 acres"],
        "housing": ["housing.com", "housing "],
        "magicbricks": ["magicbricks", "magic bricks", "magicbricks.com"]
    }
    for label, keys in sources.items():
        if any(k in s for k in keys):
            return label.title()
    # fallback (many screenshots show 99acres)
    return "Unknown"

def parse_age_days(text):
    """
    Convert 'Yesterday', '2 months ago', '1 month ago', '3 weeks ago',
    '2 days ago', '5 hrs ago', 'Today' -> integer days (approx).
    """
    t = text.lower()

    # Direct words
    if "today" in t:
        return 0
    if "yesterday" in t:
        return 1

    # months
    m = re.search(r"(\d+)\s*month", t)
    if m:
        return int(m.group(1)) * 30

    # weeks
    w = re.search(r"(\d+)\s*week", t)
    if w:
        return int(w.group(1)) * 7

    # days
    d = re.search(r"(\d+)\s*day", t)
    if d:
        return int(d.group(1))

    # hours
    h = re.search(r"(\d+)\s*hour|\b(\d+)\s*hr", t)
    if h:
        hours = int(h.group(1) or h.group(2))
        return 0 if hours < 24 else hours // 24

    return None  # unknown

# -------- Parsing lead fields ----------
def parse_lead(text, filename=""):
    name = ""
    location = ""
    flat_type = ""
    budget = ""
    contact = ""
    source = parse_source(text, filename)
    age_days = parse_age_days(text)  # None if not found

    # Name (first line letters)
    name_match = re.search(r"([A-Za-z][A-Za-z ]{1,40})\n", text)
    if name_match:
        name = name_match.group(1).strip()

    # Phone number (10-digit India)
    phone_match = re.search(r"\b[6-9]\d{9}\b", text)
    if phone_match:
        contact = phone_match.group(0)

    # Flat type
    flat_match = re.search(r"(\d+\s*BHK)", text, re.IGNORECASE)
    if flat_match:
        flat_type = flat_match.group(1).upper()

    # Budget (₹ or plain number with commas/decimals)
    budget_match = re.search(r"(₹\s?[\d,.]+|\b\d{1,3}(?:,\d{2,3})+\b)", text)
    if budget_match:
        budget = budget_match.group(1)

    # Location (simple 'in <place>' grab)
    loc_match = re.search(r"\bin\s+([A-Za-z ,\-]+)", text, re.IGNORECASE)
    if loc_match:
        location = loc_match.group(1).strip(" ,")

    return {
        "Name": name,
        "Location": location,
        "Flat Type": flat_type,
        "Budget": budget,
        "Contact Number": contact,
        "Source": source,
        "Lead Age (days)": age_days
    }

# -------- Main ----------
def process_images(image_list, output_file="leads.xlsx"):
    leads = []
    for img in image_list:
        text = extract_text(img)
        lead = parse_lead(text, filename=img)

        # Avoid duplicates by Contact
        if lead["Contact Number"] and lead["Contact Number"] not in [l["Contact Number"] for l in leads]:
            leads.append(lead)

    cols = ["Name", "Location", "Flat Type", "Budget", "Contact Number", "Source", "Lead Age (days)"]
    df = pd.DataFrame(leads, columns=cols)
    df.to_excel(output_file, index=False)
    print("✅ Leads saved:", output_file)

# Example (when running locally)
if __name__ == "__main__":
    images = sorted(glob.glob("leads_imgs/*"))  # folder of screenshots
    process_images(images, "leads.xlsx")
