import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import tempfile
import os
from datetime import datetime

# --- 1. CONFIGURAÇÕES VISUAIS ---
st.set_page_config(page_title="Simulador Eficiencie", page_icon="☀️", layout="centered")

# NOVA PALETA MODO ESCURO GESTÃO EMPRESARIAL
PRIMARY_BLUE = "#0A1B35"     
PRIMARY_GOLD = "#DE9E26"     
SUCCESS_GREEN = "#27ae60"

LOGO_URL = "https://i.postimg.cc/8c1tSX1V/Nova-logo-Eficiencie-removebg-preview.png"

# Ícones Icons8
ICON_SOLAR = "https://img.icons8.com/ios-filled/50/ffffff/solar-panel.png"
ICON_PIGGY = "https://img.icons8.com/ios-filled/50/ffffff/money-box.png"
ICON_BULB =  "https://img.icons8.com/ios-filled/50/ffffff/light-on.png"
ICON_PLANT = "https://img.icons8.com/ios-filled/50/ffffff/potted-plant.png"
ICON_FILE =  "https://img.icons8.com/ios-filled/50/ffffff/checked--v1.png"

ICONS_LIST = [ICON_SOLAR, ICON_PIGGY, ICON_BULB, ICON_PLANT, ICON_FILE]
ICONS_FALLBACK = ["S", "$", "!", "Y", "V"] 

# Cores para o PDF
PDF_BLUE = (10, 27, 53)
PDF_GOLD = (222, 158, 38)
PDF_GRAY = (240, 240, 240)

def fmt_currency(val): return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_number(val): return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# CSS Customizado - Modo Escuro Premium
st.markdown(f"""
    <style>
    .stApp {{ background-color: {PRIMARY_BLUE}; }}
    h1, h2, h3, h4, p, label, li {{ color: #FFFFFF !important; font-family: 'Segoe UI', sans-serif; }}
    
    .stTextInput input, .stNumberInput input {{ 
        border-radius: 6px !important;
        border: 2px solid {PRIMARY_GOLD} !important;
        background-color: #ffffff !important; 
        color: {PRIMARY_BLUE} !important;
        font-weight: 600;
    }}
    
    div.stButton > button {{ 
        background-color: {PRIMARY_GOLD} !important; 
        color: {PRIMARY_BLUE} !important; 
        border-radius: 8px; 
        height: 55px; 
        font-weight: 900; 
        font-size: 16px;
        text-transform: uppercase; 
        border: none; 
        width: 100%;
        box-shadow: 0 4px 6px rgba(222, 158, 38, 0.3);
        transition: all 0.3s ease;
    }}
    div.stButton > button:hover {{ background-color: #c48a20 !important; }}
    div.stButton > button p {{ color: {PRIMARY_BLUE} !important; font-size: 16px; font-weight: 900; }}
    
    .card-result {{ 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center; 
        margin-bottom: 15px; 
        background-color: #FFFFFF !important; 
    }}
    .card-result div, .card-result p, .card-result span {{ color: {PRIMARY_BLUE} !important; }}
    .card-result .label-text {{ font-size: 13px; font-weight: 700; text-transform: uppercase; color: #7F8C8D !important; }}
    .card-result .big-number {{ font-size: 24px; font-weight: 800; margin: 8px 0; }}
    
    .card-red {{ border-top: 5px solid {PRIMARY_GOLD}; }}
    .card-blue {{ border-top: 5px solid {PRIMARY_BLUE}; }}
    
    .card-green {{ 
        background: linear-gradient(135deg, {PRIMARY_BLUE}, #112A52) !important; 
        border: 1px solid {PRIMARY_GOLD};
    }}
    .card-green div, .card-green span {{ color: #FFFFFF !important; }}
    .card-green .highlight {{ color: {PRIMARY_GOLD} !important; font-weight: 900; }} 
    </style>
""", unsafe_allow_html=True)

