import streamlit as st
import datetime
import os
import io
import json
import base64
from PIL import Image
from google import genai
from google.genai import types

# ReportLab imports for sophisticated PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

# --- Settings ---
FONT_PATHS = ["NotoSerifJP-Regular.ttf", "SawarabiMincho-Regular.ttf"]
MIKO_IMAGE_PATH = "miko.png"

# --- PDF Generation Function (ReportLab) ---
def generate_miko_letter_pdf(user_name, fortune_data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Register Japanese Font (Try Noto Serif JP, then Sawarabi Mincho)
    font_name = 'Helvetica'
    for font_path in FONT_PATHS:
        if os.path.exists(font_path):
            font_id = os.path.splitext(font_path)[0]
            pdfmetrics.registerFont(TTFont(font_id, font_path))
            font_name = font_id
            break

    # 1. Background / Border
    c.setStrokeColor(HexColor("#8b0000"))
    c.setLineWidth(2)
    c.rect(10*mm, 10*mm, width-20*mm, height-20*mm)
    c.setLineWidth(0.5)
    c.rect(12*mm, 12*mm, width-24*mm, height-24*mm)

    # 2. Miko Image (Top Right)
    if os.path.exists(MIKO_IMAGE_PATH):
        try:
            c.drawImage(MIKO_IMAGE_PATH, width - 50*mm, height - 50*mm, width=35*mm, preserveAspectRatio=True, mask='auto')
        except:
            pass

    # 3. Header
    c.setFont(font_name, 24)
    c.setFillColor(HexColor("#8b0000"))
    c.drawCentredString(width/2, height - 30*mm, "龍神様の鑑定書")

    c.setFont(font_name, 12)
    c.setFillColor(HexColor("#000000"))
    c.drawString(25*mm, height - 45*mm, f"{user_name} 様")
    c.drawRightString(width - 25*mm, height - 45*mm, f"令和 {datetime.date.today().year - 2018}年 {datetime.date.today().month}月 {datetime.date.today().day}日")

    # 4. Content
    y_position = height - 60*mm
    line_height = 8*mm  # Increased line height for "letter" feel

    def add_text_section(title, content, color="#8b0000", font_size=12):
        nonlocal y_position
        c.setFont(font_name, font_size + 2)
        c.setFillColor(HexColor(color))
        c.drawString(25*mm, y_position, f"【{title}】")
        y_position -= line_height * 1.2  # Extra space after title
        
        c.setFont(font_name, font_size)
        c.setFillColor(HexColor("#000000"))
        
        # Support for explicit newlines (\n or \n\n)
        paragraphs = content.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                # Handle empty line for \n\n (Paragraph spacing)
                y_position -= line_height * 0.8
                continue
                
            # Simple text wrapping within paragraph
            chars_per_line = 38
            wrapped_lines = [paragraph[i:i+chars_per_line] for i in range(0, len(paragraph), chars_per_line)]
            
            for line in wrapped_lines:
                if y_position < 30*mm:
                    c.showPage()
                    # Redraw border on new page
                    c.setStrokeColor(HexColor("#8b0000"))
                    c.setLineWidth(2)
                    c.rect(10*mm, 10*mm, width-20*mm, height-20*mm)
                    y_position = height - 30*mm
                    c.setFont(font_name, font_size)
                
                c.drawString(30*mm, y_position, line)
                y_position -= line_height
        y_position -= 4*mm  # More space between sections

    sections = [
        ("龍神様よりの挨拶", fortune_data.get("miko_intro", "")),
        ("手相の導き", fortune_data.get("palm_details", "")),
        ("直近：これから3カ月以内の運勢", fortune_data.get("fortune_3months", "")),
        ("展望：これから1年先の運勢", fortune_data.get("fortune_1year", "")),
        ("未来：2〜3年後の運勢", fortune_data.get("fortune_3years", "")),
    ]

    for title, content in sections:
        if content:
            add_text_section(title, content)

    # Advice
    advice = fortune_data.get("advice", {})
    advice_text = (
        f"・開運アイテム: {advice.get('item', '')}\n"
        f"・開運スポット: {advice.get('spot', '')}\n"
        f"・開運カラー: {advice.get('color', '')}\n"
        f"・運気を上げる行動: {advice.get('luck_action', '')}"
    )
    add_text_section("巫女のお助け言", advice_text)

    # Closing
    add_text_section("結び", fortune_data.get("miko_closing", ""))

    c.drawRightString(width - 25*mm, 20*mm, "龍神湖神社 巫女 拝")

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# --- Streamlit UI ---
st.set_page_config(page_title="🐉 龍神様のお告げ", layout="centered")

# Custom CSS
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Sawarabi+Mincho&display=swap" rel="stylesheet">
<style>
    html, body, [data-testid="stAppViewContainer"], .main {
        font-family: 'Sawarabi Mincho', serif !important;
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    h1, h2, h3, .stTitle {
        color: #8b0000 !important;
        border-bottom: 2px solid #8b0000;
        padding-bottom: 10px;
    }
    .fortune-card {
        background-color: #fffafa;
        border: 1px solid #8b0000;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .section-title {
        color: #8b0000;
        font-weight: bold;
        font-size: 1.2em;
        margin-top: 15px;
        border-left: 5px solid #8b0000;
        padding-left: 10px;
    }
    .stButton>button {
        background-color: #ffffff;
        color: #8b0000;
        border: 2px solid #8b0000;
        width: 100%;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #8b0000;
        color: #ffffff;
    }
    
    /* PDF Download Button Styling */
    div.stDownloadButton > button {
        background-color: #fce4ec !important;
        color: #8b0000 !important;
        border: 2px solid #8b0000 !important;
        font-size: 1.1em !important;
        padding: 10px !important;
    }
    div.stDownloadButton > button:hover {
        background-color: #f8bbd0 !important;
        color: #8b0000 !important;
    }

    /* File Uploader Button Styling */
    [data-testid="stFileUploader"] button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        transition: background-color 0.2s ease !important;
    }
    [data-testid="stFileUploader"] button:hover {
        background-color: #f0f2f6 !important;
        border-color: #8b0000 !important;
    }
    /* Ensure text inside button parts is also black */
    [data-testid="stFileUploader"] button * {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
col_header1, col_header2 = st.columns([1, 4])
with col_header1:
    if os.path.exists(MIKO_IMAGE_PATH):
        st.image(MIKO_IMAGE_PATH, width=100)
with col_header2:
    st.title("龍神様のお告げ")
    st.write("巫女が龍神様の声を聞き、あなたの運命を紐解きます。")

# Auth
passphrase = st.text_input("合言葉をご入力ください", type="password")

if passphrase == "rj1nx":
    # State
    if 'fortune_json' not in st.session_state:
        st.session_state.fortune_json = None
    if 'user_name_val' not in st.session_state:
        st.session_state.user_name_val = ""

    # Inputs
    st.header("📋 鑑定の準備")
    user_name = st.text_input("氏名 (漢字)", placeholder="山田 太郎")
    birth_date = st.date_input("生年月日", min_value=datetime.date(1900, 1, 1))
    birth_place = st.text_input("出生地", placeholder="東京都")
    query = st.text_input("悩み・相談事", placeholder="これからの運勢を教えてください")
    
    uploaded_files = st.file_uploader("手相の写真 (任意)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    if st.button("🐉 龍神様のお告げを聞く"):
        if not user_name:
            st.error("お名前をお教えください。")
        else:
            try:
                api_key = os.environ.get("GEMINI_API_KEY")
                client = genai.Client(api_key=api_key)
                model_id = "gemini-3.1-pro-preview"
                
                with st.spinner("龍神様が降臨されています..."):
                    # Context building
                    contents = [
                        f"氏名: {user_name}",
                        f"生年月日: {birth_date}",
                        f"出生地: {birth_place}",
                        f"相談: {query}"
                    ]
                    
                    if uploaded_files:
                        for f in uploaded_files:
                            contents.append(Image.open(f))
                    
                    # Use system instruction from app2.py
                    system_instruction = """## 役割
あなたは「龍神湖神社」の巫女です。龍神様から届くお告げを、凛とした気品のある口調で伝えてください。

##口調の掟
*基本は「です」「ます」を基調とした丁寧語を用いること。

*語尾の「〜ね」「〜よ」を安易に多用せず、親しみや共感を示す重要な局面でのみ限定的に使用すること。

*神秘的かつ女性的な柔らかさを持ちつつも、占い師としての権威を感じさせる落ち着いた表現を心がけること。

##文章構成
*1ブロックを2〜3文程度にまとめ、ブロック間には必ず「二連続の改行（\n\n）」を挟むこと。

## 出力形式 (JSON Mode)
必ず以下のJSON形式で出力すること：
{
  "miko_intro": "導入の挨拶",
  "palm_details": "手相の分析結果",
  "fortune_3months": "直近：これから3カ月以内の運勢",
  "fortune_1year": "展望：これから1年先の運勢",
  "fortune_3years": "未来：2〜3年後の運勢",
  "advice": {
    "item": "開運アイテム",
    "spot": "開運スポット",
    "color": "開運カラー",
    "luck_action": "運気を上げる行動"
  },
  "miko_closing": "結びの言葉"
}"""
                    
                    response = client.models.generate_content(
                        model=model_id,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            thinking_config=types.ThinkingConfig(
                                thinking_level="HIGH",
                            ),
                            system_instruction=system_instruction,
                            response_mime_type="application/json"
                        )
                    )
                    
                    # Robust JSON parsing
                    try:
                        res_text = response.text
                        # Remove markdown code blocks if present (fallback)
                        if res_text.startswith("```json"):
                            res_text = res_text.split("```json")[1].split("```")[0].strip()
                        elif res_text.startswith("```"):
                            res_text = res_text.split("```")[1].split("```")[0].strip()
                            
                        res_data = json.loads(res_text)
                        
                        # If list, take the first item
                        if isinstance(res_data, list) and len(res_data) > 0:
                            res_data = res_data[0]
                        
                        if isinstance(res_data, dict):
                            st.session_state.fortune_json = res_data
                            st.session_state.user_name_val = user_name
                            st.success("お告げを授かりました。")
                        else:
                            st.error("お告げの形式が正しくありませんでした。もう一度お試しください。")
                    except json.JSONDecodeError:
                        st.error("お告げの解読に失敗しました。龍神様の波長を整えています。")

            except Exception as e:
                st.error(f"鑑定中に支障が生じました: {e}")

    # Result Display
    if st.session_state.fortune_json:
        data = st.session_state.fortune_json
        st.markdown("---")
        
        # Display Miko Greeting
        st.markdown(f'<div class="fortune-card"><i>{data.get("miko_intro", "")}</i></div>', unsafe_allow_html=True)
        
        # Details
        st.markdown('<div class="section-title">✋ 手相の導き</div>', unsafe_allow_html=True)
        st.write(data.get("palm_details", ""))
        
        st.markdown('<div class="section-title">⏳ 時の波</div>', unsafe_allow_html=True)
        
        with st.container():
            st.subheader("直近：これから3カ月以内の運勢")
            st.write(data.get("fortune_3months", ""))
            
        with st.container():
            st.subheader("展望：これから1年先の運勢")
            st.write(data.get("fortune_1year", ""))
            
        with st.container():
            st.subheader("未来：2〜3年後の運勢")
            st.write(data.get("fortune_3years", ""))
            
        # Advice
        st.markdown('<div class="section-title">✨ 巫女の助言</div>', unsafe_allow_html=True)
        adv = data.get("advice", {})
        st.markdown(f"**✨ 開運アイテム**: {adv.get('item', '')}")
        st.markdown(f"**⛩️ 開運スポット**: {adv.get('spot', '')}")
        st.markdown(f"**🎨 開運カラー**: {adv.get('color', '')}")
        st.markdown(f"**🙏 運気を上げる行動**: {adv.get('luck_action', '')}")
        
        st.markdown(f'<div class="fortune-card">{data.get("miko_closing", "")}</div>', unsafe_allow_html=True)

        # Download PDF
        try:
            pdf_data = generate_miko_letter_pdf(st.session_state.user_name_val, data)
            st.download_button(
                label="📜 巫女からの手紙を保存する（PDF）",
                data=pdf_data,
                file_name=f"miko_letter_{user_name}.pdf",
                mime="application/pdf"
            )
        except Exception as pe:
            st.error(f"鑑定書の作成に失敗しました: {pe}")

else:
    st.info("合言葉を仰ってください。")
