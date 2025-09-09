import cv2
import pytesseract
import pandas as pd
import re
from datetime import datetime

# OCR se text nikalne wala function
def extract_text(image_path):
    img = cv2.imread(image_path)
    text = pytesseract.image_to_string(img)
    return text

# Text se leads nikalne wala function
def parse_lead(text):
    name = ""
    location = ""
    flat_type = ""
    budget = ""
    contact = ""

    # Name
    name_match = re.search(r"([A-Za-z ]+)\n", text)
    if name_match:
        name = name_match.group(1).strip()

    # Phone number (valid 10 digit)
    phone_match = re.search(r"\b[6-9]\d{9}\b", text)
    if phone_match:
        contact = phone_match.group(0)

    # Flat Type
    flat_match = re.search(r"(\d+\s*BHK)", text, re.IGNORECASE)
    if flat_match:
        flat_type = flat_match.group(1).upper()

    # Budget
    budget_match = re.search(r"₹?\s?[0-9,]+", text)
    if budget_match:
        budget = budget_match.group(0)

    # Location
    loc_match = re.search(r"in\s+([A-Za-z ,]+)", text, re.IGNORECASE)
    if loc_match:
        location = loc_match.group(1).strip()

    return {
        "Name": name,
        "Location": location,
        "Flat Type": flat_type,
        "Budget": budget,
        "Contact Number": contact
    }

# Main function
def process_images(image_list, output_file="leads.xlsx", source="Unknown", lead_age="Fresh"):
    leads = []
    for img in image_list:
        text = extract_text(img)
        lead = parse_lead(text)
        if lead["Contact Number"] and lead["Contact Number"] not in [l["Contact Number"] for l in leads]:
            lead["Source"] = source
            lead["Lead Age"] = lead_age
            leads.append(lead)

    df = pd.DataFrame(leads, columns=["Name", "Location", "Flat Type", "Budget", "Contact Number", "Source", "Lead Age"])
    df.to_excel(output_file, index=False)
    print(f"✅ Leads saved: {output_file}")

# Example Run
if __name__ == "__main__":
    import glob
    images = sorted(glob.glob("/content/drive/MyDrive/leads_imgs/*.jpg"))
    process_images(images, "/content/drive/MyDrive/leads.xlsx", source="99acres", lead_age="1 Day Old")
