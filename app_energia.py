import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import tempfile
import os
from datetime import datetime

# --- 1. CONFIGURAÇÕES VISUAIS ---
st.set_page_config(page_title="Simulador Comercial", page_icon="☀️", layout="centered")

# PALETA ENERGISA
BG_COLOR = "#FFFFFF"         # Fundo Branco
PRIMARY_ORANGE = "#F37021"   # Laranja Energisa
SECONDARY_BLUE = "#005596"   # Azul Energisa
TEXT_COLOR = "#334155"
SUCCESS_GREEN = "#28a745"

# LINK DA LOGO ENERGISA (Enviado pelo usuário)
LOGO_URL = "https://i.postimg.cc/K80nPvHc/Energisa-svg-2-removebg-preview.png"

# Ícones Icons8 (Links diretos para PNG branco)
ICON_SOLAR = "https://img.icons8.com/ios-filled/50/ffffff/solar-panel.png"
ICON_PIGGY = "https://img.icons8.com/ios-filled/50/ffffff/money-box.png"
ICON_BULB =  "https://img.icons8.com/ios-filled/50/ffffff/light-on.png"
ICON_PLANT = "https://img.icons8.com/ios-filled/50/ffffff/potted-plant.png"
ICON_FILE =  "https://img.icons8.com/ios-filled/50/ffffff/checked--v1.png"

ICONS_LIST = [ICON_SOLAR, ICON_PIGGY, ICON_BULB, ICON_PLANT, ICON_FILE]
ICONS_FALLBACK = ["S", "$", "!", "Y", "V"] 

PDF_CYAN = (0, 85, 150); PDF_LIME = (195, 213, 0); PDF_ORANGE = (243, 112, 33)

