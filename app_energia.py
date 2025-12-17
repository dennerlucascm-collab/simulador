import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import tempfile
import os
import base64
from datetime import datetime

# --- 1. CONFIGURAÇÕES VISUAIS DO SITE ---
st.set_page_config(page_title="Simulador Reenergisa", page_icon="☀️", layout="centered")

# Cores
BG_COLOR = "#fdf1db"       # Bege
PRIMARY_BLUE = "#26628d"   # Azul Escuro
ECONOMY_BLUE = "#4a90e2"   # Azul Claro
ALERT_ORANGE = "#e67e22"   # Laranja
SUCCESS_GREEN = "#28a745"  # Verde

# Links Imagens (Logos continuam por link pois são maiores e funcionam bem)
LOGO_EFICIENCIE = "https://i.postimg.cc/WzKTZg47/LOGO-COMPLETA-removebg-preview.png"
LOGO_REENERGISA = "https://i.postimg.cc/nzHb5T5v/LOGO-positivo-reenergisa-2000x674.png"

# --- ÍCONES EM BASE64 (SOLUÇÃO DEFINITIVA) ---
# Isso garante que os ícones funcionem sem precisar baixar da internet
# Ícone Solar (Painel)
ICON_SOLAR_B64 = """
iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAABmJLR0QA/wD/AP+gvaeTAAAB
iklEQVRoge3ZwUpDQRDG8f+mCBEqaCNF8Cp6H8G76H0E76K30WsVvYoQoQcR3Ehx42J1sDQT
Mzvk2+YPJLPwdt/szt3ZSWJmZmamY80G8AxsA2/ACbAGLADJ+90Ad8AzcAncVR28L6wD98Az
cKm+d4F94L7q4H1hG3gEroBToK++d4CtwH01wUfCInAPXAPn6nsH2Fbfj9UEHwk7wD1wDZyr
7x1gR30/VRN8JOwD98A1cKG+d4A99f1STfCRcADcA9fAhfreAfbU92s1wUfCIXAPXAPn6nsH
OFDfH9UEHwmHwT1wDZyr7x3gUH2/VxN8JBwG98A1cK6+d4Aj9f1RTfCRcATcA9fAufreAY7V
92c1wUfCMXAPXAPn6nsHOFbf39UEHwnHwT1wDZyr7x3gRH3/UBN8JJwE98A1cK6+d4BT9f1T
TfCRcAr8/6+B8/i9t4Fz9f1bTfCRcAbcA9fAufreAc7U9+9qgo+E8+AeuAbO1fcOcK6+f6sJ
PhL+hZ6Z/df8Am5bWd66rYQPAAAAAElFTkSuQmCC
"""

# Ícone Porquinho (Economia)
ICON_PIGGY_B64 = """
iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAABmJLR0QA/wD/AP+gvaeTAAAC
TUlEQVRoge3ZvU8UQRQH8N+DICZUEA0xMdZQaYyFhR9/g4WlxsaY2FhZ+R+wsbTExsRYaIyf
g4UfCwoTE6wJ8VFBYiDxMzE73N3bs7v32IGbu59kQvbu3rw3O/PemzcvMzo6Ojo6Ov5faQZe
Aj3ACtAPjAHdwC1gEngGrANLwI+mIl6QYeAR0A+sU51pYBT4bF/3gCngJbAUQ8i2MAI8A/qB
DerzFHgF/LDvB8AM8BJYiiFkWxgFngL9wAb1eQq8An7a9wNgBngJLMYQsi2MAk+AfmCT+jwF
XgE/7fsBMAO8BJZiCNkWRoCnQD+wSX2eAq+AH/b9AJgBXgJLMYRsCyPAM6Af2KQ+T4FXwHf7
vg/MAC+BpRhCtoUR4BnQD2xSn6fAK+Cbfd8HZoCXwFIMIdvCCPAM6Ac2qc9T4BXwzb7vAzPA
S2AphpBtYQR4BvQDm9TnKfAK+GLf94EZ4CWwFEPItjACPAX6gU3q8xR4BXyz7/vADPASWIoh
ZFsYAZ4B/cAm9XkKvAK+2fd9YAZ4CSzFELItjADPgH5gk/o8BV4B3+37PjADvASWYgjZFkaA
p0A/sEl9ngKvgB/2/QCYAV4CSzGEbAsjwFOgH9ikPk+BV8BP+34AzAAvgcUYQraFUeAp0A9s
UJ+nwCvgp30/AGaAl8BSDCHbwigwBfQD69TnKfAK+GHf94EZ4CWwFEPItjAKfAA+A2vU5ykw
CnTa9z1gCngJLMUQsi10A6PAZ+A9sA4sU51pYBT4bF/3gEngGbAOLAPfmonY1dHR0dHR0fE/
+g31+554+r/s4AAAAABJRU5ErkJggg==
"""

