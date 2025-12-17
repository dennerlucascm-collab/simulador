import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import tempfile
import os
from datetime import datetime

# --- 1. CONFIGURAÇÕES VISUAIS ---
st.set_page_config(page_title="Simulador Reenergisa", page_icon="☀️", layout="centered")

BG_COLOR = "#fdf1db"
PRIMARY_BLUE = "#26628d"
ECONOMY_BLUE = "#4a90e2"
ALERT_ORANGE = "#e67e22"
SUCCESS_GREEN = "#28a745"

LOGO_EFICIENCIE = "https://i.postimg.cc/WzKTZg47/LOGO-COMPLETA-removebg-preview.png"
LOGO_REENERGISA = "https://i.postimg.cc/nzHb5T5v/LOGO-positivo-reenergisa-2000x674.png"

# Ícones Icons8 (Links diretos para PNG branco)
ICON_SOLAR = "https://img.icons8.com/ios-filled/50/ffffff/solar-panel.png"
ICON_PIGGY = "https://img.icons8.com/ios-filled/50/ffffff/money-box.png"
ICON_BULB =  "https://img.icons8.com/ios-filled/50/ffffff/light-on.png"
ICON_PLANT = "https://img.icons8.com/ios-filled/50/ffffff/potted-plant.png"
ICON_FILE =  "https://img.icons8.com/ios-filled/50/ffffff/checked--v1.png"

ICONS_LIST = [ICON_SOLAR, ICON_PIGGY, ICON_BULB, ICON_PLANT, ICON_FILE]
ICONS_FALLBACK = ["S", "$", "!", "Y", "V"] # Letras caso a imagem falhe

PDF_CYAN = (0, 158, 224); PDF_LIME = (195, 213, 0); PDF_ORANGE = (243, 112, 33)

