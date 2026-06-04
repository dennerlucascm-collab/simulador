import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import tempfile
import os
from datetime import datetime

# --- 1. CONFIGURAÇÕES VISUAIS ---
st.set_page_config(page_title="Simulador Comercial", page_icon="☀️", layout="centered")

# Cores solicitadas: fundo marronzinho, azul principal e detalhe laranja Energisa
BG_COLOR = "#fdf1db"
PRIMARY_BLUE = "#005596" # Azul Energisa
ECONOMY_BLUE = "#4a90e2" 
ALERT_ORANGE = "#F37021" # Laranja Energisa
SUCCESS_GREEN = "#28a745"

# Logo Oficial Energisa (Link atualizado)
LOGO_URL = "https://i.postimg.cc/K80nPvHc/Energisa-svg-2-removebg-preview.png"

# Ícones Icons8 (PNG branco)
ICON_SOLAR = "https://img.icons8.com/ios-filled/50/ffffff/solar-panel.png"
ICON_PIGGY = "https://img.icons8.com/ios-filled/50/ffffff/money-box.png"
ICON_BULB =  "https://img.icons8.com/ios-filled/50/ffffff/light-on.png"
ICON_PLANT = "https://img.icons8.com/ios-filled/50/ffffff/potted-plant.png"
ICON_FILE =  "https://img.icons8.com/ios-filled/50/ffffff/checked--v1.png"

ICONS_LIST = [ICON_SOLAR, ICON_PIGGY, ICON_BULB, ICON_PLANT, ICON_FILE]
ICONS_FALLBACK = ["S", "$", "!", "Y", "V"]

# Cores para o PDF
PDF_CYAN = (0, 85, 150)
PDF_LIME = (195, 213, 0)
PDF_ORANGE = (243, 112, 33)

