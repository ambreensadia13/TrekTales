import streamlit as st

st.set_page_config(
    page_title="TrekTales AI",
    page_icon="🥾",
    layout="wide"
)

st.title("🥾 TrekTales AI")

st.success("STREAMLIT IS WORKING")

st.write("The TrekTales Streamlit application has started successfully.")

st.markdown("---")

st.header("Deployment Test")

st.write("If you can see this page, Streamlit Cloud is working correctly.")

st.info(
    "FAISS and Groq will be connected after this deployment test passes."
)