def fmt_currency(val): return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_number(val): return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# CSS Reforçado
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
    
    /* Card Verde com Texto Branco Forçado */
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
        # User-Agent de navegador real para evitar bloqueio
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        def safe_image(url, x, y, w):
            try:
                r = requests.get(url, headers=headers, timeout=5)
                if r.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(r.content); tmp_name = tmp.name
                    self.image(tmp_name, x, y, w); os.unlink(tmp_name)
            except: pass

        safe_image(LOGO_EFICIENCIE, 10, 5, 35)
        safe_image(LOGO_REENERGISA, 140, 6, 55)

    def footer(self):
        self.set_y(-12); self.set_font('Arial', 'I', 6); self.set_text_color(150); self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def criar_pdf_visual_final(d, nome, cidade, desconto):
    pdf = PDFOficial(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
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
        cx = centers[i]
        # Círculo
        pdf.set_fill_color(*PDF_CYAN); pdf.ellipse(cx-8, y_icons, 16, 16, 'F')
        
        # Tenta baixar imagem, senão desenha letra (Fallback)
        success = False
        try:
            r = requests.get(ICONS_LIST[i], headers=headers, timeout=4)
            if r.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(r.content); tmp_name = tmp.name
                pdf.image(tmp_name, cx-4, y_icons+4, 8, 8); os.unlink(tmp_name)
                success = True
        except: pass
        
        # Se falhou, coloca uma letra branca no meio
        if not success:
            pdf.set_xy(cx-8, y_icons+4)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(16, 8, ICONS_FALLBACK[i], 0, 0, 'C')
            pdf.set_text_color(80) # Volta cor normal
            pdf.set_font("Arial", "", 7)

        pdf.set_xy(cx-15, y_icons + 18); pdf.multi_cell(30, 3, t, 0, 'C')

    # Como Funciona
    y_steps = y_icons + 35; pdf.set_xy(0, y_steps - 6); pdf.set_font("Arial", "B", 10); pdf.set_text_color(*PDF_CYAN); pdf.cell(0, 6, "Veja como funciona:", 0, 1, 'C')
    steps = ["1. Nos instalamos os paineis solares nas nossas usinas", "2. A luz solar e convertida em energia eletrica", "3. Voce adquire uma cota de acordo com seu consumo", "4. A energia injetada vira credito na sua conta"]
    bw = 42; sx = 13; gp = 4; pdf.set_font("Arial", "", 8); pdf.set_text_color(255)
    for i, t in enumerate(steps):
        cx = sx + (i * (bw + gp)); pdf.set_fill_color(*PDF_CYAN); pdf.rect(cx, y_steps, bw, 22, 'F')
        pdf.set_xy(cx + 2, y_steps + 3); pdf.multi_cell(bw - 4, 3.5, t, 0, 'C')

    # Titulo e Dados
    yp = y_steps + 30; pdf.set_xy(0, yp); pdf.set_font("Arial", "B", 12); pdf.set_text_color(*PDF_CYAN); pdf.cell(0, 8, "Proposta Comercial de Locacao de Usina Fotovoltaica", 0, 1, 'C')
    yb = pdf.get_y() + 2; pdf.set_draw_color(*PDF_CYAN); pdf.set_line_width(0.5); pdf.rect(13, yb, 184, 12)
    pdf.set_xy(15, yb + 3); pdf.set_font("Arial", "", 9); pdf.set_text_color(*PDF_CYAN); pdf.cell(40, 5, "N cliente ENERGISA MATO", 0, 1)

    # Cards
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

    # Footer
    pdf.ln(2); yf = pdf.get_y(); pdf.set_draw_color(*PDF_CYAN); pdf.set_line_width(0.7); pdf.rect(13, yf, 184, 18, 'D')
    pdf.set_xy(15, yf + 3); pdf.set_font("Arial", "B", 8); pdf.set_text_color(*PDF_CYAN); pdf.cell(12, 4, "Cliente:", 0, 0)
    pdf.set_font("Arial", "", 8); pdf.set_text_color(0); pdf.cell(110, 4, nome.upper(), 0, 1)
    pdf.set_x(15); pdf.set_font("Arial", "B", 8); pdf.set_text_color(*PDF_CYAN); pdf.cell(15, 4, "Cidade:", 0, 0)
    pdf.set_font("Arial", "", 8); pdf.set_text_color(0); pdf.cell(50, 4, f"{cidade.upper()} / MS", 0, 1)
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
            
            # Card 1
            st.markdown(f"""
            <div class="card-result card-orange">
                <div class="label-text" style="color: {ALERT_ORANGE} !important;">1. Fatura Atual Energisa</div>
                <div class="big-number">{fmt_currency(res['total_atual'])}</div>
                <p style="font-size:12px; margin:0; color:#888 !important;">(Sem Desconto)</p>
            </div>
            """, unsafe_allow_html=True)

            # Detalhes
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="card-result card-blue" style="height: 140px;">
                    <div class="label-text" style="color: {PRIMARY_BLUE} !important;">2. Fatura Energisa (Residual)</div>
                    <div class="big-number" style="font-size: 18px;">{fmt_currency(res['fat_en'])}</div>
                    <p style="font-size:11px; color:#888 !important; margin-top:5px;">(Taxa Mínima + Ilum + Bandeira)</p>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="card-result card-light-blue" style="height: 140px;">
                    <div class="label-text" style="color: {ECONOMY_BLUE} !important;">3. Fatura Reenergisa</div>
                    <div class="big-number" style="font-size: 18px;">{fmt_currency(res['fat_re'])}</div>
                    <p style="font-size:11px; color:#888 !important; margin-top:5px;">(Energia com Desconto)</p>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                 st.markdown(f"""
                <div class="card-result card-blue" style="height: 140px; border-left: 5px solid {SUCCESS_GREEN};">
                    <div class="label-text" style="color: {SUCCESS_GREEN} !important;">4. Novo Total (2+3)</div>
                    <div class="big-number" style="font-size: 18px;">{fmt_currency(res['total_novo'])}</div>
                    <p style="font-size:11px; color:#888 !important; margin-top:5px;">Total a Pagar</p>
                </div>
                """, unsafe_allow_html=True)

            # Economia (Verde)
            st.markdown(f"""
            <div class="card-result card-green">
                <div style="font-size: 16px; margin-bottom: 5px; color: #ffffff !important;">💰 Economia Estimada</div>
                <div style="font-size: 28px; font-weight: bold; color: #ffffff !important;">Mensal: {fmt_currency(res['econ_mes'])}</div>
                <div style="font-size: 20px; opacity: 0.9; color: #ffffff !important;">Anual: {fmt_currency(res['econ_ano'])}</div>
            </div>
            """, unsafe_allow_html=True)

            c_tec1, c_tec2 = st.columns(2)
            with c_tec1: st.info(f"**Cota Necessária:** {fmt_number(res['kwh_re'])} kWh")
            with c_tec2: st.info(f"**Equipamento:** {res['qtd_placas']} Placas")

            st.write("")
            pdf_bytes = criar_pdf_visual_final(res, nome, cidade, desc)
            st.download_button(label="⬇️ BAIXAR PROPOSTA EM PDF", data=pdf_bytes, file_name=f"Proposta_{nome.split()[0] if nome else 'Cliente'}.pdf", mime="application/pdf", use_container_width=True)
