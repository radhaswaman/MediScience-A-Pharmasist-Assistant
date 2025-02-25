import pytesseract
from PIL import Image
import cv2
import pandas as pd
import re
from fuzzywuzzy import process
import streamlit as st

# ✅ Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# ✅ Load CSV file into DataFrame
inventory_df = pd.read_csv('pharmacy_db.csv')

# --- IMAGE PREPROCESSING ---
def preprocess_image(image_path):
    """Preprocess image for better OCR using OpenCV."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    image = cv2.medianBlur(image, 3)
    return Image.fromarray(image)

# --- OCR FUNCTION ---
def extract_text(image_path):
    """Extract text using pytesseract with optimized preprocessing."""
    img = preprocess_image(image_path)
    text = pytesseract.image_to_string(img, config="--psm 6")
    return text.strip()

# --- MEDICINE MATCHING ---
def match_medicines(prescription_text):
    """Extract medicine names and match with MedicineName column using fuzzy logic."""
    medicine_lines = re.findall(r'([A-Za-z]+)\s*(\d+)?\s*mg?', prescription_text)
    medicine_names = [line[0].strip().lower() for line in medicine_lines]

    matched_medicines = []
    inventory_names = inventory_df['MedicineName'].str.lower().tolist()

    for med_name in medicine_names:
        best_match, score = process.extractOne(med_name, inventory_names)
        if score >= 80:  # ✅ Only append if similarity >= 80%
            matched_row = inventory_df[inventory_df['MedicineName'].str.lower() == best_match].iloc[0]
            matched_medicines.append(matched_row.to_dict())

    return matched_medicines

# --- ORDER GENERATION ---
def generate_order(matched_medicines):
    """Generate final order JSON with user-specified quantities."""
    order_items = []

    for med in matched_medicines:
        medicine_name = med['MedicineName']
        stock = med['QuantityInStock']
        price = med['PriceInRupees']

        quantity_needed = st.number_input(f"Enter quantity needed for {medicine_name} (Available: {stock}): ", 
                                          min_value=1, max_value=stock, key=medicine_name)

        if stock >= quantity_needed:
            total_price = quantity_needed * price
            order_items.append({'Medicine': medicine_name, 'Quantity': quantity_needed, 'TotalPrice': total_price})
        else:
            st.warning(f"⚠ Only {stock} units available for {medicine_name}. Adding available quantity to order.")
            total_price = stock * price
            order_items.append({'Medicine': medicine_name, 'Quantity': stock, 'TotalPrice': total_price})

    # ✅ Display Final Order
    st.subheader("🚀 Final Order:")
    for item in order_items:
        st.write(f"- {item['Medicine']}: {item['Quantity']} units (₹{item['TotalPrice']:.2f})")

    return {'OrderItems': order_items}

# --- STREAMLIT UI ---
def main():
    # ✅ Set Streamlit page config
    st.set_page_config(page_title="Pharmacist's Assistant AI", page_icon="💊", layout="wide")
    
    # ✅ Page Title and Styling
    st.title("Pharmacist's Assistant AI 💊")
    st.markdown("""
        <style>
        .title {
            color: #00796B;
            font-size: 36px;
            font-family: 'Arial', sans-serif;
        }
        .description {
            font-size: 18px;
            color: #004D40;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # ✅ Upload Prescription Image
    st.header("📸 Upload Prescription Image")
    uploaded_image = st.file_uploader("Choose an image of the prescription", type=["jpg", "jpeg", "png"])

    if uploaded_image is not None:
        # Save the uploaded file to a local path
        image_path = f"temp_{uploaded_image.name}"
        with open(image_path, "wb") as f:
            f.write(uploaded_image.getbuffer())
        
        # ✅ Display uploaded image
        st.image(uploaded_image, caption="Uploaded Prescription", use_container_width=True)

        # ✅ Extract text from the prescription image
        st.write("📸 Extracting text from the image...")
        prescription_text = extract_text(image_path)
        st.text_area("Extracted Text", prescription_text, height=300, max_chars=1500)

        # ✅ Match medicines and generate order
        st.write("🔎 Matching medicines with pharmacy inventory...")
        matched_medicines = match_medicines(prescription_text)

        if matched_medicines:
            st.write("📦 Generating your final order...")
            final_order = generate_order(matched_medicines)
            st.json(final_order)
        else:
            st.warning("⚠ No medicines matched from the prescription.")

# ✅ Make sure this is the correct entry point
if __name__ == "__main__":
    main()
 
