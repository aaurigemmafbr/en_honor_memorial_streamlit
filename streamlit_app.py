import streamlit as st
import pandas as pd
from datetime import datetime
from en_api import authenticate

# ---------- PASSWORD PROTECTION ----------
def check_password():
    """Simple password check stored in Streamlit secrets"""
    def password_entered():
        if st.session_state["password"] == st.secrets["app"]["password"]:
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("Password incorrect")
        return False
    else:
        return True


# ---------- MAIN APP ----------
if check_password():
    st.set_page_config(page_title="EN Reference Builder", layout="centered")

    st.title("Engaging Networks - Add Honor/Memorial Information to Transaction Report Reference")

    token = st.secrets["en_api"]["token"]

    uploaded_file = st.file_uploader("📁 Upload your CSV", type=["csv"])

    if uploaded_file:
        user_df = pd.read_csv(uploaded_file)
        
        # Drop any completely empty or unnamed columns
        user_df = user_df.loc[:, ~user_df.columns.str.contains("^Unnamed")]
        
        # Ensure 'Campaign Date' exists
        if "Campaign Date" not in user_df.columns:
            st.error("The uploaded CSV must include a 'Campaign Date' column.")
        else:
            # Parse and find min/max date
            user_df["Campaign Date"] = pd.to_datetime(user_df["Campaign Date"], errors="coerce")
            start_date = user_df["Campaign Date"].min()
            end_date = user_df["Campaign Date"].max()

            if pd.isna(start_date) or pd.isna(end_date):
                st.error("No valid dates found in 'Campaign Date' column.")
            else:
                st.info(f"📅 Date range detected: {start_date.date()} → {end_date.date()}")

                start_str = start_date.strftime("%m%d%Y")
                end_str = end_date.strftime("%m%d%Y")

                if st.button("Fetch and Merge EN Data"):
                    with st.spinner("Fetching data from Engaging Networks..."):
                        try:
                            en_df = authenticate(token, start_str, end_str)

                            # Filter for (P)FIM types
                            fim_df = en_df[en_df["Campaign Type"].isin(["FIM", "PFIM"])].copy()

                            # Create Reference column
                            fim_df["Reference"] = fim_df["Campaign Data 9"].str.lower() + " " + fim_df["Campaign Data 11"].astype(str)

                            # Merge with user data on EN Transaction ID
                            if "EN Transaction ID" not in user_df.columns or "EN Transaction ID" not in fim_df.columns:
                                st.error("Both datasets must include an 'EN Transaction ID' column.")
                            else:
                                # Convert both columns to string for consistent merge
                                user_df["EN Transaction ID"] = user_df["EN Transaction ID"].astype(str).str.strip()
                                fim_df["EN Transaction ID"] = fim_df["EN Transaction ID"].astype(str).str.strip()
                            
                                merged_df = pd.merge(
                                    user_df,
                                    fim_df[["EN Transaction ID", "Reference"]],
                                    on="EN Transaction ID",
                                    how="left"
                                )
                            
                                st.success("✅ Reference column added successfully!")
                                st.dataframe(merged_df.head(20))
                            
                                # Allow CSV download
                                csv_bytes = merged_df.to_csv(index=False).encode("utf-8")
                                download_name = "EN_Reference_Added.csv"
                            
                                st.download_button(
                                    label="📥 Download Final CSV",
                                    data=csv_bytes,
                                    file_name=download_name,
                                    mime="text/csv",
                                )

                        except Exception as e:
                            st.error(f"❌ Error fetching or merging data: {e}")