def fmt_currency(val): return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_number(val): return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# CSS Reforçado com fundo marronzinho e cores Energisa
st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_COLOR}; }}
    h1, h2, h3, h4, p, div, span, label, li {{ color: {PRIMARY_BLUE} !important; font-family: sans-serif; }}
    .stTextInput input, .stNumberInput input, .stSelectbox div {{ color: {PRIMARY_BLUE} !important; background-color: #ffffff !important; }}
    
    div.stButton > button {{ 
        background-color: {PRIMARY_BLUE} !important; color: #ffffff !important; 
        border-radius: 8px; height: 50px; font-weight: bold; text-transform: uppercase; border: none; width: 100%;
    }}
    div.stButton > button p {{ color: #ffffff !important; }}
    
    .card-result {{ padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); background-color: white; }}
    .card-orange {{ border-left: 5px solid {ALERT_ORANGE}; }}
    .card-blue {{ border-left: 5px solid {PRIMARY_BLUE}; }}
    .card-light-blue {{ border-left: 5px solid {ECONOMY_BLUE}; }}
    
    .card-green {{ background-color: {SUCCESS_GREEN} !important; }}
    .card-green div, .card-green h2, .card-green p, .card-green span {{ color: #ffffff !important; }}
    
    .big-number {{ font-size: 20px; font-weight: bold; margin: 5px 0; color: #333 !important; }}
    .label-text {{ font-size: 12px; font-weight: bold; text-transform: uppercase; color: #666 !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. CÁLCULO ---
def calcular(kwh_total, valor_unit, tipo, bandeira, ilum, desc):
    kwh_total = kwh_total if kwh_total else 0.0
    valor_unit = valor_unit if valor_unit else 0.0
    bandeira = bandeira if bandeira else 0.0
    ilum = ilum if ilum else 0.0
    desc = desc if desc else 0.0

    if tipo == "Monofásico": residuo = 30
    elif tipo == "Bifásico": residuo = 50
    else: residuo = 100 
    
    kwh_re = max(0, kwh_total - residuo)
    kwh_res = min(kwh_total, residuo)

    qtd_placas = int(kwh_re / 52)
    if qtd_placas < 1 and kwh_re > 0: qtd_placas = 1

    total_atual = (kwh_total * valor_unit) + bandeira + ilum
    fat_en = (kwh_res * valor_unit) + bandeira + ilum
    val_re_unit = valor_unit * (1 - (desc/100))
    fat_re = kwh_re * val_re_unit
    total_novo = fat_en + fat_re
    econ_mes = total_atual - total_novo
    
    return {
        "total_atual": total_atual, "fat_en": fat_en, "fat_re": fat_re,
        "total_novo": total_novo, "econ_mes": econ_mes, "econ_ano": econ_mes * 12,
        "kwh_re": kwh_re, "qtd_placas": qtd_placas
    }

# --- 3. PDF ---
class PDFOficial(FPDF):
    def header(self):
        self.set_fill_color(255, 255, 255); self.rect(0, 0, 210, 30, 'F')
        headers = {'User-Agent': 'Mozilla/5.0'}
        def safe_image(url, x, y, w):
            try:
                r = requests.get(url, headers=headers, timeout=5)
                if r.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(r.content); tmp_name = tmp.name
                    self.image(tmp_name, x, y, w); os.unlink(tmp_name)
            except: pass
        safe_image(LOGO_URL, 10, 5, 35)

    def footer(self):
        self.set_y(-12); self.set_font('Arial', 'I', 6); self.set_text_color(150); self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def criar_pdf_visual_final(d, nome, cidade, desconto, uc):
    pdf = PDFOficial(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    pdf.set_y(30); pdf.set_fill_color(*PDF_LIME); pdf.rect(0, 30, 210, 8, 'F')
    pdf.set_font("Arial", "B", 10); pdf.set_text_color(255); pdf.cell(0, 8, "Energia solar sem investimento? Saiba como isso e possivel.", 0, 1, 'C')
    
    pdf.ln(3); pdf.set_font("Arial", "B", 10); pdf.set_text_color(*PDF_CYAN)
    pdf.cell(0, 6, "Conheca os beneficios da Geracao Compartilhada:", 0, 1, 'C')
    y_icons = pdf.get_y() + 2; centers = [25, 65, 105, 145, 185]
    txts = ["Sem instalacao\nde equipamentos", "Sem preocupacao\ncom manutencao", "Economia na\nconta de energia", "Energia limpa\ne sustentavel", "Sem fidelidade"]
    
    pdf.set_font("Arial", "", 7); pdf.set_text_color(80)
    for i, t in enumerate(txts):
        cx = centers[i]
        pdf.set_fill_color(*PDF_CYAN); pdf.ellipse(cx-8, y_icons, 16, 16, 'F')
        success = False
        try:
            r = requests.get(ICONS_LIST[i], headers=headers, timeout=4)
            if r.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(r.content); tmp_name = tmp.name
                pdf.image(tmp_name, cx-4, y_icons+4, 8, 8); os.unlink(tmp_name)
                success = True
        except: pass
        if not success:
            pdf.set_xy(cx-8, y_icons+4); pdf.set_text_color(255); pdf.set_font("Arial", "B", 10)
            pdf.cell(16, 8, ICONS_FALLBACK[i], 0, 0, 'C'); pdf.set_text_color(80); pdf.set_font("Arial", "", 7)
        pdf.set_xy(cx-15, y_icons + 18); pdf.multi_cell(30, 3, t, 0, 'C')

    y_steps = y_icons + 35; pdf.set_xy(0, y_steps - 6); pdf.set_font("Arial", "B", 10); pdf.set_text_color(*PDF_CYAN); pdf.cell(0, 6, "Veja como funciona:", 0, 1, 'C')
    steps = ["1. Instalamos os paineis", "2. Geramos energia limpa", "3. Voce adquire sua cota", "4. O credito vira desconto"]
    bw = 42; sx = 13; gp = 4; pdf.set_font("Arial", "", 8); pdf.set_text_color(255)
    for i, t in enumerate(steps):
        cx = sx + (i * (bw + gp)); pdf.set_fill_color(*PDF_CYAN); pdf.rect(cx, y_steps, bw, 22, 'F')
        pdf.set_xy(cx + 2, y_steps + 3); pdf.multi_cell(bw - 4, 3.5, t, 0, 'C')

    yp = y_steps + 30; pdf.set_xy(0, yp); pdf.set_font("Arial", "B", 12); pdf.set_text_color(*PDF_CYAN); pdf.cell(0, 8, "Proposta Comercial de Locacao de Usina Fotovoltaica", 0, 1, 'C')
    yb = pdf.get_y() + 2; pdf.set_draw_color(*PDF_CYAN); pdf.set_line_width(0.5); pdf.rect(13, yb, 184, 12)
    pdf.set_xy(15, yb + 3); pdf.set_font("Arial", "", 9); pdf.set_text_color(*PDF_CYAN)
    
    # Exibindo o número da UC preenchido
    texto_uc = f"N cliente {uc}" if uc else "N cliente"
    pdf.cell(40, 5, texto_uc, 0, 1)

    yc = yb + 16; wc = 60; hc = 28; xc = 13
    pdf.set_draw_color(*PDF_ORANGE); pdf.set_line_width(1); pdf.rect(xc, yc, wc, hc)
    pdf.set_xy(xc, yc + 3); pdf.set_font("Arial", "B", 9); pdf.set_text_color(*PDF_ORANGE); pdf.cell(wc, 5, "Media* (R$)", 0, 2, 'C')
    pdf.ln(2); pdf.set_font("Arial", "B", 14); pdf.set_text_color(50); pdf.cell(wc, 6, fmt_currency(d['total_atual']), 0, 0, 'C')
    
    xc += wc + 2; pdf.set_draw_color(*PDF_CYAN); pdf.rect(xc, yc, wc, hc)
    pdf.set_xy(xc, yc + 3); pdf.set_font("Arial", "B", 9); pdf.set_text_color(*PDF_CYAN); pdf.cell(wc, 5, "Economia Ofertada", 0, 2, 'C')
    pdf.set_font("Arial", "", 8); pdf.set_text_color(50); pdf.cell(wc, 5, f"Previo: {desconto:.1f}%", 0, 2, 'C')
    
    xc += wc + 2; pdf.set_draw_color(*PDF_CYAN); pdf.rect(xc, yc, wc, hc)
    pdf.set_xy(xc, yc + 3); pdf.set_font("Arial", "B", 9); pdf.set_text_color(*PDF_CYAN); pdf.cell(wc, 5, "Economia Anual Projetada", 0, 2, 'C')
    pdf.ln(4); pdf.set_x(xc); pdf.set_font("Arial", "B", 14); pdf.set_text_color(50); pdf.cell(wc, 8, fmt_currency(d['econ_ano']), 0, 0, 'C')

    pdf.set_y(-30); pdf.set_font("Arial", "B", 8); pdf.set_text_color(*PDF_CYAN)
    pdf.cell(0, 4, f"Cliente: {nome.upper()} | Cidade: {cidade.upper()} / MS", 0, 1, 'C')
    pdf.set_font("Arial", "I", 8); pdf.set_text_color(50); pdf.cell(0, 4, "Validade da proposta: 10 dias.", 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFACE ---
st.image(LOGO_URL, width=150)
st.title("Simulador Comercial")
st.write("---")

with st.container():
    st.markdown("### 1. Dados do Cliente")
    c1, c2, c3 = st.columns(3)
    nome = c1.text_input("Nome", value="")
    cidade = c2.text_input("Cidade", value="")
    tipo = c3.radio("Tipo de Ligação", ["Trifásico", "Bifásico", "Monofásico"], horizontal=True)
    
    st.markdown("### 2. Dados da Fatura")
    c_uc, c4, c5 = st.columns(3)
    uc = c_uc.text_input("UC (Unidade Consumidora)", value="", placeholder="Ex: 1234.56")
    kwh = c4.number_input("Consumo (kWh)", min_value=0.0, value=None, placeholder="kWh...")
    val_unit = c5.number_input("Valor Unitário (R$)", min_value=0.0, value=1.1540, format="%.4f")
    
    c6, c7, c8 = st.columns(3)
    ban = c6.number_input("Bandeiras (R$)", min_value=0.0, value=None)
    ilum = c7.number_input("Ilum. Púb. (R$)", min_value=0.0, value=None)
    desc = c8.number_input("Desconto (%)", value=30.0, step=0.5)

    if st.button("CALCULAR PROPOSTA", use_container_width=True):
        if kwh:
            res = calcular(kwh, val_unit, tipo, ban, ilum, desc)
            st.write("---")
            st.markdown("### 📊 Resultado da Simulação")
            st.markdown(f"""<div class="card-result card-orange"><div class="label-text">1. Fatura Atual Energisa</div><div class="big-number">{fmt_currency(res['total_atual'])}</div></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="card-result card-green"><div style="font-size: 16px; color: white;">💰 Economia Mensal Estimada</div><div style="font-size: 28px; font-weight: bold; color: white;">{fmt_currency(res['econ_mes'])}</div><div style="font-size: 20px; color: white;">Anual: {fmt_currency(res['econ_ano'])}</div></div>""", unsafe_allow_html=True)
            pdf_bytes = criar_pdf_visual_final(res, nome, cidade, desc, uc)
            st.download_button(label="⬇️ BAIXAR PROPOSTA EM PDF", data=pdf_bytes, file_name=f"Proposta_{nome}.pdf", mime="application/pdf", use_container_width=True)
