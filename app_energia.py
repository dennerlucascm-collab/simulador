import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import tempfile
import os
from datetime import datetime, timedelta

# ============================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(page_title="Simulador Reenergisa | Eficiencie", page_icon="☀️", layout="centered")

# ------------------------------------------------------------
# PALETA DE CORES — baseada na identidade visual da Eficiencie
# (azul marinho + vermelho da logo, com azul do painel solar)
# ------------------------------------------------------------
BG_COLOR       = "#F3F6FA"   # Cinza muito claro (neutro, profissional)
CARD_BG        = "#FFFFFF"
NAVY           = "#0B2545"   # Azul marinho principal (texto "Eficiencie")
NAVY_LIGHT     = "#123A6B"
BLUE_ACCENT    = "#1E6FD9"   # Azul do painel solar / telefone
RED_ACCENT     = "#E4032E"   # Vermelho da logo
SUCCESS_GREEN  = "#12A150"
ALERT_ORANGE   = "#E67E22"
GRAY_TEXT      = "#5A6B7B"

# Links / caminhos de imagens
LOGO_EFICIENCIE_LOCAL = "assets/logo_eficiencie.png"
LOGO_EFICIENCIE_URL   = "https://i.postimg.cc/WzKTZg47/LOGO-COMPLETA-removebg-preview.png"
LOGO_REENERGISA       = "https://i.postimg.cc/nzHb5T5v/LOGO-positivo-reenergisa-2000x674.png"

# Ícones brancos usados no PDF (Google Material Icons)
ICON_SOLAR = "https://raw.githubusercontent.com/google/material-design-icons/master/png/image/wb_sunny/materialicons/48dp/2x/baseline_wb_sunny_white_48dp.png"
ICON_PIGGY = "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/savings/materialicons/48dp/2x/baseline_savings_white_48dp.png"
ICON_BULB  = "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/lightbulb/materialicons/48dp/2x/baseline_lightbulb_white_48dp.png"
ICON_PLANT = "https://raw.githubusercontent.com/google/material-design-icons/master/png/maps/local_florist/materialicons/48dp/2x/baseline_local_florist_white_48dp.png"
ICON_FILE  = "https://raw.githubusercontent.com/google/material-design-icons/master/png/action/verified/materialicons/48dp/2x/baseline_verified_white_48dp.png"
ICONS_LIST = [ICON_SOLAR, ICON_PIGGY, ICON_BULB, ICON_PLANT, ICON_FILE]

# Cores em RGB para o PDF (fpdf trabalha em tuplas 0-255)
PDF_NAVY   = (11, 37, 69)
PDF_BLUE   = (30, 111, 217)
PDF_RED    = (228, 3, 46)
PDF_GREEN  = (18, 161, 80)
PDF_GRAY   = (90, 107, 123)
PDF_LGRAY  = (243, 246, 250)