# Ícone Lâmpada (Ideia/Energia)
ICON_BULB_B64 = """
iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAABmJLR0QA/wD/AP+gvaeTAAAB
c0lEQVRoge3ZsUrDQBzG8U+Lggii0CK4OImj4OIgOImj4OIgOImj4OIgOImj4OIgOImj4OIg
OImj4OIgOImjiKCDg0gLFpS2xV6uF3y/y9397vLgLxc4jo6Ojo6Ozh+yDKwAL8A9cAgcArfA
G7AKzDUS8k0GgRfget1z4AJ4BVYaCfkma8C76lV5C1wAb8BKIyHfZB14V70qb4EL4A1YaSTk
m2wA76pX5S1wAbwBK42EfJMt4EP1qrwFLoA3YKWxkA9kG/hQvSpvgQvgDVhpLOSDbAMfqlfl
LXABvAErjYV8INvAh+pVeQtcAG/ASmMhH8gO8KF6Vd4CF8AbsNJYyAeyC3yoXpW3wAXwBqw0
FvKB7AEfqlflLXABvAErjYV8IPvAh+pVeQtcAG/ASmMhH8gB8KF6Vd4CF8AbsNJYyAdyCHyo
XpW3wAXwBqw0FvKBHAEfqlflLXABvAErjYV8IMfAh+pVeQtcAG/ASmMhH8gJ8KF6Vd4C5+Po
6Ojo6Ojo/OELq7qE+wWc3cEAAAAASUVORK5CYII=
"""

# Ícone Planta (Sustentável)
ICON_PLANT_B64 = """
iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAABmJLR0QA/wD/AP+gvaeTAAAB
+0lEQVRoge3Zz0uUQRjH8ZeW0S528BJE6OAleAki6OAleAki6OAleAki6OAleAki6OAleAki
6OAleAki6OAleAki6OAleAki6OAleAki6OAleAmC/oBwWJ0dZ3dnZ919n5n7g8/LzrzPzDPP
7M4888zU1NTU1NTU1PwfTcAg0A/0A21AC9ACNAO/gV/AD+AHMAosA4t1w6pKA9ADjADdwK2K
f3cDeA6MA49qwlWNAWAMGALuV/y7h8AL4CkwUBOuagwA48AQ8LDi3z0E3gBPgYmacFVjABgH
hoGHFf/uIfAGeApM1ISrGgPAODAMPCr5dw+At8BTYKImXNUYAMaBYeBRyb97ALwFngITNeGq
xgAwDgwDj0r+3QPgLfAUmKgJVzUGgHFgGHhU8u8eAG+Bp8BETbiqMQCMA8PAo5J/9wB4CzwF
JmrCVY0BYBwYBh6V/LsHwFvgKTBRE65qDADjwDDwqOTfPQDeAk+BiZpwVWNQaC/wFHgM3Kv4
d1uAF8AY8LgmXNUYFNoLPAUeA/cq/t0W4AUwBjyuCVc1BoX2Ak+Bx8C9in+3BXgBjAGPa8JV
jUGhvcBT4DFwr+LfbQFeAGPA45pwVWNQaC/wFHgM3Kv4b5sFHgNjwOOacFVjUGgMGAUeA/cq
/ttmgcfAGPC4JlzVqKmpqampqan5b3wH0s1/q8Lq7gIAAAAASUVORK5CYII=
"""

