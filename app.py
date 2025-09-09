import cv2
import pytesseract
from PIL import Image
import pandas as pd
import re, glob, os, datetime, argparse

# ---------- OCR helpers ----------
def _read_image_as_pil(image_path):
    img = cv2.imread(image_path)            # OpenCV BGR
    if img is None:
        return None
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)              # PIL Image
    return pil

def extract_text(image_path):
    pil = _read_image_as_pil(image_path)
    if pil is None:
        return ""
    return pytesseract.image_to_string(pil)

# ---------- Parsing helpers ----------
CITIES = [
    "Pune","Mumbai","Thane","Navi Mumbai","Nagpur","Nashik","Aurangabad",
    "Noida","Delhi","Gurgaon","Talegaon","Wagholi","Parel","Andheri",
    "Kalyan","Vasai","Vihar","Peth","Dabhade"
]
LOC_KEYWORDS = r"(Society|Galaxy|Apartment|Residency|Complex|Nagar|Vihar|Peth|Colony|CHS|Heights|Greens|City|Garden|Enclave|Phase|Road)"

FLAT_PAT   = re.compile(r"(\d+\s*BHK)", re.I)
PHONE_PAT  = re.compile(r"\b(?:\+?91[- ]?)?[6-9]\d{9}\b")
BUDGET_PAT = re.compile(r"₹\s?[\d,\.]+|Rs\.?\s?[\d,\.]+", re.I)

def guess_name(lines, phone):
    # फोन के ठीक ऊपर/पास की लाइन से नाम उठाने की कोशिश
    try:
        idx = next(i for i,l in enumerate(lines) if phone and phone in re.sub(r"\D","", l))
        for j in range(idx-1, max(-1, idx-6), -1):
            w = re.sub(r'[^A-Za-z ]+', '', lines[j]).strip()
            if 2 <= len(w) <= 30 and not any(k in w.lower() for k in ['chat','whatsapp','view number','owner','dealer','properties','property']):
                return w
    except StopIteration:
        pass
    # fallback: ऊपर की कोई साफ-सुथरी टेक्स्ट लाइन
    for l in lines[:6]:
        w = re.sub(r'[^A-Za-z ]+','', l).strip()
        if 2 <= len(w) <= 30:
            return w
    return ""

def parse_location(lines):
    picks = []
    for l in lines:
        if any(city.lower() in l.lower() for city in CITIES) or re.search(LOC_KEYWORDS, l, re.I):
            cleaned = re.sub(r"\s{2,}"," ", l).strip()
            if cleaned and cleaned not in picks:
                picks.append(cleaned)
    return ", ".join(picks[:2])  # ज़्यादा लंबा न हो, 2 टुकड़े काफी

def parse_date_from_filename(path):
    # Screenshot_20250909-180611.jpg → 2025-09-09
    m = re.search(r'(\d{8})[-_]', os.path.basename(path))
    if not m:
        return None
    s = m.group(1)
    try:
        return datetime.date(int(s[0:4]), int(s[4:6]), int(s[6:8]))
    except:
        return None

def parse_one(image_path, source):
    text = extract_text(image_path)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    flat = ""
    m = FLAT_PAT.search(text)
    if m: flat = m.group(1).upper()

    phone = ""
    m = PHONE_PAT.search(text)
    if m: phone = re.sub(r"\D","", m.group(0))[-10:]  # सिर्फ 10 अंकों का

    budget = ""
    m = BUDGET_PAT.search(text)
    if m: budget = m.group(0)

    name = guess_name(lines, phone)
    location = parse_location(lines)

    shot_date = parse_date_from_filename(image_path)
    age = ""
    if shot_date:
        age = (datetime.date.today() - shot_date).days

    return {
        "Name": name,
        "Location": location,
        "Flat Type": flat,
        "Budget": budget,
        "Contact Number": phone,
        "Source": source,
        "Lead Age (days)": age
    }

def process_folder(img_dir, output, source):
    files = sorted(glob.glob(os.path.join(img_dir, "*")))
    rows, seen = [], set()
    for f in files:
        lead = parse_one(f, source)
        # डुप्लिकेट नंबर हटाओ
        if lead["Contact Number"] and lead["Contact Number"] not in seen:
            rows.append(lead)
            seen.add(lead["Contact Number"])

    df = pd.DataFrame(
        rows,
        columns=["Name","Location","Flat Type","Budget","Contact Number","Source","Lead Age (days)"]
    )
    df.to_excel(output, index=False)
    print("Leads saved:", output)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--img_dir", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--source", default="")
    args = ap.parse_args()
    process_folder(args.img_dir, args.output, args.source)
