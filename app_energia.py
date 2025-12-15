import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import tempfile
import os

# --- 1. CONFIGURAÇÃO GERAL ---
st.set_page_config(page_title="Simulador Reenergisa", page_icon="⚡", layout="wide")

LOGO_URL = "https://i.postimg.cc/Nfyg51mD/LOGO-LAMPADA-removebg-preview.png"
BG_COLOR = "#fdf1db"
PRIMARY_BLUE = "#26628d"
DETAIL_GREEN = "#56a536" 
ECONOMY_BLUE = "#4a90e2" # Azul Claro do fundo da economia
ALERT_ORANGE = "#e67e22"

# Formatadores
def fmt(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_dec(valor):
    return f"{valor:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")

# CSS Visual
st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_COLOR}; }}
    
    /* 1. Regra Geral: Tudo Azul Escuro (Para o fundo Bege) */
    h1, h2, h3, h4, p, div, span, label, li {{ 
        color: {PRIMARY_BLUE} !important; 
        font-family: sans-serif; 
    }}
    
    /* 2. EXCEÇÃO IMPORTANTE: Texto Branco (Para fundos escuros/coloridos) */
    .texto-branco, .texto-branco h2, .texto-branco h3, .texto-branco p, .texto-branco span {{
        color: #ffffff !important;
    }}
    
    /* Botões */
    div.stButton > button {{
        background-color: {PRIMARY_BLUE} !important;
        color: white !important;
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
        text-transform: uppercase;
    }}
    
    /* Box padrão de Sucesso */
    div[data-testid="stAlert"] {{ background-color: {ECONOMY_BLUE}; color: white !important; border-radius: 10px; }}
    div[data-testid="stAlert"] p {{ color: white !important; font-size: 18px !important; }}
    
    /* Cards */
    .card-separador {{
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid {PRIMARY_BLUE};
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }}
    .card-atual {{ border-left: 5px solid {ALERT_ORANGE} !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 2. CÁLCULO ---
def calcular_separado(kwh_total, valor_unit_energisa, tipo_ligacao, bandeira, ilum, desconto_pct):
    if tipo_ligacao == "Monofásico": residuo = 30
    elif tipo_ligacao == "Bifásico": residuo = 50
    else: residuo = 100 
    
    if kwh_total < residuo:
        kwh_re = 0
        kwh_res = kwh_total
    else:
        kwh_re = kwh_total - residuo
        kwh_res = residuo

    # Fatura Energisa
    custo_disponibilidade = kwh_res * valor_unit_energisa
    fatura_energisa = custo_disponibilidade + bandeira + ilum

    # Fatura Reenergisa
    valor_unit_re = valor_unit_energisa * (1 - (desconto_pct/100))
    fatura_reenergisa = kwh_re * valor_unit_re

    # Totais
    novo_total = fatura_energisa + fatura_reenergisa
    total_antigo = (kwh_total * valor_unit_energisa) + bandeira + ilum
    economia = total_antigo - novo_total
    econ_ano = economia * 12
    
    return {
        "tipo": tipo_ligacao,
        "kwh_total": kwh_total,
        "valor_unit_e": valor_unit_energisa,
        "valor_unit_r": valor_unit_re,
        "bandeira": bandeira,
        "ilum": ilum,
        "kwh_res": kwh_res, "custo_disp": custo_disponibilidade, "fatura_energisa": fatura_energisa,
        "kwh_re": kwh_re, "fatura_reenergisa": fatura_reenergisa,
        "total_antigo": total_antigo, "total_novo": novo_total, 
        "econ_mes": economia, "econ_ano": econ_ano
    }

# --- 3. PDF ---
class PDF(FPDF):
    def header(self):
        try:
            response = requests.get(LOGO_URL)
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                self.image(tmp_path, 10, 8, 25)
                os.unlink(tmp_path)
        except: pass
        self.set_font('Arial', 'B', 15)
        self.set_text_color(38, 98, 141)
        self.cell(80); self.cell(30, 10, 'ESTUDO DE ECONOMIA', 0, 0, 'C'); self.ln(20)

    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128)
        self.cell(0, 10, 'Simulador Reenergisa', 0, 0, 'C')

def criar_pdf_individual(d, uc_nome, desconto):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Cliente: {uc_nome}", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Tipo: {d['tipo']} (Deduz {d['kwh_res']} kWh)", ln=True)
    pdf.ln(5)
    
    # Atual
    pdf.set_fill_color(240, 240, 240); pdf.set_text_color(0,0,0); pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, " CENARIO ATUAL (SEM DESCONTO)", 1, 1, 'L', fill=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(100, 8, "Fatura Energisa (Consumo + Taxas)", 1); pdf.cell(90, 8, fmt(d['total_antigo']), 1, 1, 'R')
    pdf.ln(8)
    
    # Proposta
    pdf.set_fill_color(38, 98, 141); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, f" NOVO CENARIO (COM REENERGISA)", 1, 1, 'L', fill=True)
    
    pdf.set_text_color(0,0,0); pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 8, "   1. Boleto Energisa (Obrigatorio)", 0, 1)
    pdf.set_font("Arial", "", 9)
    pdf.cell(100, 6, f"   - Disponibilidade ({d['kwh_res']} kWh x R$ {fmt_dec(d['valor_unit_e'])})", 0); pdf.cell(90, 6, fmt(d['custo_disp']), 0, 1, 'R')
    pdf.cell(100, 6, f"   - Taxas (Ilum + Bandeira)", 0); pdf.cell(90, 6, fmt(d['ilum'] + d['bandeira']), 0, 1, 'R')
    pdf.set_font("Arial", "B", 9); pdf.cell(100, 6, "   Subtotal Energisa:", "B"); pdf.cell(90, 6, fmt(d['fatura_energisa']), "B", 1, 'R'); pdf.ln(2)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 8, f"   2. Boleto Reenergisa ({desconto}% OFF)", 0, 1)
    pdf.set_font("Arial", "", 9)
    pdf.cell(100, 6, f"   - Energia Injetada ({d['kwh_re']} kWh x R$ {fmt_dec(d['valor_unit_r'])})", 0); pdf.cell(90, 6, fmt(d['fatura_reenergisa']), 0, 1, 'R')
    pdf.set_font("Arial", "B", 9); pdf.cell(100, 6, "   Subtotal Reenergisa:", "B"); pdf.cell(90, 6, fmt(d['fatura_reenergisa']), "B", 1, 'R'); pdf.ln(5)
    
    # Total
    pdf.set_font("Arial", "B", 11)
    pdf.cell(100, 10, "NOVO CUSTO MENSAL (1+2):", 1, 0, 'R')
    pdf.cell(90, 10, fmt(d['total_novo']), 1, 1, 'R')
    pdf.ln(10)
    
    # Economia Azul
    pdf.set_fill_color(74, 144, 226)
    pdf.rect(pdf.get_x(), pdf.get_y(), 190, 30, 'DF'); pdf.set_y(pdf.get_y()+5)
    pdf.set_text_color(255,255,255); pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, f"ECONOMIA MENSAL: {fmt(d['econ_mes'])}", 0, 1, 'C')
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, f"ECONOMIA ANUAL: {fmt(d['econ_ano'])}", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