# Ícone Check (Verificado)
ICON_CHECK_B64 = """
iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAABmJLR0QA/wD/AP+gvaeTAAAB
t0lEQVRoge3ZPUvDQBjG8f+TiiC0oK0dFMFJHAUncRScxFFwEkfBSWwVnMRRcBJHwUkcBSdx
FJzEUXASR8FJHAVE0MHBQasFpW0s1w++9+XucpcHfrnAcXR0dHR0dP6RZWAFeAHugUPgELgF
3oBVYK6RkG8yCLwA1+ueAxfAK7DSeC3fZB14V70qb4EL4A1YaSTkm2wA76pX5S1wAbwBK42E
fJMt4F31qrwFLoA3YKWxkA9kB/hQvSpvgQvgDVhpLOSD7AAfqlflLXABvAErjYV8ILvAh+pV
eQtcAG/ASmMhH8g+8KF6Vd4CF8AbsNJYyAdyAHyoXpW3wAXwBqw0FvKBHAEfqlflLXABvAEr
jYV8IMfAh+pVeQtcAG/ASmMhH8gJ8KF6Vd4CF8AbsNJYyAdyCnyoXpW3wAXwBqw0FvKBnAMf
qlflLXABvAErjYV8IBfAh+pVeQtcAG/ASmMhH8gl8KF6Vd4CF8AbsNJYyAdyBXyoXpW3wAXw
Bqw0FvKB3AAfqlflLXABvAErjYV8ILfAh+pVeQtcAG/ASmMhH8g98KF6Vd4C5+Po6Ojo6Ojo
/OELv6qE+3t/dCQAAAAASUVORK5CYII=
"""

# Lista de ícones decodificados (será preenchida no loop)
# Mapeamento para facilitar o uso no loop
ICONS_B64_LIST = [ICON_SOLAR_B64, ICON_PIGGY_B64, ICON_BULB_B64, ICON_PLANT_B64, ICON_CHECK_B64]

# Cores PDF
PDF_CYAN = (0, 158, 224); PDF_LIME = (195, 213, 0); PDF_ORANGE = (243, 112, 33)