def fmt_currency(val): return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_number(val): return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# CSS Reforçado com Cores Energisa
st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_COLOR}; }}
    h1, h2, h3, h4, p, div, span, label, li {{ color: {TEXT_COLOR} !important; font-family: sans-serif; }}
    .stTextInput input, .stNumberInput input, .stSelectbox div {{ color: {TEXT_COLOR} !important; background-color: #f8fafc !important; border: 1px solid #e2e8f0 !important; }}
    
    /* Títulos em Azul Energisa */
    h1, h2, h3, .slide-title {{ color: {SECONDARY_BLUE} !important; }}

    div.stButton > button {{ 
        background-color: {PRIMARY_ORANGE} !important; color: #ffffff !important; 
        border-radius: 8px; height: 50px; font-weight: bold; text-transform: uppercase; border: none; width: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    div.stButton > button p {{ color: #ffffff !important; }}
    
    .card-result {{ padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); background-color: white; }}
    .card-orange {{ border-left: 5px solid {PRIMARY_ORANGE}; }}
    .card-blue {{ border-left: 5px solid {SECONDARY_BLUE}; }}
    
    /* Card Laranja para Destaque de Economia */
    .card-green {{ background-color: {PRIMARY_ORANGE} !important; }}
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
    
    if kwh_total < residuo: kwh_re, kwh_res = 0, kwh_total
    else: kwh_re, kwh_res = kwh_total - residuo, residuo

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

        safe_image(LOGO_URL, 10, 5, 45)

    def footer(self):
        self.set_y(-12); self.set_font('Arial', 'I', 6); self.set_text_color(150); self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def criar_pdf_visual_final(d, nome, cidade, desconto):
    pdf = PDFOficial(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Barra Energisa (Laranja)
    pdf.set_y(30); pdf.set_fill_color(*PDF_ORANGE); pdf.rect(0, 30, 210, 8, 'F')
    pdf.set_font("Arial", "B", 10); pdf.set_text_color(255); pdf.cell(0, 8, "Economia Energisa Solar - Mato Grosso", 0, 1, 'C')
    
    # Ícones
    pdf.ln(3); pdf.set_font("Arial", "B", 10); pdf.set_text_color(*PDF_CYAN)
    pdf.cell(0, 6, "Principais Beneficios:", 0, 1, 'C')
    y_icons = pdf.get_y() + 2; centers = [25, 65, 105, 145, 185]
    txts = ["Sem instalacao", "Sem manutencao", "Economia real", "Energia limpa", "Sem fidelidade"]
    
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

    # Titulo e Dados
    yp = pdf.get_y() + 15; pdf.set_xy(0, yp); pdf.set_font("Arial", "B", 12); pdf.set_text_color(*PDF_CYAN); pdf.cell(0, 8, "Proposta Comercial de Geracao Compartilhada", 0, 1, 'C')
    yb = pdf.get_y() + 2; pdf.set_draw_color(*PDF_CYAN); pdf.set_line_width(0.5); pdf.rect(13, yb, 184, 12)
    pdf.set_xy(15, yb + 3); pdf.set_font("Arial", "", 9); pdf.set_text_color(*PDF_CYAN); pdf.cell(40, 5, "Fatura Energisa Mato Grosso", 0, 1)

    # Cards de Resumo no PDF
    yc = yb + 16; wc = 60; hc = 28; xc = 13
    pdf.set_draw_color(*PDF_ORANGE); pdf.set_line_width(1); pdf.rect(xc, yc, wc, hc)
    pdf.set_xy(xc, yc + 3); pdf.set_font("Arial", "B", 9); pdf.set_text_color(*PDF_ORANGE); pdf.cell(wc, 5, "Media Atual (R$)", 0, 2, 'C')
    pdf.ln(2); pdf.set_font("Arial", "B", 14); pdf.set_text_color(50); pdf.cell(wc, 6, fmt_currency(d['total_atual']), 0, 0, 'C')
    
    xc += wc + 2; pdf.set_draw_color(*PDF_LIME); pdf.rect(xc, yc, wc, hc)
    pdf.set_xy(xc, yc + 3); pdf.set_font("Arial", "B", 9); pdf.set_text_color(*PDF_LIME); pdf.cell(wc, 5, "Economia Projetada", 0, 2, 'C')
    pdf.set_font("Arial", "", 8); pdf.set_text_color(50); pdf.cell(wc, 5, f"Desconto: {desconto:.1f}%", 0, 2, 'C')
    
    xc += wc + 2; pdf.set_draw_color(*PDF_CYAN); pdf.rect(xc, yc, wc, hc)
    pdf.set_xy(xc, yc + 3); pdf.set_font("Arial", "B", 9); pdf.set_text_color(*PDF_CYAN); pdf.cell(wc, 5, "Econ. Anual", 0, 2, 'C')
    pdf.ln(4); pdf.set_x(xc); pdf.set_font("Arial", "B", 14); pdf.set_text_color(50); pdf.cell(wc, 8, fmt_currency(d['econ_ano']), 0, 0, 'C')

    # Footer
    pdf.set_y(-30); pdf.set_font("Arial", "B", 8); pdf.set_text_color(*PDF_CYAN)
    pdf.cell(0, 4, f"Cliente: {nome.upper()} | Cidade: {cidade.upper()} / MS", 0, 1, 'C')
    pdf.set_font("Arial", "I", 8); pdf.set_text_color(50); pdf.cell(0, 4, "Validade da proposta: 10 dias.", 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFACE ---
st.image(LOGO_URL, width=220)
st.title("Simulador Comercial")
st.write("---")

with st.container():
    st.markdown("### 📝 Dados do Cliente")
    c1, c2, c3 = st.columns(3)
    nome = c1.text_input("Nome Completo", value="")
    cidade = c2.text_input("Cidade", value="")
    tipo = c3.radio("Rede", ["Trifásico", "Bifásico", "Monofásico"], horizontal=True)
    
    st.markdown("### ⚡ Dados da Fatura")
    c4, c5 = st.columns(2)
    kwh = c4.number_input("Consumo (kWh)", min_value=0.0, value=None, placeholder="kWh...")
    val_unit = c5.number_input("Tarifa (R$)", min_value=0.0, value=1.1540, format="%.4f")
    c6, c7, c8 = st.columns(3)
    ban = c6.number_input("Bandeiras (R$)", min_value=0.0, value=None)
    ilum = c7.number_input("Ilum. (R$)", min_value=0.0, value=None)
    desc = c8.number_input("Desconto (%)", value=20.0, step=0.5)

    st.write("")
    if st.button("CALCULAR PROPOSTA", use_container_width=True):
        if kwh is not None:
            res = calcular(kwh, val_unit, tipo, ban, ilum, desc)
            st.write("---")
            st.markdown("### 📊 Resultado")
            
            st.markdown(f"""
            <div class="card-result card-blue">
                <div class="label-text">Fatura Atual Energisa</div>
                <div class="big-number">{fmt_currency(res['total_atual'])}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="card-result card-green">
                <div style="font-size: 16px; font-weight:bold; color: white;">💰 Economia Anual Estimada</div>
                <div style="font-size: 32px; font-weight: bold; color: white;">{fmt_currency(res['econ_ano'])}</div>
                <div style="font-size: 16px; color: white;">Mensal: {fmt_currency(res['econ_mes'])}</div>
            </div>
            """, unsafe_allow_html=True)

            pdf_bytes = criar_pdf_visual_final(res, nome, cidade, desc)
            st.download_button(label="⬇️ BAIXAR PROPOSTA EM PDF", data=pdf_bytes, file_name=f"Proposta_Energisa_{nome}.pdf", mime="application/pdf", use_container_width=True)

O código está finalizado com a sua logo e as cores da Energisa! Pode subir para o GitHub e testar. Se precisar de qualquer outro ajuste fino, é só me chamar.