def criar_pdf_lote(df_res, totais, nome_cliente, desconto):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12); pdf.set_text_color(38, 98, 141)
    pdf.cell(0, 10, f"PROPOSTA CORPORATIVA: {nome_cliente}", ln=True); pdf.ln(5)
    
    pdf.set_fill_color(74, 144, 226); 
    pdf.rect(pdf.get_x(), pdf.get_y(), 190, 30, 'DF'); pdf.set_y(pdf.get_y()+5)
    pdf.set_text_color(255,255,255); pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "ECONOMIA MENSAL TOTAL", 0, 1, 'C')
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, fmt(totais['econ_total']), 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_text_color(0,0,0); pdf.set_font("Arial", "B", 8)
    pdf.cell(40, 8, "UC", 1); pdf.cell(20, 8, "Tipo", 1); pdf.cell(25, 8, "Consumo", 1); pdf.cell(25, 8, "Fat. Ener", 1); pdf.cell(25, 8, "Fat. Re", 1); pdf.cell(25, 8, "Econ. Mes", 1); pdf.cell(30, 8, "Econ. Ano", 1, 1)
    
    pdf.set_font("Arial", "", 8)
    for _, row in df_res.iterrows():
        pdf.cell(40, 7, str(row['UC'])[:20], 1)
        pdf.cell(20, 7, row['Tipo'][:3], 1)
        pdf.cell(25, 7, f"{row['Consumo']:.0f}", 1)
        pdf.cell(25, 7, fmt(row['Fat. Energisa']).replace("R$ ",""), 1)
        pdf.cell(25, 7, fmt(row['Fat. Reenergisa']).replace("R$ ",""), 1)
        pdf.cell(25, 7, fmt(row['Economia']).replace("R$ ",""), 1)
        pdf.cell(30, 7, fmt(row['Economia']*12).replace("R$ ",""), 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFACE ---
c1, c2 = st.columns([1, 6])
with c1: st.image(LOGO_URL, width=100)
with c2: st.title("Simulador Comercial")

abas = st.tabs(["🏠 Individual", "🏢 Lote"])

# === ABA INDIVIDUAL ===
with abas[0]:
    with st.form("form_single"):
        st.markdown("##### 1. Dados do Cliente")
        c1, c2 = st.columns(2)
        uc = c1.text_input("Nome/UC")
        tipo = c2.selectbox("Tipo de Ligação", ["Trifásico", "Bifásico", "Monofásico"])
        
        st.markdown("##### 2. Dados da Fatura")
        c3, c4 = st.columns(2)
        kwh = c3.number_input("Consumo Total (kWh)", value=1000, min_value=0)
        valor_unit = c4.number_input("Valor Unitário (R$)", value=1.15, format="%.4f", min_value=0.0)
        
        c5, c6, c7 = st.columns(3)
        ban = c5.number_input("Bandeira (R$)", 0.0)
        ilum = c6.number_input("Ilum. Púb. (R$)", 0.0)
        desc = c7.number_input("Desconto (%)", 0.0, 100.0, 30.0, 0.5)
        
        btn = st.form_submit_button("CALCULAR PROPOSTA", use_container_width=True)
    
    if btn:
        d = calcular_separado(kwh, valor_unit, tipo, ban, ilum, desc)
        
        st.write("")
        
        # BLOCO 1
        with st.container():
            st.markdown(f"""
            <div class='card-separador card-atual'>
                <h3>🟠 Cenario Atual (Sem Desconto)</h3>
                <p>O cliente paga tarifa cheia sobre todo o consumo.</p>
                <hr>
                <div style="display: flex; justify-content: space-between;">
                    <span><b>Total Fatura Atual:</b></span>
                    <span style="font-size: 20px;"><b>{fmt(d['total_antigo'])}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # BLOCO 2
        with st.container():
            st.markdown(f"""<div class='card-separador'><h3>🔵 Proposta Reenergisa</h3>""", unsafe_allow_html=True)
            c_bol1, c_bol2 = st.columns(2)
            with c_bol1:
                st.info("**📄 1. Boleto Energisa**")
                st.caption("Resíduo (Disp.) + Taxas")
                df_e = pd.DataFrame([{"Descrição": f"Disp. ({d['kwh_res']} kWh)", "Valor": fmt(d['custo_disp'])}, {"Descrição": "Taxas (Ilum+Band)", "Valor": fmt(d['ilum']+d['bandeira'])}, {"Descrição": "TOTAL", "Valor": fmt(d['fatura_energisa'])}])
                st.dataframe(df_e, hide_index=True, use_container_width=True)
            with c_bol2:
                st.info(f"**⚡ 2. Boleto Reenergisa**")
                st.caption(f"Desconto de {desc}% na tarifa")
                df_r = pd.DataFrame([{"Descrição": f"Consumo ({d['kwh_re']} kWh)", "Valor": fmt(d['fatura_reenergisa'])}, {"Descrição": "TOTAL", "Valor": fmt(d['fatura_reenergisa'])}])
                st.dataframe(df_r, hide_index=True, use_container_width=True)

            st.markdown(f"""
                <hr>
                <div style="text-align: right;">
                    <span>Novo Custo Mensal (Soma):</span>
                    <span style="font-size: 22px; color: {PRIMARY_BLUE}"><b>{fmt(d['total_novo'])}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        # BLOCO 3: ECONOMIA (Com classe 'texto-branco')
        with st.container():
            st.markdown(f"""
            <div class='texto-branco' style="background-color: {ECONOMY_BLUE}; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
                <h2 style="margin:0;">💰 ECONOMIA MENSAL: {fmt(d['econ_mes'])}</h2>
                <h3 style="margin-top: 10px;">📅 Anual: {fmt(d['econ_ano'])}</h3>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.download_button("📄 BAIXAR PDF DETALHADO", criar_pdf_individual(d, uc, desc), f"Proposta_{uc}.pdf", "application/pdf", use_container_width=True)

# === ABA LOTE ===
with abas[1]:
    st.info("Copie e cole seus dados.")
    col_cli, col_desc_lote = st.columns([3, 1])
    nome_cliente_lote = col_cli.text_input("Nome Cliente Corporativo")
    desc_lote = col_desc_lote.number_input("Desconto Global (%)", 30.0)

    if 'df_lote' not in st.session_state:
        st.session_state.df_lote = pd.DataFrame([{"Nome/UC": "Unidade 1", "Tipo Ligação": "Trifásico", "Consumo (kWh)": 1000, "Valor Unit. (R$)": 1.15, "Bandeira (R$)": 0.0, "Ilum. Pub. (R$)": 0.0}])

    df_editado = st.data_editor(st.session_state.df_lote, num_rows="dynamic", use_container_width=True, column_config={
        "Tipo Ligação": st.column_config.SelectboxColumn("Tipo", options=["Trifásico", "Bifásico", "Monofásico"], required=True),
        "Valor Unit. (R$)": st.column_config.NumberColumn(format="R$ %.4f"),
        "Consumo (kWh)": st.column_config.NumberColumn(format="%d"),
        "Bandeira (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
        "Ilum. Pub. (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
    })

    if st.button("CALCULAR LOTE", use_container_width=True):
        if not df_editado.empty:
            resultados = []
            for _, row in df_editado.iterrows():
                d = calcular_separado(row['Consumo (kWh)'], row['Valor Unit. (R$)'], row['Tipo Ligação'], row['Bandeira (R$)'], row['Ilum. Pub. (R$)'], desc_lote)
                resultados.append({
                    "UC": row['Nome/UC'], "Tipo": row['Tipo Ligação'], "Consumo": row['Consumo (kWh)'],
                    "Fat. Energisa": d['fatura_energisa'], "Fat. Reenergisa": d['fatura_reenergisa'],
                    "Novo": d['total_novo'], "Economia": d['econ_mes']
                })
            
            df_final = pd.DataFrame(resultados)
            totais = {"econ_total": df_final['Economia'].sum(), "atual_total": 0, "novo_total": df_final['Novo'].sum()}
            
            st.divider()
            with st.container(): 
                # Adicionei a classe 'texto-branco' aqui também
                st.markdown(f"""
                <div class='texto-branco' style="background-color: {ECONOMY_BLUE}; padding: 15px; border-radius: 10px; text-align: center;">
                    <h3>Economia Mensal Total: {fmt(totais['econ_total'])}</h3>
                    <p>Anual: {fmt(totais['econ_total']*12)}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.dataframe(df_final, use_container_width=True)
            st.download_button("📄 BAIXAR PDF CORPORATIVO", criar_pdf_lote(df_final, totais, nome_cliente_lote, desc_lote), f"Proposta_Corp_{nome_cliente_lote}.pdf", "application/pdf", use_container_width=True)
