import streamlit as st
import requests

st.set_page_config(page_title="Sales Inbox → CRM Agent", layout="wide")
st.title("Sales Inbox → CRM Agent (Day 2 placeholder)")

api = st.sidebar.text_input("API base", "http://localhost:8000")

if st.button("Health checks"):
    response = requests.get(f"{api}/health")
    if response.status_code == 200:
        st.success("API is healthy")
    else:
        st.error("API is not healthy")

if st.button("List emails"):
    r = requests.get(f"{api}/emails", timeout=10)
    if r.ok:
        st.write(r.json()[:5])
    else:
        st.error(r.text)

col1, col2, col3, col4, col5 = st.columns(5)
if st.button("Metrics"):
    r = requests.get(f"{api}/metrics", timeout=10)
    if r.ok:
        metrics = r.json()
        col1.metric("Emails processed", metrics.get("processed_emails", 0))
        col2.metric("Total tokens", metrics.get("total_tokens", 0))
        col3.metric("Total cost (USD)", f"${metrics.get('total_cost', 0.0):.4f}")
        col4.metric("Latency p95 (ms)", f"{metrics.get('classify', {}).get('p_95', 0.0):.1f}")
        col5.metric("Latency p95 (Tools)", f"{metrics.get('tools_upsert', {}).get('p_95', 0.0):.1f}")
    else:
        st.error(r.text)