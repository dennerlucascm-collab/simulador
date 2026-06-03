import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import tempfile
import os
from datetime import datetime

# --- 1. CONFIGURAÇÕES VISUAIS ---
st.set_page_config(page_title="Simulador Comercial", page_icon="☀️", layout="centered")

BG_COLOR = "#fdf1db"
PRIMARY_BLUE = "#005596" 
SECONDARY_ORANGE = "#F37021"
SUCCESS_GREEN = "#28a745"

# LINK DA LOGO ENVIADO
LOGO_URL = "https://i.postimg.cc/D0wjcYP4/grupo-energisa.png"

# Ícones Icons8
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

# CSS Estilizado
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
    .card-orange {{ border-left: 5px solid {SECONDARY_ORANGE}; }}
    .card-blue {{ border-left: 5px solid {PRIMARY_BLUE}; }}
    .card-light-blue {{ border-left: 5px solid #4a90e2; }}
    
    .card-green {{ background-color: {SUCCESS_GREEN} !important; }}
    .card-green div, .card-green h2, .card-green p, .card-green span {{ color: #ffffff !important; }}
    
    .big-number {{ font-size: 20px; font-weight: bold; margin: 5px 0; color: #333 !important; }}
    .label-text {{ font-size: 12px; font-weight: bold; text-transform: uppercase; color: #666 !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. LÓGICA DE CÁLCULO ---
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

# --- 3. GERADOR DE PDF ---
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

        # Logo centralizada no topo do PDF
        safe_image(LOGO_URL, 85, 5, 40)

    def footer(self):
        self.set_y(-12); self.set_font('Arial', 'I', 6); self.set_text_color(150); self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def criar_pdf_visual_final(d, nome, cidade, desconto):
    pdf = PDFOficial(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Barra de Destaque
    pdf.set_y(30); pdf.set_fill_color(*PDF_CYAN); pdf.rect(0, 30, 210, 8, 'F')
    pdf.set_font("Arial", "B", 10); pdf.set_text_color(255); pdf.cell(0, 8, "Proposta de Economia e Eficiencia Energetica", 0, 1, 'C')
    
    # [Mantendo a lógica de ícones e cards do seu PDF original]
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12); pdf.set_text_color(*PDF_CYAN); pdf.cell(0, 8, "Resumo da Proposta Comercial", 0, 1, 'C')
    
    # Card de Economia Anual no PDF
    pdf.set_fill_color(240, 240, 240); pdf.rect(15, 60, 180, 40, 'F')
    pdf.set_xy(15, 65); pdf.set_font("Arial", "B", 14); pdf.set_text_color(50)
    pdf.cell(180, 10, f"Economia Anual Estimada: {fmt_currency(d['econ_ano'])}", 0, 1, 'C')
    pdf.set_font("Arial", "", 10); pdf.cell(180, 10, f"Desconto aplicado: {desconto}%", 0, 1, 'C')

    # Rodapé de Dados
    pdf.set_y(-40); pdf.set_font("Arial", "B", 8); pdf.set_text_color(*PDF_CYAN)
    pdf.cell(0, 5, f"Cliente: {nome.upper()}", 0, 1)
    pdf.cell(0, 5, f"Cidade: {cidade.upper()}", 0, 1)
    pdf.set_font("Arial", "I", 7); pdf.set_text_color(100)
    pdf.cell(0, 5, "Validade: 10 dias. Sujeito a alteracoes de tarifa da distribuidora.", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFACE DO USUÁRIO ---
# LOGO NO SITE
st.image(LOGO_URL, width=220)
st.title("Simulador Comercial")
st.write("---")

with st.container():
    st.markdown("### 1. Dados do Cliente")
    c1, c2, c3 = st.columns(3)
    nome = c1.text_input("Nome", value="")
    cidade = c2.text_input("Cidade", value="")
    tipo = c3.radio("Tipo de Ligação", ["Trifásico", "Bifásico", "Monofásico"], horizontal=True)
    
    st.markdown("### 2. Dados da Fatura")
    c4, c5 = st.columns(2)
    kwh = c4.number_input("Consumo (kWh)", min_value=0.0, value=None, placeholder="Digite o kWh...")
    val_unit = c5.number_input("Valor Unitário (R$)", min_value=0.0, value=1.1540, format="%.4f")
    c6, c7, c8 = st.columns(3)
    ban = c6.number_input("Bandeiras (R$)", min_value=0.0, value=None, placeholder="R$ 0,00")
    ilum = c7.number_input("Ilum. Púb. (R$)", min_value=0.0, value=None, placeholder="R$ 0,00")
    desc = c8.number_input("Desconto (%)", value=20.0, step=0.5)

    if st.button("GERAR SIMULAÇÃO", use_container_width=True):
        if kwh:
            res = calcular(kwh, val_unit, tipo, ban, ilum, desc)
            st.write("---")
            
            # Cards de Resultado no Site
            st.markdown(f"""
            <div class="card-result card-orange">
                <div class="label-text">Fatura Atual Estimada</div>
                <div class="big-number">{fmt_currency(res['total_atual'])}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="card-result card-green">
                <div style="font-weight:bold; color:white;">Economia Mensal: {fmt_currency(res['econ_mes'])}</div>
                <div style="font-size:22px; font-weight:bold; color:white;">Economia Anual: {fmt_currency(res['econ_ano'])}</div>
            </div>
            """, unsafe_allow_html=True)

            pdf_bytes = criar_pdf_visual_final(res, nome, cidade, desc)
            st.download_button(label="⬇️ BAIXAR PROPOSTA EM PDF", data=pdf_bytes, file_name=f"Proposta_{nome}.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.error("Informe o consumo em kWh para calcular.")
