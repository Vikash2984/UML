import os, json, zlib, requests, streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# -------- ENV --------
load_dotenv()

SAMPLE_SRS = """An ecommerce system has Users, Products, Orders and Payments.
A User can place many Orders.
An Order contains order_id, order_date and has multiple Products (through OrderItem).
A Product has id, name, price.
Payment belongs to an Order and stores amount and payment_date."""

# -------- LLM --------
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
    data = json.loads(chain.invoke({"question": srs}).content)
    return data["plantuml"], data.get("confidence")

# -------- PlantUML Server --------
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
        encode_6bit(((b1 & 3) << 4) | (b2 >> 4)) +
        encode_6bit(((b2 & 15) << 2) | (b3 >> 6)) +
        encode_6bit(b3 & 63)
    )

def plantuml_encode(text):
    c = zlib.compress(text.encode())[2:-4]
    return "".join(
        append_3bytes(
            c[i],
            c[i+1] if i+1 < len(c) else 0,
            c[i+2] if i+2 < len(c) else 0
        )
        for i in range(0, len(c), 3)
    )

def render_uml(body):
    uml = f"@startuml\n{body.replace('```','').strip()}\n@enduml"
    r = requests.get(SERVER + plantuml_encode(uml), timeout=20)
    return (r.content, None) if r.status_code == 200 else (None, f"PlantUML error {r.status_code}")

# -------- UI --------
st.set_page_config(page_title="AI UML Generator | CA2", layout="wide")

st.markdown(
    """
    <div style="line-height:1.4">
        <div style="font-size:1.5em; font-weight:bold;">
            📘 CA2 Assignment | AI-Based UML Diagram Generator
        </div>
        Vikash Kumar Pandey | Roll: 10830622025 | Sem: 8th | AIML<br>
        Software Engineering (OECAIML 801C)
    </div>
    <hr style="margin-top:6px; margin-bottom:10px;">
    """,
    unsafe_allow_html=True
)

if "srs" not in st.session_state: st.session_state.srs = SAMPLE_SRS
if "uml" not in st.session_state: st.session_state.uml = ""

left, right = st.columns(2)

with left:
    srs = st.text_area("Input (description)", height=280, key="srs")
    if st.button("Generate UML"):
        with st.spinner("Generating UML..."):
            uml, conf = generate_uml(srs)
        st.session_state.uml = uml
        st.success(f"Generated (confidence: {conf})")
        img, err = render_uml(uml)
        st.image(img) if img else (st.error(err), st.code(uml))

with right:
    uml_text = st.text_area("Generated PlantUML (editable)", height=280, key="uml")
    if st.button("Re-render edited PlantUML"):
        img, err = render_uml(uml_text)
        st.image(img) if img else (st.error(err), st.code(uml_text))

st.caption("PlantUML rendered via server (cloud-safe). Ready for Render & Railway deployment.")
