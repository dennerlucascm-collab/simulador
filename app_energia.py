import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import tempfile
import os
from datetime import datetime

# --- 1. CONFIGURAÇÕES VISUAIS ---
st.set_page_config(page_title="Simulador Comercial Energisa", page_icon="☀️", layout="centered")

# CORES ENERGISA
BG_COLOR = "#FFFFFF"         # Branco
PRIMARY_ORANGE = "#F37021"   # Laranja Energisa
SECONDARY_BLUE = "#005596"   # Azul Energisa
TEXT_DARK = "#334155"
SUCCESS_GREEN = "#28a745"

# LINK DA LOGO ENERGISA ATUALIZADO
LOGO_ENERGISA = "https://i.postimg.cc/K80nPvHc/Energisa-svg-2-removebg-preview.png"

# Ícones Icons8 (Links diretos para PNG branco)
ICON_SOLAR = "https://img.icons8.com/ios-filled/50/ffffff/solar-panel.png"
ICON_PIGGY = "https://img.icons8.com/ios-filled/50/ffffff/money-box.png"
ICON_BULB =  "https://img.icons8.com/ios-filled/50/ffffff/light-on.png"
ICON_PLANT = "https://img.icons8.com/ios-filled/50/ffffff/potted-plant.png"
ICON_FILE =  "https://img.icons8.com/ios-filled/50/ffffff/checked--v1.png"

ICONS_LIST = [ICON_SOLAR, ICON_PIGGY, ICON_BULB, ICON_PLANT, ICON_FILE]
ICONS_FALLBACK = ["S", "$", "!", "Y", "V"]

# Cores para o PDF
PDF_ORANGE = (243, 112, 33)
PDF_BLUE = (0, 85, 150)

