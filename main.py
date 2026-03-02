import os, json, zlib, requests, streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# ---------------- ENV ----------------
load_dotenv()

SAMPLE_SRS = """An ecommerce system has Users, Products, Orders and Payments.
A User can place many Orders.
An Order contains order_id, order_date and has multiple Products (through OrderItem).
A Product has id, name, price.
Payment belongs to an Order and stores amount and payment_date."""

# ---------------- LLM ----------------
llm = ChatGroq(model="llama-3.3-70b-versatile")
prompt = PromptTemplate.from_template(
    """You convert software requirements into PlantUML class diagram BODY only.
Rules:
- Output ONLY valid JSON: {{"plantuml":"<uml body>","confidence":0.0}}
- No @startuml/@enduml, no markdown
SRS:
{question}"""
)
chain = prompt | llm

def generate_uml(srs):
    resp = chain.invoke({"question": srs}).content
    data = json.loads(resp)
    return data["plantuml"], data.get("confidence")

# ---------------- PlantUML Server (OFFICIAL ENCODER) ----------------
SERVER = "https://www.plantuml.com/plantuml/png/"

def encode_6bit(b):
    if b < 10: return chr(48 + b)
    b -= 10
    if b < 26: return chr(65 + b)
    b -= 26
    if b < 26: return chr(97 + b)
    b -= 26
    return '-' if b == 0 else '_'

def append_3bytes(b1, b2, b3):
    return (
        encode_6bit(b1 >> 2) +
        encode_6bit(((b1 & 0x3) << 4) | (b2 >> 4)) +
        encode_6bit(((b2 & 0xF) << 2) | (b3 >> 6)) +
        encode_6bit(b3 & 0x3F)
    )

def plantuml_encode(text):
    compressed = zlib.compress(text.encode("utf-8"))[2:-4]
    res = ""
    for i in range(0, len(compressed), 3):
        b1 = compressed[i]
        b2 = compressed[i+1] if i+1 < len(compressed) else 0
        b3 = compressed[i+2] if i+2 < len(compressed) else 0
        res += append_3bytes(b1, b2, b3)
    return res

def render_uml(uml_body):
    uml_body = uml_body.replace("```", "").strip()
    uml = f"@startuml\n{uml_body}\n@enduml"
    url = SERVER + plantuml_encode(uml)
    r = requests.get(url, timeout=20)
    return (r.content, None) if r.status_code == 200 else (None, f"PlantUML error {r.status_code}")

# ---------------- UI ----------------
st.set_page_config("AI UML Generator", layout="wide")
st.title("AI-based UML Generator — Streamlit + Groq (PlantUML Server)")

if "srs" not in st.session_state: st.session_state.srs = SAMPLE_SRS
if "uml" not in st.session_state: st.session_state.uml = ""

left, right = st.columns(2)

with left:
    srs = st.text_area("Input (SRS / description)", height=280, key="srs")
    if st.button("Generate UML"):
        with st.spinner("Generating UML..."):
            uml, conf = generate_uml(srs)
        st.session_state.uml = uml
        st.success(f"Generated (confidence: {conf})")
        img, err = render_uml(uml)
        if img: st.image(img)
        else: st.error(err); st.code(uml)

with right:
    uml_text = st.text_area("Generated PlantUML (editable)", height=280, key="uml")
    if st.button("Re-render edited PlantUML"):
        img, err = render_uml(uml_text)
        if img: st.image(img)
        else: st.error(err); st.code(uml_text)

st.caption("PlantUML rendered via server (cloud-safe, no Java). Ready for Render deployment.")