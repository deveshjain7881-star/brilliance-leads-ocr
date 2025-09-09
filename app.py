import cv2
import pytesseract
import pandas as pd
import re

# OCR से text निकालने वाला function
def extract_text(image_path):
    img = cv2.imread(image_path)
    text = pytesseract.image_to_string(img)
    return text

# Text से साफ-सुथरे leads निकालने वाला function
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

    # Phone number (पहला valid 10 digit)
    phone_match = re.search(r"\b[6-9]\d{9}\b", text)
    if phone_match:
        contact = phone_match.group(0)

    # Flat Type
    flat_match = re.search(r"(\d+\s*BHK)", text, re.IGNORECASE)
    if flat_match:
        flat_type = flat_match.group(1).upper()

    # Budget
    budget_match = re.search(r"₹\s?[\d,.]+\s?[A-Za-z]*", text)
    if budget_match:
        budget = budget_match.group(0)

    # Location (area + city approx)
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
def process_images(image_list, output_file="leads.xlsx"):
    leads = []
    for img in image_list:
        text = extract_text(img)
        lead = parse_lead(text)
        if lead["Contact Number"]:  # Duplicate avoid
            if lead["Contact Number"] not in [l["Contact Number"] for l in leads]:
                leads.append(lead)

    df = pd.DataFrame(leads, columns=["Name", "Location", "Flat Type", "Budget", "Contact Number"])
    df.to_excel(output_file, index=False)
    print(f"✅ Leads saved in {output_file}")

# Example Run
if __name__ == "__main__":
    images = ["ss1.jpg", "ss2.jpg"]  # यहाँ अपने screenshot file names डालना
    process_images(images)
