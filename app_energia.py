import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import tempfile
import os
from datetime import datetime

# --- 1. CONFIGURAÇÕES VISUAIS ---
st.set_page_config(page_title="Simulador Eficiencie", page_icon="☀️", layout="centered")

# NOVA PALETA DE CORES EFICIENCIE (Baseado na logo: Azul Escuro e Vermelho)
BG_COLOR = "#F4F7F6"         # Fundo cinza super claro/moderno
PRIMARY_BLUE = "#0a3a64"     # Azul escuro da logo
PRIMARY_RED = "#d31212"      # Vermelho da logo
TEXT_COLOR = "#2C3E50"
SUCCESS_GREEN = "#27ae60"

# ATENÇÃO: Suba a imagem nova no Postimages e troque este link se necessário
LOGO_URL = "https://i.postimg.cc/WzKTZg47/LOGO-COMPLETA-removebg-preview.png"

# Ícones Icons8 (Links diretos para PNG branco)
ICON_SOLAR = "https://img.icons8.com/ios-filled/50/ffffff/solar-panel.png"
ICON_PIGGY = "https://img.icons8.com/ios-filled/50/ffffff/money-box.png"
ICON_BULB =  "https://img.icons8.com/ios-filled/50/ffffff/light-on.png"
ICON_PLANT = "https://img.icons8.com/ios-filled/50/ffffff/potted-plant.png"
ICON_FILE =  "https://img.icons8.com/ios-filled/50/ffffff/checked--v1.png"

ICONS_LIST = [ICON_SOLAR, ICON_PIGGY, ICON_BULB, ICON_PLANT, ICON_FILE]
ICONS_FALLBACK = ["S", "$", "!", "Y", "V"] 

# Cores para o PDF
PDF_BLUE = (10, 58, 100)
PDF_RED = (211, 18, 18)
PDF_GRAY = (240, 240, 240)

