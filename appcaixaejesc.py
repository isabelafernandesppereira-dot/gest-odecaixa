import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Caixa Diário - EJESC", page_icon="🐺", layout="wide")

# ARQUIVOS DE MEMÓRIA (Salvamento Automático)
ARQUIVO_DADOS = "dados_caixa_ejesc.csv"
ARQUIVO_SALDO_INICIAL = "saldo_inicial.txt"

# --- FUNÇÕES DE DADOS ---
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        df = pd.read_csv(ARQUIVO_DADOS)
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df
    return pd.DataFrame(columns=["Data", "Descrição", "Tipo", "Categoria", "Valor"])

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

def carregar_saldo_inicial():
    if os.path.exists(ARQUIVO_SALDO_INICIAL):
        with open(ARQUIVO_SALDO_INICIAL, "r") as f:
            try:
                return float(f.read())
            except:
                return 0.0
    return 0.0

def salvar_saldo_inicial(valor):
    with open(ARQUIVO_SALDO_INICIAL, "w") as f:
        f.write(str(valor))

# Inicialização da Memória
if 'df_caixa' not in st.session_state:
    st.session_state['df_caixa'] = carregar_dados()

# --- BARRA LATERAL (CONFIGURAÇÕES) ---
with st.sidebar:
    st.header("⚙️ Configurações")
    s_ini_atual = carregar_saldo_inicial()
    novo_s_ini = st.number_input("Saldo Inicial da Conta (R$)", value=s_ini_atual, format="%.2f")
    if st.button("Atualizar Saldo Inicial"):
        salvar_saldo_inicial(novo_s_ini)
        st.success("Saldo inicial atualizado!")
        st.rerun()

st.title("🐺 Gestão Financeira EJESC")
st.markdown("---")

# --- ABAS ---
tab_lanc, tab_dia, tab_mensal = st.tabs(["📝 Lançamentos", "📅 Relatório do Dia", "📚 Biblioteca Mensal"])

# --- ABA 1: LANÇAMENTOS ---
with tab_lanc:
    col_d, col_m = st.columns(2)
    with col_d:
        data_sel = st.date_input("Data do Registro", datetime.now(), format="DD/MM/YYYY")
    with col_m:
        st.write("")
        sem_mov = st.toggle("Hoje não houve movimentação")

    if sem_mov:
        st.warning(f"Você está fechando o dia {data_sel.strftime('%d/%m/%Y')} sem movimentações.")
        if st.button("🔒 Salvar Fechamento Vazio", use_container_width=True):
            novo = pd.DataFrame([[data_sel, "Fechamento: Sem Movimentação", "Neutro", "N/A", 0.0]], 
                                columns=["Data", "Descrição", "Tipo", "Categoria", "Valor"])
            st.session_state['df_caixa'] = pd.concat([st.session_state['df_caixa'], novo], ignore_index=True)
            salvar_dados(st.session_state['df_caixa'])
            st.success("Dia vazio registrado!")
    else:
        with st.container(border=True):
            st.subheader("Registrar Movimentação")
            c1, c2, c3, c4 = st.columns([3, 2, 3, 2])
            desc = c1.text_input("Descrição")
            tipo = c2.selectbox("Tipo", ["Entrada", "Saída"])
            
            if tipo == "Entrada":
                cats = ["Vendas à vista", "Vendas a prazo", "Aportes", "Rendimentos"]
            else:
                cats = ["Fornecedores", "Operacional", "Salários", "Impostos", "Investimentos", "Pró-labore"]
                
            cat = c3.selectbox("Categoria", cats)
            val = c4.number_input("Valor (R$)", min_value=0.0, format="%.2f")

            if st.button("➕ Salvar Registro", use_container_width=True):
                if desc:
                    novo = pd.DataFrame([[data_sel, desc, tipo, cat, val]], 
                                        columns=["Data", "Descrição", "Tipo", "Categoria", "Valor"])
                    st.session_state['df_caixa'] = pd.concat([st.session_state['df_caixa'], novo], ignore_index=True)
                    salvar_dados(st.session_state['df_caixa'])
                    st.success("Lançamento salvo!")
                else:
                    st.error("Preencha a descrição.")

# --- ABA 2: RELATÓRIO DO DIA ---
with tab_dia:
    st.subheader(f"📊 Resumo do Dia: {data_sel.strftime('%d/%m/%Y')}")
    df_dia = st.session_state['df_caixa'][st.session_state['df_caixa']['Data'] == data_sel]
    
    if not df_dia.empty:
        ent = df_dia[df_dia['Tipo'] == 'Entrada']['Valor'].sum()
        sai = df_dia[df_dia['Tipo'] == 'Saída']['Valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas do Dia", f"R$ {ent:,.2f}")
        c2.metric("Saídas do Dia", f"R$ {sai:,.2f}")
        c3.metric("Resultado Líquido", f"R$ {(ent-sai):,.2f}")
        
        st.divider()
        df_dia_exibir = df_dia.copy()
        df_dia_exibir['Data'] = pd.to_datetime(df_dia_exibir['Data']).dt.strftime('%d/%m/%Y')
        st.dataframe(df_dia_exibir, use_container_width=True)
        
        csv_dia = df_dia_exibir.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
        st.download_button("📥 Baixar CSV de Hoje", csv_dia, f"caixa_{data_sel}.csv", "text/csv")
    else:
        st.info("Nenhum registro para esta data.")

# --- ABA 3: BIBLIOTECA MENSAL ---
with tab_mensal:
    df_total = st.session_state['df_caixa']
    s_ini = carregar_saldo_inicial()

    if not df_total.empty:
        st.subheader("📈 Consolidado Geral")
        t_ent = df_total[df_total['Tipo'] == 'Entrada']['Valor'].sum()
        t_sai = df_total[df_total['Tipo'] == 'Saída']['Valor'].sum()
        s_fim = s_ini + t_ent - t_sai

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Inicial", f"R$ {s_ini:,.2f}")
        m2.metric("Entradas", f"R$ {t_ent:,.2f}")
        m3.metric("Saídas", f"R$ {t_sai:,.2f}")
        m4.metric("SALDO NO BANCO", f"R$ {s_fim:,.2f}")

        st.divider()
        st.subheader("Evolução do Saldo")
        df_g = df_total.copy().sort_values('Data')
        df_g['V'] = df_g.apply(lambda x: x['Valor'] if x['Tipo'] == 'Entrada' else (-x['Valor'] if x['Tipo'] == 'Saída' else 0), axis=1)
        df_g['Evolução'] = df_g['V'].cumsum() + s_ini
        st.line_chart(df_g.set_index('Data')['Evolução'])
        
        df_down = df_total.copy()
        df_down['Data'] = pd.to_datetime(df_down['Data']).dt.strftime('%d/%m/%Y')
        csv_t = df_down.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
        st.download_button("📥 Baixar Biblioteca Completa (CSV)", csv_t, 'caixa_completo.csv', 'text/csv')
    else:
        st.warning("Adicione lançamentos para ver os relatórios.")