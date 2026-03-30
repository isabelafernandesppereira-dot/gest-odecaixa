import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. CONFIGURAÇÃO GERAL ---
st.set_page_config(page_title="Portal Financeiro EJESC", page_icon="🐺", layout="wide")

# --- 2. BANCO DE DADOS FALSO (Para testar o login de múltiplas empresas) ---
USUARIOS_DB = {
    "isabela@ejesc.com": {"senha": "123", "empresa": "EJESC", "id": 1},
    "cliente@empresa.com": {"senha": "abc", "empresa": "Cliente Alpha", "id": 2}
}

if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = None

def realizar_login(email, senha):
    if email in USUARIOS_DB and USUARIOS_DB[email]['senha'] == senha:
        st.session_state.logado = True
        st.session_state.usuario = USUARIOS_DB[email]
        return True
    return False

# --- 3. TELA DE LOGIN (A Trava de Segurança) ---
if not st.session_state.logado:
    st.title("🔐 Acesso ao Portal Financeiro")
    with st.container(border=True):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if realizar_login(email, senha):
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop() # PARA O CÓDIGO AQUI SE NÃO ESTIVER LOGADO

# ==========================================
# 🚀 DAQUI PARA BAIXO, O USUÁRIO ESTÁ LOGADO
# ==========================================
user = st.session_state.usuario

# --- 4. SEPARAÇÃO DE DADOS POR EMPRESA ---
# A mágica: cada empresa salva num arquivo com o ID dela!
ARQUIVO_DADOS = f"dados_caixa_{user['id']}.csv"
ARQUIVO_SALDO_INICIAL = f"saldo_inicial_{user['id']}.txt"

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
            try: return float(f.read())
            except: return 0.0
    return 0.0

def salvar_saldo_inicial(valor):
    with open(ARQUIVO_SALDO_INICIAL, "w") as f:
        f.write(str(valor))

# Recarrega os dados se o usuário mudar
if 'df_caixa' not in st.session_state or st.session_state.get('ultimo_user') != user['id']:
    st.session_state['df_caixa'] = carregar_dados()
    st.session_state['ultimo_user'] = user['id']

# --- 5. MENU LATERAL (As Páginas) ---
with st.sidebar:
    st.write(f"🏢 **Empresa:** {user['empresa']}")
    st.divider()
    pagina = st.radio("Navegação", ["🏠 Início", "💰 Fluxo de Caixa"])
    st.divider()
    if st.button("Sair / Logout"):
        st.session_state.logado = False
        st.session_state.usuario = None
        st.rerun()

# --- 6. AS FERRAMENTAS DO PORTAL ---

if pagina == "🏠 Início":
    st.title(f"Bem-vindo(a), {user['empresa']}! 🐺")
    st.write("Use o menu lateral para acessar suas ferramentas financeiras.")

elif pagina == "💰 Fluxo de Caixa":
    st.title(f"Gestão Financeira - {user['empresa']}")
    st.markdown("---")
    
    # Atualizar Saldo Inicial
    c_saldo, c_vazio = st.columns([1, 2])
    s_ini_atual = carregar_saldo_inicial()
    novo_s_ini = c_saldo.number_input("Saldo Inicial da Conta (R$)", value=s_ini_atual, format="%.2f")
    if c_saldo.button("Atualizar Saldo Inicial"):
        salvar_saldo_inicial(novo_s_ini)
        st.success("Atualizado!")
        st.rerun()

    # Abas do Fluxo de Caixa
    tab_lanc, tab_dia, tab_mensal = st.tabs(["📝 Lançamentos", "📅 Relatório do Dia", "📚 Biblioteca Mensal"])

    with tab_lanc:
        data_sel = st.date_input("Data do Registro", datetime.now(), format="DD/MM/YYYY")
        sem_mov = st.toggle("Hoje não houve movimentação")
        
        if sem_mov:
            if st.button("🔒 Salvar Fechamento Vazio", use_container_width=True):
                novo = pd.DataFrame([[data_sel, "Fechamento Vazio", "Neutro", "N/A", 0.0]], columns=["Data", "Descrição", "Tipo", "Categoria", "Valor"])
                st.session_state['df_caixa'] = pd.concat([st.session_state['df_caixa'], novo], ignore_index=True)
                salvar_dados(st.session_state['df_caixa'])
                st.success("Salvo!")
        else:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 2, 3, 2])
                desc = c1.text_input("Descrição")
                tipo = c2.selectbox("Tipo", ["Entrada", "Saída"])
                cats = ["Vendas à vista", "Vendas a prazo", "Aportes", "Rendimentos"] if tipo == "Entrada" else ["Fornecedores", "Operacional", "Salários", "Impostos", "Investimentos", "Pró-labore"]
                cat = c3.selectbox("Categoria", cats)
                val = c4.number_input("Valor (R$)", min_value=0.0, format="%.2f")

                if st.button("➕ Salvar Registro", use_container_width=True):
                    if desc:
                        novo = pd.DataFrame([[data_sel, desc, tipo, cat, val]], columns=["Data", "Descrição", "Tipo", "Categoria", "Valor"])
                        st.session_state['df_caixa'] = pd.concat([st.session_state['df_caixa'], novo], ignore_index=True)
                        salvar_dados(st.session_state['df_caixa'])
                        st.success("Salvo com sucesso!")

    with tab_dia:
        st.subheader(f"Resumo: {data_sel.strftime('%d/%m/%Y')}")
        df_dia = st.session_state['df_caixa'][st.session_state['df_caixa']['Data'] == data_sel]
        if not df_dia.empty:
            df_dia_vis = df_dia.copy()
            df_dia_vis['Data'] = pd.to_datetime(df_dia_vis['Data']).dt.strftime('%d/%m/%Y')
            st.dataframe(df_dia_vis, use_container_width=True)
        else:
            st.info("Nenhum registro para esta data.")

    with tab_mensal:
        df_t = st.session_state['df_caixa']
        s_i = carregar_saldo_inicial()
        if not df_t.empty:
            ent = df_t[df_t['Tipo'] == 'Entrada']['Valor'].sum()
            sai = df_t[df_t['Tipo'] == 'Saída']['Valor'].sum()
            st.metric("SALDO ATUAL NO BANCO", f"R$ {(s_i + ent - sai):,.2f}")
            
            df_g = df_t.copy().sort_values('Data')
            df_g['V'] = df_g.apply(lambda x: x['Valor'] if x['Tipo'] == 'Entrada' else (-x['Valor'] if x['Tipo'] == 'Saída' else 0), axis=1)
            st.line_chart(df_g.set_index('Data')['V'].cumsum() + s_i)