def fmt_currency(val): return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_number(val): return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# CSS Customizado - Visual Premium
st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_COLOR}; }}
    h1, h2, h3, h4, p, div, span, label, li {{ color: {TEXT_COLOR} !important; font-family: 'Segoe UI', sans-serif; }}
    
    /* Títulos em Azul */
    h1, h2, h3 {{ color: {PRIMARY_BLUE} !important; font-weight: 700; }}
    
    /* Inputs Estilizados */
    .stTextInput input, .stNumberInput input, .stSelectbox div {{ 
        border-radius: 6px !important;
        border: 1px solid #BDC3C7 !important;
        background-color: #ffffff !important; 
        color: {PRIMARY_BLUE} !important;
    }}
    
    /* Botão Principal */
    div.stButton > button {{ 
        background-color: {PRIMARY_RED} !important; 
        color: #ffffff !important; 
        border-radius: 8px; 
        height: 55px; 
        font-weight: 800; 
        font-size: 16px;
        text-transform: uppercase; 
        border: none; 
        width: 100%;
        box-shadow: 0 4px 6px rgba(211, 18, 18, 0.3);
        transition: all 0.3s ease;
    }}
    div.stButton > button:hover {{
        background-color: #a80f0f !important;
        box-shadow: 0 6px 8px rgba(211, 18, 18, 0.4);
    }}
    div.stButton > button p {{ color: #ffffff !important; font-size: 16px; }}
    
    /* Cards de Resultado */
    .card-result {{ 
        padding: 20px; 
        border-radius: 12px; 
        text-align: center; 
        margin-bottom: 15px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
        background-color: white; 
    }}
    .card-red {{ border-top: 5px solid {PRIMARY_RED}; }}
    .card-blue {{ border-top: 5px solid {PRIMARY_BLUE}; }}
    
    /* Card de Economia (Destaque Maior) */
    .card-green {{ 
        background: linear-gradient(135deg, {PRIMARY_BLUE}, #12548c) !important; 
        box-shadow: 0 8px 20px rgba(10, 58, 100, 0.2);
    }}
    .card-green div, .card-green h2, .card-green p, .card-green span {{ color: #ffffff !important; }}
    .card-green .highlight {{ color: #f1c40f !important; font-weight: 900; }} /* Amarelo ouro para contraste */
    
    .big-number {{ font-size: 24px; font-weight: 800; margin: 8px 0; color: {PRIMARY_BLUE} !important; }}
    .label-text {{ font-size: 13px; font-weight: 700; text-transform: uppercase; color: #7F8C8D !important; letter-spacing: 0.5px; }}
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

# --- 3. PDF PREMIUM EFICIENCIE ---
class PDFOficial(FPDF):
    def header(self):
        # Faixa superior azul escuro
        self.set_fill_color(*PDF_BLUE)
        self.rect(0, 0, 210, 35, 'F')
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        def safe_image(url, x, y, w):
            try:
                r = requests.get(url, headers=headers, timeout=5)
                if r.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(r.content); tmp_name = tmp.name
                    self.image(tmp_name, x, y, w); os.unlink(tmp_name)
            except: pass

        # Fundo branco sutil atrás da logo para destacar
        self.set_fill_color(255, 255, 255)
        self.rect(8, 4, 45, 27, 'F')
        safe_image(LOGO_URL, 10, 6, 41)
        
        # Título no cabeçalho
        self.set_y(15)
        self.set_font("Arial", "B", 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 5, "ESTUDO DE VIABILIDADE ECONOMICA", 0, 1, 'R')

    def footer(self):
        self.set_y(-15)
        self.set_fill_color(*PDF_BLUE)
        self.rect(0, 285, 210, 15, 'F')
        self.set_font('Arial', 'B', 8)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'Eficiencie - Solucoes em Energia Inteligente', 0, 0, 'C')

def criar_pdf_visual_final(d, nome, cidade, desconto, uc):
    pdf = PDFOficial(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Subtítulo Vermelho
    pdf.set_y(42)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*PDF_RED)
    pdf.cell(0, 8, "Energia solar sem investimento? Saiba como isso e possivel.", 0, 1, 'C')
    pdf.set_draw_color(*PDF_RED)
    pdf.line(15, 51, 195, 51)
    
    # Ícones (Textos originais mantidos)
    pdf.ln(6)
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(*PDF_BLUE)
    pdf.cell(0, 6, "Conheca os beneficios da Geracao Compartilhada:", 0, 1, 'C')
    y_icons = pdf.get_y() + 4; centers = [25, 65, 105, 145, 185]
    txts = ["Sem instalacao\nde equipamentos", "Sem preocupacao\ncom manutencao", "Economia na\nconta de energia", "Energia limpa\ne sustentavel", "Sem fidelidade apos\no cumprimento\ndo aviso previo"]
    
    pdf.set_font("Arial", "", 7); pdf.set_text_color(80)
    for i, t in enumerate(txts):
        cx = centers[i]
        pdf.set_fill_color(*PDF_BLUE); pdf.ellipse(cx-9, y_icons, 18, 18, 'F') # Círculos ligeiramente maiores
        
        success = False
        try:
            r = requests.get(ICONS_LIST[i], headers=headers, timeout=4)
            if r.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(r.content); tmp_name = tmp.name
                pdf.image(tmp_name, cx-5, y_icons+4, 10, 10); os.unlink(tmp_name)
                success = True
        except: pass
        
        if not success:
            pdf.set_xy(cx-9, y_icons+5); pdf.set_text_color(255); pdf.set_font("Arial", "B", 11)
            pdf.cell(18, 8, ICONS_FALLBACK[i], 0, 0, 'C'); pdf.set_text_color(80); pdf.set_font("Arial", "", 7)
        pdf.set_xy(cx-16, y_icons + 20); pdf.multi_cell(32, 3.5, t, 0, 'C')

    # Como Funciona
    y_steps = y_icons + 38; pdf.set_xy(0, y_steps - 6); pdf.set_font("Arial", "B", 11); pdf.set_text_color(*PDF_BLUE); pdf.cell(0, 6, "Veja como funciona:", 0, 1, 'C')
    steps = ["1. Nos instalamos os paineis solares nas nossas usinas", "2. A luz solar e convertida em energia eletrica", "3. Voce adquire uma cota de acordo com seu consumo", "4. A energia injetada vira credito na sua conta"]
    bw = 42; sx = 13; gp = 4; pdf.set_font("Arial", "", 8); pdf.set_text_color(255)
    for i, t in enumerate(steps):
        cx = sx + (i * (bw + gp))
        pdf.set_fill_color(*PDF_BLUE)
        pdf.rect(cx, y_steps, bw, 22, 'F')
        pdf.set_xy(cx + 2, y_steps + 3); pdf.multi_cell(bw - 4, 4, t, 0, 'C')

    # Titulo e Dados Resumo
    yp = y_steps + 32; pdf.set_xy(0, yp); pdf.set_font("Arial", "B", 13); pdf.set_text_color(*PDF_BLUE); pdf.cell(0, 8, "Proposta Comercial de Locacao de Usina Fotovoltaica", 0, 1, 'C')
    
    yb = pdf.get_y() + 2; 
    pdf.set_fill_color(*PDF_GRAY); pdf.set_draw_color(*PDF_BLUE); pdf.set_line_width(0.5)
    pdf.rect(13, yb, 184, 12, 'FD') # Fundo cinza claro
    pdf.set_xy(15, yb + 3); pdf.set_font("Arial", "B", 10); pdf.set_text_color(*PDF_BLUE)
    
    texto_uc = f"N cliente {uc}" if uc else "N cliente"
    pdf.cell(40, 6, texto_uc, 0, 1)

    # Cards Redesenhados
    yc = yb + 18; wc = 58; hc = 30; xc = 13; espaco = 5
    
    # Card 1 - Media
    pdf.set_draw_color(*PDF_BLUE); pdf.set_line_width(0.5); pdf.rect(xc, yc, wc, hc, 'D')
    pdf.set_fill_color(*PDF_BLUE); pdf.rect(xc, yc, wc, 8, 'F')
    pdf.set_xy(xc, yc + 1); pdf.set_font("Arial", "B", 9); pdf.set_text_color(255); pdf.cell(wc, 6, "Media* (R$)", 0, 2, 'C')
    pdf.set_font("Arial", "", 7); pdf.set_text_color(100); pdf.set_y(yc + 10); pdf.cell(wc, 4, "(sem contratacao de GD)", 0, 2, 'C')
    pdf.ln(2); pdf.set_font("Arial", "B", 14); pdf.set_text_color(*PDF_BLUE); pdf.cell(wc, 8, fmt_currency(d['total_atual']), 0, 0, 'C')
    
    # Card 2 - Desconto
    xc += wc + espaco; pdf.set_draw_color(*PDF_BLUE); pdf.rect(xc, yc, wc, hc, 'D')
    pdf.set_fill_color(*PDF_BLUE); pdf.rect(xc, yc, wc, 8, 'F')
    pdf.set_xy(xc, yc + 1); pdf.set_font("Arial", "B", 9); pdf.set_text_color(255); pdf.cell(wc, 6, "Economia Ofertada", 0, 2, 'C')
    pdf.set_font("Arial", "B", 9); pdf.set_text_color(*PDF_RED); pdf.set_y(yc + 11); pdf.cell(wc, 6, f"Previo: {desconto:.1f}%", 0, 2, 'C')
    pdf.set_font("Arial", "", 7); pdf.set_text_color(100); pdf.cell(wc, 4, "% sobre credito compensado", 0, 0, 'C')
    
    # Card 3 - Anual (Destaque Vermelho)
    xc += wc + espaco; pdf.set_draw_color(*PDF_RED); pdf.rect(xc, yc, wc, hc, 'D')
    pdf.set_fill_color(*PDF_RED); pdf.rect(xc, yc, wc, 8, 'F')
    pdf.set_xy(xc, yc + 1); pdf.set_font("Arial", "B", 9); pdf.set_text_color(255); pdf.cell(wc, 6, "Economia Anual Projetada", 0, 2, 'C')
    pdf.ln(6); pdf.set_x(xc); pdf.set_font("Arial", "B", 15); pdf.set_text_color(*PDF_RED); pdf.cell(wc, 10, fmt_currency(d['econ_ano']), 0, 0, 'C')

    # Cota
    pdf.set_y(yc + hc + 8); pdf.set_font("Arial", "B", 10); pdf.set_text_color(*PDF_BLUE)
    pdf.cell(0, 6, f"Cota necessaria: {fmt_number(d['kwh_re'])} KWh, equivalente a {d['qtd_placas']} placas solares.", 0, 1, 'C')

    # Dados de Validade
    pdf.set_y(260); pdf.set_draw_color(*PDF_BLUE); pdf.set_line_width(0.5); pdf.rect(13, 260, 184, 18, 'D')
    pdf.set_xy(15, 262); pdf.set_font("Arial", "B", 8); pdf.set_text_color(*PDF_BLUE); pdf.cell(15, 5, "Cliente:", 0, 0)
    pdf.set_font("Arial", "", 8); pdf.set_text_color(50); pdf.cell(105, 5, nome.upper(), 0, 1)
    
    pdf.set_x(15); pdf.set_font("Arial", "B", 8); pdf.set_text_color(*PDF_BLUE); pdf.cell(15, 5, "Cidade:", 0, 0)
    pdf.set_font("Arial", "", 8); pdf.set_text_color(50); pdf.cell(50, 5, f"{cidade.upper()}", 0, 1)
    
    pdf.set_xy(13, 272); pdf.set_font("Arial", "I", 8); pdf.set_text_color(100); pdf.cell(184, 5, "Validade da proposta: 10 dias, sujeita a analise de credito.", 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFACE DO SITE ---
st.markdown(f"<div style='text-align: center;'><img src='{LOGO_URL}' width='250'></div>", unsafe_allow_html=True)
st.markdown(f"<h2 style='text-align: center; color: {PRIMARY_BLUE}; margin-top: 15px;'>Simulador de Inteligência Energética</h2>", unsafe_allow_html=True)
st.write("---")

with st.container():
    st.markdown("### 👤 1. Dados do Cliente")
    c1, c2, c3 = st.columns(3)
    nome = c1.text_input("Nome", value="")
    cidade = c2.text_input("Cidade", value="")
    tipo = c3.selectbox("Tipo de Ligação", ["Trifásico", "Bifásico", "Monofásico"])
    
    st.markdown("### 📄 2. Dados da Fatura")
    c_uc, c4, c5 = st.columns(3)
    uc = c_uc.text_input("UC (Unidade Consumidora)", value="", placeholder="Ex: 123456")
    kwh = c4.number_input("Consumo (kWh)", min_value=0.0, value=None, placeholder="Digite o kWh...")
    val_unit = c5.number_input("Valor Unitário (R$)", min_value=0.0, value=1.1540, format="%.4f")
    
    c6, c7, c8 = st.columns(3)
    ban = c6.number_input("Bandeiras (R$)", min_value=0.0, value=None, placeholder="R$ 0,00")
    ilum = c7.number_input("Ilum. Púb. (R$)", min_value=0.0, value=None, placeholder="R$ 0,00")
    desc = c8.number_input("Desconto (%)", value=30.0, step=0.5)

    st.write("")
    if st.button("CALCULAR PROPOSTA EFICIENCIE", use_container_width=True):
        if kwh is None or kwh == 0:
            st.error("⚠️ Por favor, informe o consumo (kWh) válido para realizar o cálculo.")
        else:
            res = calcular(kwh, val_unit, tipo, ban, ilum, desc)
            st.write("---")
            st.markdown("### 📊 Resultado da Simulação")
            
            # Card Fatura Atual
            st.markdown(f"""
            <div class="card-result card-red">
                <div class="label-text">1. Fatura Atual Sem Desconto</div>
                <div class="big-number" style="color: {PRIMARY_RED} !important;">{fmt_currency(res['total_atual'])}</div>
                <p style="font-size:12px; margin:0; color:#888 !important;">Custo estimado mantendo a distribuidora</p>
            </div>
            """, unsafe_allow_html=True)

            # Detalhes Financeiros
            c_res1, c_res2, c_res3 = st.columns(3)
            with c_res1:
                st.markdown(f"""
                <div class="card-result card-blue" style="height: 155px;">
                    <div class="label-text">2. Taxa Distribuidora</div>
                    <div class="big-number" style="font-size: 18px;">{fmt_currency(res['fat_en'])}</div>
                    <p style="font-size:11px; color:#888 !important; margin-top:5px;">(Custo de Disp. + Ilum + Band)</p>
                </div>
                """, unsafe_allow_html=True)
            with c_res2:
                st.markdown(f"""
                <div class="card-result card-blue" style="height: 155px;">
                    <div class="label-text">3. Fatura Eficiencie</div>
                    <div class="big-number" style="font-size: 18px;">{fmt_currency(res['fat_re'])}</div>
                    <p style="font-size:11px; color:#888 !important; margin-top:5px;">(Energia Limpa com Desconto)</p>
                </div>
                """, unsafe_allow_html=True)
            with c_res3:
                 st.markdown(f"""
                <div class="card-result card-blue" style="height: 155px; border-top: 5px solid {SUCCESS_GREEN};">
                    <div class="label-text">4. Novo Total a Pagar</div>
                    <div class="big-number" style="font-size: 20px; color: {SUCCESS_GREEN} !important;">{fmt_currency(res['total_novo'])}</div>
                    <p style="font-size:11px; color:#888 !important; margin-top:5px;">Soma dos itens 2 e 3</p>
                </div>
                """, unsafe_allow_html=True)

            # Economia Destacada
            st.markdown(f"""
            <div class="card-result card-green">
                <div style="font-size: 14px; font-weight:700; letter-spacing: 1px; margin-bottom: 10px;">💰 ECONOMIA ESTIMADA COM A EFICIENCIE</div>
                <div style="font-size: 38px; font-weight: 900; margin-bottom: 5px;" class="highlight">{fmt_currency(res['econ_ano'])} <span style="font-size:16px; font-weight:normal; color:#ddd;">/ano</span></div>
                <div style="font-size: 18px; font-weight: 600;">{fmt_currency(res['econ_mes'])} <span style="font-size:14px; font-weight:normal; color:#ccc;">/mês</span></div>
            </div>
            """, unsafe_allow_html=True)

            # Dados Técnicos
            c_tec1, c_tec2 = st.columns(2)
            with c_tec1: st.info(f"⚡ **Cota Necessária:** {fmt_number(res['kwh_re'])} kWh")
            with c_tec2: st.info(f"☀️ **Equipamento:** {res['qtd_placas']} Placas")

            st.write("")
            pdf_bytes = criar_pdf_visual_final(res, nome, cidade, desc, uc)
            st.download_button(
                label="⬇️ GERAR PROPOSTA COMERCIAL (PDF)", 
                data=pdf_bytes, 
                file_name=f"Proposta_Eficiencie_{nome.split()[0] if nome else 'Cliente'}.pdf", 
                mime="application/pdf", 
                use_container_width=True
            )