# ============================================================
# FORMATADORES
# ============================================================
def fmt_currency(val): return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_number(val):   return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ============================================================
# 2. CSS — INTERFACE DO CONSULTOR
# ============================================================
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
    .stApp {{ background-color: {BG_COLOR}; }}

    h1, h2, h3, h4 {{ color: {NAVY} !important; font-weight: 700 !important; }}
    p, div, span, label, li {{ color: {NAVY} !important; }}

    /* Cabeçalho com faixa gradiente */
    .header-banner {{
        background: linear-gradient(90deg, {NAVY} 0%, {NAVY_LIGHT} 60%, {BLUE_ACCENT} 100%);
        padding: 22px 28px;
        border-radius: 16px;
        margin-bottom: 22px;
        box-shadow: 0 6px 18px rgba(11,37,69,0.25);
        border-bottom: 4px solid {RED_ACCENT};
    }}
    .header-banner h1 {{ color: #FFFFFF !important; margin: 0; font-size: 26px; }}
    .header-banner p {{ color: #DCE6F5 !important; margin: 4px 0 0 0; font-size: 13px; }}

    /* Cartões de formulário */
    .form-card {{
        background-color: {CARD_BG};
        padding: 22px 24px;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(11,37,69,0.08);
        margin-bottom: 18px;
        border-top: 4px solid {BLUE_ACCENT};
    }}
    .section-title {{
        font-size: 15px; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.5px; color: {NAVY} !important;
        margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
    }}

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox div, .stRadio div {{
        color: {NAVY} !important; background-color: #FBFCFE !important;
    }}
    .stTextInput input, .stNumberInput input {{
        border: 1px solid #D7E0EA !important; border-radius: 8px !important;
    }}

    /* Botão principal */
    div.stButton > button {{
        background: linear-gradient(90deg, {RED_ACCENT} 0%, #C4021F 100%) !important;
        color: #ffffff !important;
        border-radius: 10px; height: 52px; font-weight: 700; letter-spacing: 0.5px;
        text-transform: uppercase; border: none; width: 100%;
        box-shadow: 0 4px 12px rgba(228,3,46,0.3);
        transition: all 0.2s ease-in-out;
    }}
    div.stButton > button p {{ color: #ffffff !important; }}
    div.stButton > button:hover {{ transform: translateY(-1px); box-shadow: 0 6px 16px rgba(228,3,46,0.4); }}

    div.stDownloadButton > button {{
        background: linear-gradient(90deg, {NAVY} 0%, {BLUE_ACCENT} 100%) !important;
        color: #ffffff !important;
        border-radius: 10px; height: 52px; font-weight: 700; letter-spacing: 0.5px;
        text-transform: uppercase; border: none; width: 100%;
        box-shadow: 0 4px 12px rgba(11,37,69,0.3);
    }}
    div.stDownloadButton > button p {{ color: #ffffff !important; }}

    /* Cartões de resultado */
    .card-result {{
        padding: 16px 14px; border-radius: 12px; text-align: center;
        margin-bottom: 12px; background-color: {CARD_BG};
        box-shadow: 0 2px 10px rgba(11,37,69,0.08);
    }}
    .card-orange     {{ border-top: 4px solid {ALERT_ORANGE}; }}
    .card-navy       {{ border-top: 4px solid {NAVY}; }}
    .card-blue       {{ border-top: 4px solid {BLUE_ACCENT}; }}
    .card-green-line {{ border-top: 4px solid {SUCCESS_GREEN}; }}

    .card-green {{
        background: linear-gradient(135deg, {SUCCESS_GREEN} 0%, #0C7A3C 100%);
        color: #ffffff !important; box-shadow: 0 6px 18px rgba(18,161,80,0.3);
    }}
    .card-green div, .card-green span {{ color: #ffffff !important; }}

    .big-number  {{ font-size: 21px; font-weight: 800; margin: 6px 0; color: {NAVY} !important; }}
    .label-text  {{ font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; color: {GRAY_TEXT} !important; }}
    .sub-text    {{ font-size: 11.5px; margin: 0; color: #93A2B3 !important; }}

    .info-pill {{
        background-color: {CARD_BG}; border-radius: 10px; padding: 12px 16px;
        box-shadow: 0 2px 8px rgba(11,37,69,0.07); border-left: 4px solid {BLUE_ACCENT};
    }}
    </style>
""", unsafe_allow_html=True)

# ============================================================
# 3. CÁLCULO (lógica de negócio mantida)
# ============================================================
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

    val_re_unit = valor_unit * (1 - (desc / 100))
    fat_re = kwh_re * val_re_unit

    total_novo = fat_en + fat_re

    econ_mes = total_atual - total_novo

    return {
        "total_atual": total_atual,
        "fat_en": fat_en,
        "fat_re": fat_re,
        "total_novo": total_novo,
        "econ_mes": econ_mes,
        "econ_ano": econ_mes * 12,
        "kwh_re": kwh_re,
        "qtd_placas": qtd_placas
    }

# ============================================================
# 4. PDF — PROPOSTA COMERCIAL
# ============================================================
def _baixar_temp(url, headers, timeout=6):
    """Baixa uma imagem para um arquivo temporário e retorna o caminho (ou None)."""
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            tmp.write(r.content)
            tmp.close()
            return tmp.name
    except Exception:
        pass
    return None


class PDFOficial(FPDF):
    def header(self):
        # Faixa navy no topo
        self.set_fill_color(*PDF_NAVY)
        self.rect(0, 0, 210, 26, 'F')
        # Filete vermelho
        self.set_fill_color(*PDF_RED)
        self.rect(0, 26, 210, 1.2, 'F')

        headers = {'User-Agent': 'Mozilla/5.0'}

        # Logo Eficiencie (prioriza arquivo local, cai para URL)
        try:
            if os.path.exists(LOGO_EFICIENCIE_LOCAL):
                self.image(LOGO_EFICIENCIE_LOCAL, 10, 4, 32)
            else:
                p = _baixar_temp(LOGO_EFICIENCIE_URL, headers)
                if p:
                    self.image(p, 10, 4, 32)
                    os.unlink(p)
        except Exception:
            pass

        # Logo Reenergisa
        try:
            p = _baixar_temp(LOGO_REENERGISA, headers)
            if p:
                self.image(p, 148, 6, 52)
                os.unlink(p)
        except Exception:
            pass

    def footer(self):
        self.set_y(-14)
        self.set_fill_color(*PDF_NAVY)
        self.rect(0, self.get_y(), 210, 14, 'F')
        self.set_font('Arial', '', 7)
        self.set_text_color(255)
        self.set_y(-10)
        self.cell(0, 6, f'Eficiencie  |  Proposta gerada em {datetime.now().strftime("%d/%m/%Y")}  |  Página {self.page_no()}', 0, 0, 'C')


def criar_pdf_visual_final(d, nome, cidade, desconto):
    pdf = PDFOficial()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    headers = {'User-Agent': 'Mozilla/5.0'}

    # ---------- Título principal ----------
    pdf.set_y(33)
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(*PDF_NAVY)
    pdf.cell(0, 9, "Proposta Comercial - Energia Solar por Assinatura", 0, 1, 'C')
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(*PDF_GRAY)
    pdf.cell(0, 6, "Geracao Compartilhada Reenergisa em parceria com Eficiencie", 0, 1, 'C')

    # ---------- Faixa de destaque ----------
    pdf.ln(2)
    y_faixa = pdf.get_y()
    pdf.set_fill_color(*PDF_RED)
    pdf.rect(13, y_faixa, 184, 9, 'F')
    pdf.set_xy(13, y_faixa + 1.7)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(255)
    pdf.cell(184, 6, "Energia solar sem investimento inicial. Saiba como isso e possivel.", 0, 1, 'C')

    # ---------- Benefícios (ícones) ----------
    pdf.ln(4)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*PDF_NAVY)
    pdf.cell(0, 6, "Conheca os beneficios da Geracao Compartilhada:", 0, 1, 'C')

    y_icons = pdf.get_y() + 3
    centers = [25, 65, 105, 145, 185]
    txts = [
        "Sem instalacao\nde equipamentos",
        "Sem preocupacao\ncom manutencao",
        "Economia na\nconta de energia",
        "Energia limpa\ne sustentavel",
        "Sem fidelidade apos\no cumprimento\ndo aviso previo",
    ]
    pdf.set_font("Arial", "", 7)
    pdf.set_text_color(*PDF_GRAY)
    for i, t in enumerate(txts):
        cx = centers[i]
        pdf.set_fill_color(*PDF_BLUE)
        pdf.ellipse(cx - 8, y_icons, 16, 16, 'F')
        p = _baixar_temp(ICONS_LIST[i], headers)
        if p:
            pdf.image(p, cx - 4, y_icons + 4, 8, 8)
            os.unlink(p)
        pdf.set_xy(cx - 15, y_icons + 18)
        pdf.multi_cell(30, 3, t, 0, 'C')

    # ---------- Como funciona ----------
    y_steps = y_icons + 36
    pdf.set_xy(0, y_steps - 6)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*PDF_NAVY)
    pdf.cell(0, 6, "Veja como funciona:", 0, 1, 'C')

    steps = [
        "1. Nos instalamos os paineis solares nas nossas usinas",
        "2. A luz solar e convertida em energia eletrica",
        "3. Voce adquire uma cota de acordo com seu consumo",
        "4. A energia injetada vira credito na sua conta",
    ]
    bw, sx, gp = 42, 13, 4
    pdf.set_font("Arial", "", 8)
    for i, t in enumerate(steps):
        cx = sx + (i * (bw + gp))
        cor = PDF_NAVY if i % 2 == 0 else PDF_BLUE
        pdf.set_fill_color(*cor)
        pdf.rect(cx, y_steps, bw, 22, 'F')
        pdf.set_text_color(255)
        pdf.set_xy(cx + 2, y_steps + 3)
        pdf.multi_cell(bw - 4, 3.5, t, 0, 'C')

    # ---------- Bloco: identificação do cliente ----------
    yp = y_steps + 30
    pdf.set_xy(13, yp)
    pdf.set_fill_color(*PDF_LGRAY)
    pdf.rect(13, yp, 184, 14, 'F')
    pdf.set_draw_color(*PDF_NAVY)
    pdf.set_line_width(0.3)
    pdf.rect(13, yp, 184, 14)

    pdf.set_xy(18, yp + 2.5)
    pdf.set_font("Arial", "B", 8.5)
    pdf.set_text_color(*PDF_NAVY)
    pdf.cell(18, 4.5, "Cliente:", 0, 0)
    pdf.set_font("Arial", "", 8.5)
    pdf.set_text_color(30)
    pdf.cell(90, 4.5, (nome.upper() if nome else "-"), 0, 0)

    pdf.set_font("Arial", "B", 8.5)
    pdf.set_text_color(*PDF_NAVY)
    pdf.cell(15, 4.5, "Cidade:", 0, 0)
    pdf.set_font("Arial", "", 8.5)
    pdf.set_text_color(30)
    pdf.cell(0, 4.5, f"{cidade.upper() if cidade else '-'} / MS", 0, 1)

    pdf.set_xy(18, yp + 8)
    pdf.set_font("Arial", "B", 8.5)
    pdf.set_text_color(*PDF_NAVY)
    pdf.cell(30, 4.5, "N cliente ENERGISA:", 0, 0)
    pdf.set_font("Arial", "", 8.5)
    pdf.set_text_color(30)
    pdf.cell(0, 4.5, "MATO GROSSO DO SUL", 0, 1)

    # ---------- Cards financeiros ----------
    yc = yp + 20
    wc = 60
    hc = 30
    xc = 13

    # Média atual
    pdf.set_fill_color(*PDF_LGRAY)
    pdf.rect(xc, yc, wc, hc, 'F')
    pdf.set_draw_color(230, 126, 34)
    pdf.set_line_width(0.8)
    pdf.rect(xc, yc, wc, 1.2, 'FD')
    pdf.set_xy(xc, yc + 4)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(230, 126, 34)
    pdf.cell(wc, 5, "Fatura Atual (R$)", 0, 2, 'C')
    pdf.set_font("Arial", "", 7)
    pdf.set_text_color(*PDF_GRAY)
    pdf.cell(wc, 4, "sem contratacao de GD", 0, 2, 'C')
    pdf.ln(2)
    pdf.set_font("Arial", "B", 15)
    pdf.set_text_color(40)
    pdf.cell(wc, 6, fmt_currency(d['total_atual']), 0, 0, 'C')

    # Economia ofertada
    xc += wc + 2
    pdf.set_fill_color(*PDF_LGRAY)
    pdf.rect(xc, yc, wc, hc, 'F')
    pdf.set_fill_color(*PDF_GREEN)
    pdf.rect(xc, yc, wc, 1.2, 'F')
    pdf.set_xy(xc, yc + 4)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*PDF_GREEN)
    pdf.cell(wc, 5, "Economia Ofertada", 0, 2, 'C')
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(40)
    pdf.cell(wc, 5, f"{desconto:.1f}%", 0, 2, 'C')
    pdf.set_font("Arial", "", 7)
    pdf.set_text_color(*PDF_GRAY)
    pdf.cell(wc, 4, "sobre credito compensado", 0, 0, 'C')

    # Economia anual
    xc += wc + 2
    pdf.set_fill_color(*PDF_LGRAY)
    pdf.rect(xc, yc, wc, hc, 'F')
    pdf.set_fill_color(*PDF_BLUE)
    pdf.rect(xc, yc, wc, 1.2, 'F')
    pdf.set_xy(xc, yc + 4)
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*PDF_BLUE)
    pdf.cell(wc, 5, "Economia Anual Projetada", 0, 2, 'C')
    pdf.ln(4)
    pdf.set_x(xc)
    pdf.set_font("Arial", "B", 15)
    pdf.set_text_color(40)
    pdf.cell(wc, 8, fmt_currency(d['econ_ano']), 0, 0, 'C')

    # ---------- Faixa de economia mensal (destaque total) ----------
    y_econ = yc + hc + 6
    pdf.set_fill_color(*PDF_GREEN)
    pdf.rect(13, y_econ, 184, 16, 'F')
    pdf.set_xy(13, y_econ + 3)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(255)
    pdf.cell(184, 6, f"Economia mensal estimada: {fmt_currency(d['econ_mes'])}", 0, 1, 'C')
    pdf.set_font("Arial", "", 8.5)
    pdf.cell(0, 4, f"Nova fatura total (Energisa + Reenergisa): {fmt_currency(d['total_novo'])}", 0, 1, 'C')

    # ---------- Detalhamento da nova fatura ----------
    y_det = y_econ + 22
    pdf.set_xy(13, y_det)
    pdf.set_font("Arial", "B", 9.5)
    pdf.set_text_color(*PDF_NAVY)
    pdf.cell(184, 5, "Composicao da nova fatura", 0, 1, 'C')

    wcol = 90
    pdf.set_xy(13, y_det + 6)
    pdf.set_fill_color(*PDF_LGRAY)
    pdf.rect(13, y_det + 6, wcol, 14, 'F')
    pdf.set_xy(15, y_det + 8)
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(*PDF_NAVY)
    pdf.cell(wcol - 4, 4, "Fatura Energisa (taxas + iluminacao)", 0, 1)
    pdf.set_x(15)
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(40)
    pdf.cell(wcol - 4, 5, fmt_currency(d['fat_en']), 0, 1)

    pdf.set_xy(13 + wcol + 4, y_det + 6)
    pdf.set_fill_color(*PDF_LGRAY)
    pdf.rect(13 + wcol + 4, y_det + 6, wcol, 14, 'F')
    pdf.set_xy(15 + wcol + 4, y_det + 8)
    pdf.set_font("Arial", "B", 8)
    pdf.set_text_color(*PDF_BLUE)
    pdf.cell(wcol - 4, 4, "Fatura Reenergisa (com desconto)", 0, 1)
    pdf.set_x(15 + wcol + 4)
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(40)
    pdf.cell(wcol - 4, 5, fmt_currency(d['fat_re']), 0, 1)

    # ---------- Dados técnicos ----------
    y_tec = y_det + 24
    pdf.set_xy(13, y_tec)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(*PDF_GRAY)
    pdf.cell(0, 6, f"Cota necessaria: {fmt_number(d['kwh_re'])} kWh, equivalente a {d['qtd_placas']} placas solares.", 0, 1, 'C')

    # ---------- Validade ----------
    validade = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
    y_val = y_tec + 8
    pdf.set_draw_color(*PDF_NAVY)
    pdf.set_line_width(0.5)
    pdf.rect(13, y_val, 184, 12)
    pdf.set_xy(13, y_val + 3.5)
    pdf.set_font("Arial", "", 8.5)
    pdf.set_text_color(*PDF_GRAY)
    pdf.cell(184, 5, f"Validade da proposta: 10 dias (ate {validade}), sujeita a analise de credito.", 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# ============================================================
# 5. INTERFACE — CONSULTOR
# ============================================================
logo_col_path = LOGO_EFICIENCIE_LOCAL if os.path.exists(LOGO_EFICIENCIE_LOCAL) else LOGO_EFICIENCIE_URL

col_head1, col_head2 = st.columns([1, 1])
with col_head1:
    st.image(logo_col_path, width=160)
with col_head2:
    st.markdown(f'<div style="text-align: right; padding-top: 10px;"><img src="{LOGO_REENERGISA}" width="150"></div>', unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-banner">
        <h1>☀️ Simulador Comercial de Energia Solar</h1>
        <p>Monte a proposta de economia do cliente e gere o PDF profissional em segundos.</p>
    </div>
""", unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">👤 1. Dados do Cliente</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    nome = c1.text_input("Nome", value="")
    cidade = c2.text_input("Cidade", value="")
    tipo = c3.radio("Tipo de Ligação", ["Trifásico", "Bifásico", "Monofásico"], horizontal=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🧾 2. Dados da Fatura</div>', unsafe_allow_html=True)
    c4, c5 = st.columns(2)
    kwh = c4.number_input("Consumo (kWh)", min_value=0.0, value=None, placeholder="Digite o kWh...")
    val_unit = c5.number_input("Valor Unitário (R$)", min_value=0.0, value=1.1540, format="%.4f")

    c6, c7, c8 = st.columns(3)
    ban = c6.number_input("Bandeiras (R$)", min_value=0.0, value=None, placeholder="R$ 0,00")
    ilum = c7.number_input("Ilum. Púb. (R$)", min_value=0.0, value=None, placeholder="R$ 0,00")
    desc = c8.number_input("Desconto (%)", value=30.0, step=0.5)
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    if st.button("CALCULAR PROPOSTA", use_container_width=True):
        if kwh is None:
            st.error("Por favor, informe o consumo (kWh).")
        else:
            res = calcular(kwh, val_unit, tipo, ban, ilum, desc)

            st.write("---")
            st.markdown("### 📊 Resultado da Simulação")

            # CARD 1: Fatura Atual
            st.markdown(f"""
            <div class="card-result card-orange">
                <div class="label-text">Fatura Atual Energisa</div>
                <div class="big-number">{fmt_currency(res['total_atual'])}</div>
                <p class="sub-text">Valor total pago hoje</p>
            </div>
            """, unsafe_allow_html=True)

            # CARDS DETALHADOS
            c_novo1, c_novo2, c_novo3 = st.columns(3)
            with c_novo1:
                st.markdown(f"""
                <div class="card-result card-navy" style="height: 140px;">
                    <div class="label-text">Fatura Energisa</div>
                    <div class="big-number" style="font-size: 18px;">{fmt_currency(res['fat_en'])}</div>
                    <p class="sub-text">(Taxas + Ilum)</p>
                </div>
                """, unsafe_allow_html=True)
            with c_novo2:
                st.markdown(f"""
                <div class="card-result card-blue" style="height: 140px;">
                    <div class="label-text">Fatura Reenergisa</div>
                    <div class="big-number" style="font-size: 18px;">{fmt_currency(res['fat_re'])}</div>
                    <p class="sub-text">(Com Desconto)</p>
                </div>
                """, unsafe_allow_html=True)
            with c_novo3:
                st.markdown(f"""
                <div class="card-result card-green-line" style="height: 140px;">
                    <div class="label-text">Novo Total</div>
                    <div class="big-number" style="font-size: 18px;">{fmt_currency(res['total_novo'])}</div>
                    <p class="sub-text">Total a Pagar</p>
                </div>
                """, unsafe_allow_html=True)

            # CARD ECONOMIA
            st.markdown(f"""
            <div class="card-result card-green">
                <div style="font-size: 15px; margin-bottom: 6px; color: #ffffff !important; font-weight:600;">💰 Economia Estimada</div>
                <div style="font-size: 28px; font-weight: 800; color: #ffffff !important;">Mensal: {fmt_currency(res['econ_mes'])}</div>
                <div style="font-size: 19px; opacity: 0.95; color: #ffffff !important;">Anual: {fmt_currency(res['econ_ano'])}</div>
            </div>
            """, unsafe_allow_html=True)

            # DADOS TÉCNICOS
            c_tec1, c_tec2 = st.columns(2)
            with c_tec1:
                st.markdown(f"""
                <div class="info-pill"><b>Cota Necessária:</b> {fmt_number(res['kwh_re'])} kWh</div>
                """, unsafe_allow_html=True)
            with c_tec2:
                st.markdown(f"""
                <div class="info-pill"><b>Equipamento:</b> {res['qtd_placas']} Placas</div>
                """, unsafe_allow_html=True)

            st.write("")
            pdf_bytes = criar_pdf_visual_final(res, nome, cidade, desc)
            st.download_button(
                label="⬇️ BAIXAR PROPOSTA EM PDF",
                data=pdf_bytes,
                file_name=f"Proposta_{nome.split()[0] if nome else 'Cliente'}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