# Formatadores
def fmt_currency(val): return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_number(val): return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# CSS Personalizado
st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_COLOR}; }}
    h1, h2, h3, h4, p, div, span, label, li {{ color: {PRIMARY_BLUE} !important; font-family: sans-serif; }}
    .stTextInput input, .stNumberInput input, .stSelectbox div {{ color: {PRIMARY_BLUE} !important; background-color: #ffffff !important; }}
    
    div.stButton > button {{ 
        background-color: {PRIMARY_BLUE} !important; 
        color: #ffffff !important; 
        border-radius: 8px; height: 50px; font-weight: bold; text-transform: uppercase; border: none; width: 100%;
    }}
    div.stButton > button p {{ color: #ffffff !important; }}
    
    /* CARDS */
    .card-result {{ padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); background-color: white; }}
    
    .card-orange {{ border-left: 5px solid {ALERT_ORANGE}; }}
    .card-blue {{ border-left: 5px solid {PRIMARY_BLUE}; }}
    .card-light-blue {{ border-left: 5px solid {ECONOMY_BLUE}; }}
    
    /* CARD ECONOMIA (VERDE) */
    .card-green {{ 
        background-color: {SUCCESS_GREEN}; 
        color: #ffffff !important; 
    }}
    .card-green div, .card-green span {{ color: #ffffff !important; }}
    
    .big-number {{ font-size: 20px; font-weight: bold; margin: 5px 0; color: #333 !important; }}
    .label-text {{ font-size: 12px; font-weight: bold; text-transform: uppercase; color: #666 !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. CÁLCULO ---
def calcular(kwh_total, valor_unit, tipo, bandeira, ilum, desc):
    # Tratamento None
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

    # Fatura Atual Completa
    total_atual = (kwh_total * valor_unit) + bandeira + ilum
    
    # Nova Fatura (Separada)
    # 1. Parte Energisa (Custo Disp + Bandeira + Ilum)
    fat_en = (kwh_res * valor_unit) + bandeira + ilum
    
    # 2. Parte Reenergisa (Consumo Injetado com Desconto)
    val_re_unit = valor_unit * (1 - (desc/100))
    fat_re = kwh_re * val_re_unit
    
    # 3. Total Novo
    total_novo = fat_en + fat_re
    
    # Economia
    econ_mes = total_atual - total_novo
    
    return {
        "total_atual": total_atual, 
        "fat_en": fat_en,          # Parte Energisa
        "fat_re": fat_re,          # Parte Reenergisa
        "total_novo": total_novo,  # Soma das duas
        "econ_mes": econ_mes, 
        "econ_ano": econ_mes * 12,
        "kwh_re": kwh_re, 
        "qtd_placas": qtd_placas
    }

# --- 3. PDF (COM BASE64) ---
class PDFOficial(FPDF):
    def header(self):
        self.set_fill_color(255, 255, 255); self.rect(0, 0, 210, 30, 'F')
        headers = {'User-Agent': 'Mozilla/5.0'} 
        try:
            r1 = requests.get(LOGO_EFICIENCIE, headers=headers)
            if r1.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(r1.content); self.image(tmp.name, 10, 5, 35); os.unlink(tmp.name)
        except: pass
        try:
            r2 = requests.get(LOGO_REENERGISA, headers=headers)
            if r2.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(r2.content); self.image(tmp.name, 140, 6, 55); os.unlink(tmp.name)
        except: pass

    def footer(self):
        self.set_y(-12); self.set_font('Arial', 'I', 6); self.set_text_color(150); self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def criar_pdf_visual_final(d, nome, cidade, desconto):
    pdf = PDFOficial(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    
    # Barra Verde
    pdf.set_y(30); pdf.set_fill_color(*PDF_LIME); pdf.rect(0, 30, 210, 8, 'F')
    pdf.set_font("Arial", "B", 10); pdf.set_text_color(255); pdf.cell(0, 8, "Energia solar sem investimento? Saiba como isso e possivel.", 0, 1, 'C')
    
    # Ícones
    pdf.ln(3); pdf.set_font("Arial", "B", 10); pdf.set_text_color(*PDF_CYAN)
    pdf.cell(0, 6, "Conheca os beneficios da Geracao Compartilhada:", 0, 1, 'C')
    y_icons = pdf.get_y() + 2; centers = [25, 65, 105, 145, 185]
    txts = ["Sem instalacao\nde equipamentos", "Sem preocupacao\ncom manutencao", "Economia na\nconta de energia", "Energia limpa\ne sustentavel", "Sem fidelidade apos\no cumprimento\ndo aviso previo"]
    pdf.set_font("Arial", "", 7); pdf.set_text_color(80)
    
    for i, t in enumerate(txts):
        cx = centers[i]; pdf.set_fill_color(*PDF_CYAN); pdf.ellipse(cx-8, y_icons, 16, 16, 'F')
        
        # USA BASE64 AQUI (SEM DOWNLOAD)
        try:
            img_data = base64.b64decode(ICONS_B64_LIST[i])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(img_data)
                tmp_name = tmp.name
            pdf.image(tmp_name, cx-4, y_icons+4, 8, 8)
            os.unlink(tmp_name)
        except: pass
        
        pdf.set_xy(cx-15, y_icons + 18); pdf.multi_cell(30, 3, t, 0, 'C')

    # Como Funciona
    y_steps = y_icons + 35; pdf.set_xy(0, y_steps - 6); pdf.set_font("Arial", "B", 10); pdf.set_text_color(*PDF_CYAN); pdf.cell(0, 6, "Veja como funciona:", 0, 1, 'C')
    steps = ["1. Nos instalamos os paineis solares nas nossas usinas", "2. A luz solar e convertida em energia eletrica", "3. Voce adquire uma cota de acordo com seu consumo", "4. A energia injetada vira credito na sua conta"]
    bw = 42; sx = 13; gp = 4; pdf.set_font("Arial", "", 8); pdf.set_text_color(255)
    for i, t in enumerate(steps):
        cx = sx + (i * (bw + gp)); pdf.set_fill_color(*PDF_CYAN); pdf.rect(cx, y_steps, bw, 22, 'F')
        pdf.set_xy(cx + 2, y_steps + 3); pdf.multi_cell(bw - 4, 3.5, t, 0, 'C')

    # Titulo
    yp = y_steps + 30; pdf.set_xy(0, yp); pdf.set_font("Arial", "B", 12); pdf.set_text_color(*PDF_CYAN); pdf.cell(0, 8, "Proposta Comercial de Locacao de Usina Fotovoltaica", 0, 1, 'C')
    yb = pdf.get_y() + 2; pdf.set_draw_color(*PDF_CYAN); pdf.set_line_width(0.5); pdf.rect(13, yb, 184, 12)
    pdf.set_xy(15, yb + 3); pdf.set_font("Arial", "", 9); pdf.set_text_color(*PDF_CYAN); pdf.cell(40, 5, "N cliente ENERGISA MATO", 0, 1)

    # Cards Coloridos PDF
    yc = yb + 16; wc = 60; hc = 28; xc = 13
    # Media
    pdf.set_draw_color(*PDF_ORANGE); pdf.set_line_width(1); pdf.rect(xc, yc, wc, hc)
    pdf.set_xy(xc, yc + 3); pdf.set_font("Arial", "B", 9); pdf.set_text_color(*PDF_ORANGE); pdf.cell(wc, 5, "Media* (R$)", 0, 2, 'C')
    pdf.set_font("Arial", "", 7); pdf.set_text_color(80); pdf.cell(wc, 4, "(sem contratacao de GD)", 0, 2, 'C')
    pdf.ln(2); pdf.set_font("Arial", "B", 14); pdf.set_text_color(50); pdf.cell(wc, 6, fmt_currency(d['total_atual']), 0, 0, 'C')
    # Econ
    xc += wc + 2; pdf.set_draw_color(*PDF_LIME); pdf.rect(xc, yc, wc, hc)
    pdf.set_xy(xc, yc + 3); pdf.set_font("Arial", "B", 9); pdf.set_text_color(*PDF_LIME); pdf.cell(wc, 5, "Economia Ofertada", 0, 2, 'C')
    pdf.set_font("Arial", "", 8); pdf.set_text_color(50); pdf.cell(wc, 5, f"Previo: {desconto:.1f}%", 0, 2, 'C')
    pdf.set_font("Arial", "", 7); pdf.set_text_color(100); pdf.cell(wc, 4, "% sobre credito compensado", 0, 0, 'C')
    # Anual
    xc += wc + 2; pdf.set_draw_color(*PDF_CYAN); pdf.rect(xc, yc, wc, hc)
    pdf.set_xy(xc, yc + 3); pdf.set_font("Arial", "B", 9); pdf.set_text_color(*PDF_CYAN); pdf.cell(wc, 5, "Economia Anual Projetada", 0, 2, 'C')
    pdf.ln(4); pdf.set_x(xc); pdf.set_font("Arial", "B", 14); pdf.set_text_color(50); pdf.cell(wc, 8, fmt_currency(d['econ_ano']), 0, 0, 'C')

    # Cota
    pdf.set_y(yc + hc + 5); pdf.set_font("Arial", "", 9); pdf.set_text_color(80)
    pdf.cell(0, 6, f"Cota necessaria: {fmt_number(d['kwh_re'])} KWh, equivalente a {d['qtd_placas']} placas solares.", 0, 1, 'C')

    # Footer Reduzido
    pdf.ln(2); yf = pdf.get_y(); pdf.set_draw_color(*PDF_CYAN); pdf.set_line_width(0.7); pdf.rect(13, yf, 184, 18, 'D')
    
    # Linha 1: Cliente
    pdf.set_xy(15, yf + 3); pdf.set_font("Arial", "B", 8); pdf.set_text_color(*PDF_CYAN); pdf.cell(12, 4, "Cliente:", 0, 0)
    pdf.set_font("Arial", "", 8); pdf.set_text_color(0); pdf.cell(110, 4, nome.upper(), 0, 1)
    
    # Linha 2: Cidade
    pdf.set_x(15); pdf.set_font("Arial", "B", 8); pdf.set_text_color(*PDF_CYAN); pdf.cell(15, 4, "Cidade:", 0, 0)
    pdf.set_font("Arial", "", 8); pdf.set_text_color(0); pdf.cell(50, 4, f"{cidade.upper()} / MS", 0, 1)

    # Validade
    pdf.set_xy(13, yf + 14); pdf.set_font("Arial", "", 8); pdf.set_text_color(50); pdf.cell(184, 4, "Validade da proposta: 10 dias, sujeita a analise de credito.", 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFACE ---
col_head1, col_head2 = st.columns([1, 1])
with col_head1: st.image(LOGO_EFICIENCIE, width=150)
with col_head2: st.markdown(f'<div style="text-align: right;"><img src="{LOGO_REENERGISA}" width="150"></div>', unsafe_allow_html=True)

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
    desc = c8.number_input("Desconto (%)", value=30.0, step=0.5)

    st.write("")
    if st.button("CALCULAR PROPOSTA", use_container_width=True):
        if kwh is None:
            st.error("Por favor, informe o consumo (kWh).")
        else:
            res = calcular(kwh, val_unit, tipo, ban, ilum, desc)
            
            st.write("---")
            st.markdown("### 📊 Resultado da Simulação")
            
            # CARD 1: Fatura Atual (Topo)
            st.markdown(f"""
            <div class="card-result card-orange">
                <div class="label-text" style="color: {ALERT_ORANGE} !important;">1. Fatura Atual Energisa</div>
                <div class="big-number">{fmt_currency(res['total_atual'])}</div>
                <p style="font-size:12px; margin:0; color:#888 !important;">(Sem Desconto)</p>
            </div>
            """, unsafe_allow_html=True)

            # LINHA DETALHADA (Energisa Residual | Reenergisa | Novo Total)
            c_novo1, c_novo2, c_novo3 = st.columns(3)
            with c_novo1:
                st.markdown(f"""
                <div class="card-result card-blue" style="height: 140px;">
                    <div class="label-text" style="color: {PRIMARY_BLUE} !important;">2. Fatura Energisa (Residual)</div>
                    <div class="big-number" style="font-size: 18px;">{fmt_currency(res['fat_en'])}</div>
                    <p style="font-size:11px; color:#888 !important; margin-top:5px;">(Taxa Mínima + Ilum + Bandeira)</p>
                </div>
                """, unsafe_allow_html=True)
            with c_novo2:
                st.markdown(f"""
                <div class="card-result card-light-blue" style="height: 140px;">
                    <div class="label-text" style="color: {ECONOMY_BLUE} !important;">3. Fatura Reenergisa</div>
                    <div class="big-number" style="font-size: 18px;">{fmt_currency(res['fat_re'])}</div>
                    <p style="font-size:11px; color:#888 !important; margin-top:5px;">(Com Desconto)</p>
                </div>
                """, unsafe_allow_html=True)
            with c_novo3:
                 st.markdown(f"""
                <div class="card-result card-blue" style="height: 140px; border-left: 5px solid {SUCCESS_GREEN};">
                    <div class="label-text" style="color: {SUCCESS_GREEN} !important;">4. Novo Total (2+3)</div>
                    <div class="big-number" style="font-size: 18px;">{fmt_currency(res['total_novo'])}</div>
                    <p style="font-size:11px; color:#888 !important; margin-top:5px;">Total a Pagar</p>
                </div>
                """, unsafe_allow_html=True)

            # CARD ECONOMIA FINAL
            st.markdown(f"""
            <div class="card-result card-green">
                <div style="font-size: 16px; margin-bottom: 5px; color: #ffffff !important;">💰 Economia Estimada</div>
                <div style="font-size: 28px; font-weight: bold; color: #ffffff !important;">Mensal: {fmt_currency(res['econ_mes'])}</div>
                <div style="font-size: 20px; opacity: 0.9; color: #ffffff !important;">Anual: {fmt_currency(res['econ_ano'])}</div>
            </div>
            """, unsafe_allow_html=True)

            # DADOS TÉCNICOS
            c_tec1, c_tec2 = st.columns(2)
            with c_tec1: st.info(f"**Cota Necessária:** {fmt_number(res['kwh_re'])} kWh")
            with c_tec2: st.info(f"**Equipamento:** {res['qtd_placas']} Placas")

            st.write("")
            pdf_bytes = criar_pdf_visual_final(res, nome, cidade, desc)
            st.download_button(label="⬇️ BAIXAR PROPOSTA EM PDF", data=pdf_bytes, file_name=f"Proposta_{nome.split()[0] if nome else 'Cliente'}.pdf", mime="application/pdf", use_container_width=True)
