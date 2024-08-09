import streamlit as st
from openai import OpenAI
import re
from langdetect import detect

# Initialize OpenAI client
api_key = st.secrets["api"]["key"]

base_urls = "https://integrate.api.nvidia.com/v1"
client = OpenAI(
    base_url=base_urls,
    api_key=api_key
)

def analyze_contract(file_content, language):
    prompt = f"""
    Analyze the following contract in {language} and provide:
    1. Key terms
    2. Potential risks
    3. Optimization suggestions

    Contract:
    {file_content}
    """
    response = client.chat.completions.create(
        model="meta/llama-3.1-405b-instruct",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that analyzes contracts."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )

    return response.choices[0].message.content

def clean_analysis_result(analysis_result):
    unwanted_phrases = ["Here's the analysis of the contract:"]
    for phrase in unwanted_phrases:
        analysis_result = analysis_result.replace(phrase, "")
    return analysis_result.strip()

def extract_sections(analysis_result):
    sections = {
        "Key Terms": "No key terms found.",
        "Potential Risks": "No risks identified.",
        "Optimization Suggestions": "No optimization suggestions found."
    }

    key_terms_match = re.search(r"Key Terms\s*:(.*?)(?:Potential Risks|Optimization Suggestions|$)", analysis_result, re.DOTALL)
    risks_match = re.search(r"Potential Risks\s*:(.*?)(?:Optimization Suggestions|$)", analysis_result, re.DOTALL)
    suggestions_match = re.search(r"Optimization Suggestions\s*:(.*)", analysis_result, re.DOTALL)

    if key_terms_match:
        sections["Key Terms"] = key_terms_match.group(1).strip()
    if risks_match:
        sections["Potential Risks"] = risks_match.group(1).strip()
    if suggestions_match:
        sections["Optimization Suggestions"] = suggestions_match.group(1).strip()

    return sections

# Streamlit app layout
st.set_page_config(page_title="Contract Optimization AI", layout="wide")

st.title("📄 Contract Optimization AI")
st.markdown("Upload your contract for AI-driven analysis, and receive key terms, potential risks, and optimization suggestions.")

# Upload section
with st.container():
    st.markdown("### Upload Your Contract")
    uploaded_file = st.file_uploader("Choose a contract file", type="txt", label_visibility="collapsed")

    if uploaded_file is not None:
        contract_text = uploaded_file.read().decode("utf-8")
        st.write("**File Uploaded:**", uploaded_file.name)

        # Detect language
        language_code = detect(contract_text)
        language_map = {
            'en': 'English',
            'fr': 'French',
            'ar': 'Arabic'
        }
        language = language_map.get(language_code, 'English')  # Default to English if language not mapped

        # Analyze the contract
        with st.spinner('Analyzing contract...'):
            analysis_result = analyze_contract(contract_text, language)
            cleaned_result = clean_analysis_result(analysis_result)

        # Display the results in expanders
        st.markdown("### Analysis Result")

        with st.expander("Key Terms"):
            st.write(extract_sections(cleaned_result).get("Key Terms", "No key terms found."))

        with st.expander("Potential Risks"):
            st.write(extract_sections(cleaned_result).get("Potential Risks", "No risks identified."))

        with st.expander("Optimization Suggestions"):
            st.write(extract_sections(cleaned_result).get("Optimization Suggestions", "No optimization suggestions found."))

        # Full analysis section
        with st.expander("Full Analysis"):
            st.text_area("Full Analysis", value=cleaned_result, height=300)

        # Download button
        download_analysis = st.button("Download Analysis")
        if download_analysis:
            st.download_button(
                label="Click to Download",
                data=cleaned_result,
                file_name="contract_analysis.txt",
                mime="text/plain"
            )
    else:
        st.markdown("_Please upload a contract file to proceed._")
