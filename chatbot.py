import os
import cv2
import numpy as np
import pytesseract
import streamlit as st
from PIL import Image
import google.generativeai as genai
import json

# Set up Gemini API key
os.environ["GOOGLE_API_KEY"] = "YOUR API KEY"   //REPLACE WITH YOUR OWN GEMINI API KEY
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
 
# Streamlit page configuration
st.set_page_config(page_title="Prescription Chat App", layout="wide")
st.title("💊 PHARMACY ASSISTANT CHATBOT")
st.subheader("Ask your medicinal queries here, im here to guide you!")

# Image preprocessing for OCR
def preprocess_image(image):
    """Enhances image for OCR by removing noise and increasing contrast."""
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    _, img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(img)

# Extract text from image using OCR
def extract_text_from_image(image):
    """Extracts text from a prescription image using Tesseract OCR."""
    try:
        processed_img = preprocess_image(image)
        text = pytesseract.image_to_string(processed_img, config="--psm 6 -l eng")
        return text.strip()
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return ""

# Sidebar for file upload
st.sidebar.header("Upload Prescription Image")
uploaded_file = st.sidebar.file_uploader(
    "Choose a prescription image (JPG, PNG, BMP)", type=['jpg', 'jpeg', 'png', 'bmp']
)

# Initialize extracted text variable
extracted_text = ""

if uploaded_file:
    with st.spinner("Processing prescription image..."):
        try:
            extracted_text = extract_text_from_image(Image.open(uploaded_file))
            if extracted_text:
                st.sidebar.success("✅ Text extracted successfully!")
            else:
                st.sidebar.error("⚠ No valid text extracted. Try a clearer image.")
        except Exception as e:
            st.sidebar.error(f"Error: {str(e)}")

# Display extracted text
if extracted_text:
    st.subheader("Extracted Prescription Text:")
    st.text_area("OCR Output", extracted_text, height=150)

    # Convert extracted text into JSON format
    prescription_data = {"prescription": extracted_text}
    prescription_json = json.dumps(prescription_data, indent=4)

    # Chat input
    user_question = st.text_input("Ask a question about your prescription:")

    if user_question:
        with st.spinner("Generating response..."):
            try:
                # Call Gemini AI
                model = genai.GenerativeModel("gemini-pro")
                prompt = (
                    f"You are an AI pharmacist assistant. Analyze the following prescription provided as JSON:\n"
                    f"{prescription_json}\n\n"
                    f"Answer the user's question clearly and concisely: {user_question}"
                )
                response = model.generate_content(prompt)

                # Display response
                st.subheader("🤖 Assistant's Response:")
                st.write(response.text)

            except Exception as e:
                st.error(f"Error generating response: {str(e)}")

else:
    st.info("Please upload a prescription image to extract text.")