# --- 2. MOTOR DA TABELA ÓRIGO (COM REGRA DE CORTE DE 5000 kWh) ---
def obter_planos(kwh_val):
    if kwh_val is None or kwh_val == 0:
        return [{"nome": "⚠️ Preencha o Consumo (kWh) primeiro...", "desc": 0, "fid": "-", "aviso": "-"}]
        
    k = float(kwh_val)
    
    # Se for 5000 ou mais, mostra APENAS os planos Premium (limpa os inferiores)
    if k >= 5000:
        planos = [
            {"nome": "20% | Sem Fidelidade | Aviso 180 dias", "desc": 20, "fid": "NÃO", "aviso": "180 DIAS"},
            {"nome": "25% | Fidelidade 1 Ano | Aviso 180 dias", "desc": 25, "fid": "1 ANO", "aviso": "180 DIAS"}
        ]
    else:
        # Se for menor que 5000, carrega a base (Até 999)
        planos = [
            {"nome": "10% | Sem Fidelidade | Aviso 120 dias", "desc": 10, "fid": "NÃO", "aviso": "120 DIAS"},
            {"nome": "16% | Sem Fidelidade | Aviso 180 dias", "desc": 16, "fid": "NÃO", "aviso": "180 DIAS"},
            {"nome": "18% | Fidelidade 1 Ano | Aviso 180 dias", "desc": 18, "fid": "1 ANO", "aviso": "180 DIAS"}
        ]
        # E se for de 1000 até 4999, ganha também a opção de 12%
        if k >= 1000:
            planos.append({"nome": "12% | Sem Fidelidade | Aviso 180 dias", "desc": 12, "fid": "NÃO", "aviso": "180 DIAS"})
        
    # Retorna os planos ordenados da menor porcentagem para a maior
    return sorted(planos, key=lambda x: x["desc"])

def calcular(kwh_total, valor_unit, tipo, bandeira, ilum, desc):
    kwh_total = kwh_total if kwh_total else 0.0
    valor_unit = valor_unit if valor_unit else 0.0
    bandeira = bandeira if bandeira else 0.0
    ilum = ilum if ilum else 0.0

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

# --- 3. PDF PREMIUM EFICIENCIE ---
class PDFOficial(FPDF):
    def header(self):
        self.set_fill_color(*PDF_BLUE)
        self.rect(0, 0, 210, 45, 'F')
        self.set_fill_color(*PDF_GOLD)
        self.rect(0, 44, 210, 1.5, 'F')
        headers = {'User-Agent': 'Mozilla/5.0'}
        def safe_image(url, x, y, w):
            try:
                r = requests.get(url, headers=headers, timeout=5)
                if r.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(r.content); tmp_name = tmp.name
                    self.image(tmp_name, x, y, w); os.unlink(tmp_name)
            except: pass
        safe_image(LOGO_URL, 10, 4, 42)
        
        self.set_y(20)
        self.set_font("Arial", "B", 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 5, "ESTUDO DE VIABILIDADE ECONÔMICA", 0, 1, 'R')

    def footer(self):
        self.set_y(-15)
        self.set_fill_color(*PDF_BLUE)
        self.rect(0, 285, 210, 15, 'F')
        self.set_font('Arial', 'B', 8)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'Eficiencie - Soluções em Energia Inteligente', 0, 0, 'C')

def criar_pdf_visual_final(d, nome, cidade, dados_plano, desconto_final, uc):
    pdf = PDFOficial(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    pdf.set_y(52); pdf.set_font("Arial", "B", 12); pdf.set_text_color(*PDF_GOLD)
    pdf.cell(0, 8, "Energia solar sem investimento? Saiba como isso é possível.", 0, 1, 'C')
    pdf.set_draw_color(*PDF_GOLD); pdf.line(15, 61, 195, 61)
    
    pdf.ln(6); pdf.set_font("Arial", "B", 11); pdf.set_text_color(*PDF_BLUE)
    pdf.cell(0, 6, "Conheça os benefícios da Geração Compartilhada:", 0, 1, 'C')
    y_icons = pdf.get_y() + 4; centers = [25, 65, 105, 145, 185]
    
    if dados_plano['fid'] == "NÃO":
        txt_fid = "Sem fidelidade após\no cumprimento\ndo aviso prévio"
    else:
        txt_fid = f"Fidelidade: {dados_plano['fid'].title()}\nAviso: {dados_plano['aviso'].title()}"

    txts = [
        "Sem instalação\nde equipamentos", 
        "Sem preocupação\ncom manutenção", 
        "Economia na\nconta de energia", 
        "Energia limpa\ne sustentável", 
        txt_fid
    ]
    
    pdf.set_font("Arial", "", 7); pdf.set_text_color(80)
    for i, t in enumerate(txts):
        cx = centers[i]
        pdf.set_fill_color(*PDF_BLUE); pdf.ellipse(cx-9, y_icons, 18, 18, 'F') 
        success =