def fmt_currency(val): return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_number(val): return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# CSS Estilizado com Identidade Energisa
st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_COLOR}; }}
    h1, h2, h3, h4, p, div, span, label, li {{ color: {TEXT_DARK} !important; font-family: 'sans-serif'; }}
    
    /* Títulos em Azul Energisa */
    h1, h2, .slide-title {{ color: {SECONDARY_BLUE} !important; }}
    
    div.stButton > button {{ 
        background-color: {PRIMARY_ORANGE} !important; color: #ffffff !important; 
        border-radius: 8px; height: 50px; font-weight: bold; text-transform: uppercase; border: none; width: 100%;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    div.stButton > button p {{ color: #ffffff !important; }}
    
    .card-result {{ padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); background-color: white; }}
    .card-orange {{ border-left: 8px solid {PRIMARY_ORANGE}; }}
    .card-blue {{ border-left: 8px solid {SECONDARY_BLUE}; }}
    
    /* Card Verde de Economia */
    .card-green {{ background-color: {PRIMARY_ORANGE} !important; }}
    .card-green div, .card-green h2, .card-green p, .card-green span {{ color: #ffffff !important; }}
    
    .big-number {{ font-size: 22px; font-weight: bold; margin: 5px 0; color: {SECONDARY_BLUE} !important; }}
    .label-text {{ font-size: 13px; font-weight: bold; text-transform: uppercase; color: #64748b !important; }}
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

# --- 3. PDF COM IDENTIDADE ENERGISA ---
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

        safe_image(LOGO_ENERGISA, 10, 5, 45)

    def footer(self):
        self.set_y(-12); self.set_font('Arial', 'I', 6); self.set_text_color(150); self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def criar_pdf_visual_final(d, nome, cidade, desconto):
    pdf = PDFOficial(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    
    # Barra de Destaque Energisa
    pdf.set_y(30); pdf.set_fill_color(*PDF_ORANGE); pdf.rect(0, 30, 210, 8, 'F')
    pdf.set_font("Arial", "B", 10); pdf.set_text_color(255); pdf.cell(0, 8, "Proposta Comercial Energisa Solar - Mato Grosso", 0, 1, 'C')
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12); pdf.set_text_color(*PDF_BLUE); pdf.cell(0, 8, "ESTUDO DE VIABILIDADE ECONOMICA", 0, 1, 'C')
    
    # Grid de Resultados no PDF
    pdf.set_draw_color(*PDF_BLUE); pdf.set_line_width(0.5); pdf.rect(15, 60, 180, 50)
    pdf.set_xy(20, 65); pdf.set_font("Arial", "B", 11); pdf.set_text_color(50); pdf.cell(0, 10, f"Cliente: {nome.upper()}", 0, 1)
    pdf.set_x(20); pdf.cell(0, 10, f"Economia Anual Projetada: {fmt_currency(d['econ_ano'])}", 0, 1)
    pdf.set_x(20); pdf.set_font("Arial", "", 10); pdf.cell(0, 10, f"Cidade: {cidade.upper()} / Desconto Aplicado: {desconto}%", 0, 1)

    # Footer de validade
    pdf.set_y(-30); pdf.set_font("Arial", "I", 8); pdf.set_text_color(120)
    pdf.cell(0, 5, "Esta proposta tem validade de 10 dias e esta sujeita a alteracoes tarifarias.", 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFACE ---
st.image(LOGO_ENERGISA, width=200)
st.title("Simulador Comercial")
st.write("---")

with st.container():
    st.markdown("### 📝 Dados do Cliente")
    c1, c2, c3 = st.columns(3)
    nome = c1.text_input("Nome do Cliente", value="")
    cidade = c2.text_input("Cidade", value="")
    tipo = c3.radio("Tipo de Ligação", ["Trifásico", "Bifásico", "Monofásico"], horizontal=True)
    
    st.markdown("### ⚡ Detalhes da Fatura")
    c4, c5 = st.columns(2)
    kwh = c4.number_input("Consumo Médio (kWh)", min_value=0.0, value=None, placeholder="Digite o consumo...")
    val_unit = c5.number_input("Tarifa Energisa (R$)", min_value=0.0, value=1.1540, format="%.4f")
    
    c6, c7, c8 = st.columns(3)
    ban = c6.number_input("Bandeiras (R$)", min_value=0.0, value=None, placeholder="R$ 0,00")
    ilum = c7.number_input("Contrib. Ilum (R$)", min_value=0.0, value=None, placeholder="R$ 0,00")
    desc = c8.number_input("Desconto (%)", value=20.0, step=0.5)

    st.write("")
    if st.button("CALCULAR ECONOMIA", use_container_width=True):
        if kwh:
            res = calcular(kwh, val_unit, tipo, ban, ilum, desc)
            st.write("---")
            st.markdown("### 📊 Análise de Resultados")
            
            # Card Fatura Atual
            st.markdown(f"""
            <div class="card-result card-blue">
                <div class="label-text">Investimento Atual Sem Desconto</div>
                <div class="big-number">{fmt_currency(res['total_atual'])}</div>
            </div>
            """, unsafe_allow_html=True)

            # Card Economia (Destaque Laranja)
            st.markdown(f"""
            <div class="card-result card-green">
                <div style="font-size: 18px; margin-bottom: 5px; color: white !important;">💰 Sua Economia Estimada</div>
                <div style="font-size: 32px; font-weight: bold; color: white !important;">Ano: {fmt_currency(res['econ_ano'])}</div>
                <div style="font-size: 18px; opacity: 0.9; color: white !important;">Mês: {fmt_currency(res['econ_mes'])}</div>
            </div>
            """, unsafe_allow_html=True)

            # PDF Download
            pdf_bytes = criar_pdf_visual_final(res, nome, cidade, desc)
            st.download_button(label="⬇️ BAIXAR PROPOSTA ENERGISA (PDF)", data=pdf_bytes, file_name=f"Proposta_Energisa_{nome}.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.error("Por favor, informe o consumo em kWh.")

Sua apresentação e o código do site Energisa Solar estão prontos! Sinta-se à vontade para explorar o layout e me avisar se quiser fazer mais algum ajuste.
