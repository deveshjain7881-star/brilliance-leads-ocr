import cv2
import pytesseract
import pandas as pd
import re

# OCR function
def extract_text(image_path):
    img = cv2.imread(image_path)
    text = pytesseract.image_to_string(img)
    return text

# Parsing function
def parse_lead(text, source="OLX"):
    name = ""
    location = ""
    flat_type = ""
    budget = ""
    contact = ""
    lead_age = ""

    # Name (first line valid word)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        first = lines[0]
        if not re.search(r"owner|posted", first.lower()):
            name = first

    # Phone number (10 digit)
    phone_match = re.search(r"\b[6-9]\d{9}\b", text)
    if phone_match:
        contact = phone_match.group(0)

    # Flat type
    flat_match = re.search(r"(\d+\s?BHK)", text, re.IGNORECASE)
    if flat_match:
        flat_type = flat_match.group(1).upper()

    # Budget
    budget_match = re.search(r"(₹|Rs\.?|INR)\s?[\d,]+", text, re.IGNORECASE)
    if budget_match:
        budget = budget_match.group(0)

    # Location (simple approx)
    loc_match = re.search(r"([A-Za-z ]+,\s?[A-Za-z ]+,\s?[A-Za-z ]+)", text)
    if loc_match:
        location = loc_match.group(1).strip()

    # Lead Age (Posted x days/hours ago)
    age_match = re.search(r"(\d+\s?(days|day|hours|hrs|minutes|min)\s?ago)", text, re.IGNORECASE)
    if age_match:
        lead_age = age_match.group(1)

    return {
        "Name": name,
        "Location": location,
        "Flat Type": flat_type,
        "Budget": budget,
        "Contact Number": contact,
        "Source": source,
        "Lead Age": lead_age
    }

# Process function
def process_images(image_list, output_file="leads.xlsx", source="OLX"):
    leads = []
    for img in image_list:
        text = extract_text(img)
        lead = parse_lead(text, source=source)

        # Duplicate avoid
        if lead["Contact Number"] and lead["Contact Number"] not in [l["Contact Number"] for l in leads]:
            leads.append(lead)

    df = pd.DataFrame(leads, columns=["Name","Location","Flat Type","Budget","Contact Number","Source","Lead Age"])
    df.to_excel(output_file, index=False)
    print(f"✅ Leads saved in {output_file}")
