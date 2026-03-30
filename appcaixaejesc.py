import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. CONFIGURAÇÃO GERAL ---
st.set_page_config(page_title="Portal Financeiro EJESC", page_icon="🐺", layout="wide")

# --- 2. BANCO DE DADOS (Simulado para Multi-empresa) ---
USUARIOS_DB = {
    "isa_ejesc": {"senha": "123", "empresa": "EJESC", "id": 1},
    "cliente_teste": {"senha": "123", "empresa": "Cliente Alpha", "id": 2}
}

if 'logado' not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = None

def realizar_login(usuario, senha):
    if usuario in USUARIOS_DB and USUARIOS_DB[usuario]['senha'] == senha:
        st.session_state.logado = True
        st.session_state.usuario = USUARIOS_DB[usuario]
        return True
    return False

# --- 3. TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Acesso ao Portal Financeiro")
    with st.container(border=True):
        usuario_input = st.text_input("Usuário")
        senha_input = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            if realizar_login(usuario_input, senha_input):
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# ==========================================
# 🚀 ACESSO AUTORIZADO
# ==========================================
user = st.session_state.usuario
ARQUIVO_DADOS = f"dados_caixa_{user['id']}.csv"
ARQUIVO_SALDO_INICIAL = f"saldo_inicial_{user['id']}.txt"

# --- FUNÇÕES DE ARQUIVO ---
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

# Inicialização da sessão
if 'df_caixa' not in st.session_state or st.session_state.get('ultimo_user') != user['id']:
    st.session_state['df_caixa'] = carregar_dados()
    st.session_state['ultimo_user'] = user['id']

# --- 4. BARRA LATERAL (MENU E ZONA DE PERIGO) ---
with st.sidebar:
    st.header(f"🏢 {user['empresa']}")
    st.divider()
    pagina = st.radio("Navegação", ["🏠 Início", "💰 Controle de Caixa"])
    
    st.divider()
    st.subheader("⚠️ Zona de Perigo")
    if st.button("🚨 APAGAR TODO HISTÓRICO", help="Isso excluirá permanentemente todos os dados desta empresa"):
        st.session_state.confirmar_reset = True
        
    if st.session_state.get('confirmar_reset'):
        st.error("Tem certeza? Esta ação não pode ser desfeita.")
        if st.button("Sim, apagar tudo!"):
            if os.path.exists(ARQUIVO_DADOS): os.remove(ARQUIVO_DADOS)
            if os.path.exists(ARQUIVO_SALDO_INICIAL): os.remove(ARQUIVO_SALDO_INICIAL)
            st.session_state['df_caixa'] = carregar_dados()
            st.session_state.confirmar_reset = False
            st.success("Dados resetados com sucesso!")
            st.rerun()
        if st.button("Cancelar"):
            st.session_state.confirmar_reset = False
            st.rerun()

    st.divider()
    if st.button("Sair / Logout"):
        st.session_state.logado = False
        st.rerun()

# --- 5. PÁGINAS ---

if pagina == "🏠 Início":
    st.title(f"Bem-vindo(a), {user['empresa']}! 🐺")
    st.write("Portal de ferramentas financeiras exclusivas.")

elif pagina == "💰 Controle de Caixa":
    st.title(f"Controle de Caixa - {user['empresa']}")
    st.divider()
    
    # Configuração de Saldo Inicial
    with st.expander("⚙️ Configurar Saldo Inicial da Conta"):
        s_ini_atual = carregar_saldo_inicial()
        novo_s_ini = st.number_input("Valor em conta hoje (R$)", value=s_ini_atual, format="%.2f")
        if st.button("Confirmar Saldo Inicial"):
            with open(ARQUIVO_SALDO_INICIAL, "w") as f: f.write(str(novo_s_ini))
            st.success("Saldo inicial atualizado!")
            st.rerun()

    tab_lanc, tab_dia, tab_mensal = st.tabs(["📝 Novo Lançamento", "📅 Relatório e Edição", "📚 Biblioteca Mensal"])

    with tab_lanc:
        data_sel = st.date_input("Data do Registro", datetime.now(), format="DD/MM/YYYY")
        sem_mov = st.toggle("Hoje não houve movimentação")
        
        if not sem_mov:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 2, 3, 2])
                desc = c1.text_input("Descrição")
                tipo = c2.selectbox("Tipo", ["Entrada", "Saída"])
                cats = ["Vendas à vista", "Vendas a prazo", "Aportes", "Rendimentos"] if tipo == "Entrada" else ["Fornecedores", "Operacional", "Salários", "Impostos", "Investimentos", "Pró-labore"]
                cat = c3.selectbox("Categoria", cats)
                val = c4.number_input("Valor (R$)", min_value=0.0, format="%.2f")

                if st.button("💾 Salvar Lançamento", use_container_width=True):
                    if desc:
                        novo = pd.DataFrame([[data_sel, desc, tipo, cat, val]], columns=["Data", "Descrição", "Tipo", "Categoria", "Valor"])
                        st.session_state['df_caixa'] = pd.concat([st.session_state['df_caixa'], novo], ignore_index=True)
                        salvar_dados(st.session_state['df_caixa'])
                        st.success("Salvo!")
                        st.rerun() # Atualiza a tela para aparecer na hora nas outras abas
                    else:
                        st.error("Preencha a descrição.")
        else:
            if st.button("🔒 Salvar Dia Sem Movimento", use_container_width=True):
                novo = pd.DataFrame([[data_sel, "Sem Movimentação", "Neutro", "N/A", 0.0]], columns=["Data", "Descrição", "Tipo", "Categoria", "Valor"])
                st.session_state['df_caixa'] = pd.concat([st.session_state['df_caixa'], novo], ignore_index=True)
                salvar_dados(st.session_state['df_caixa'])
                st.success("Dia vazio registrado!")
                st.rerun()

    with tab_dia:
        st.subheader(f"Lançamentos de {data_sel.strftime('%d/%m/%Y')}")
        st.info("💡 Para apagar um lançamento: Selecione a caixinha na primeira coluna da linha e aperte 'Delete' (ou no ícone da lixeira).")
        
        # Filtra os dados do dia
        df_completo = st.session_state['df_caixa']
        mask_dia = df_completo['Data'] == data_sel
        df_dia = df_completo[mask_dia]

        # EDITOR DE DADOS: Permite apagar linhas
        df_editado = st.data_editor(
            df_dia, 
            num_rows="dynamic", 
            use_container_width=True,
            key="editor_dia",
            hide_index=True # Esconde aquele número chato na frente da linha
        )

        if st.button("Confirmar Alterações/Exclusões"):
            df_sem_hoje = df_completo[~mask_dia]
            st.session_state['df_caixa'] = pd.concat([df_sem_hoje, df_editado], ignore_index=True)
            salvar_dados(st.session_state['df_caixa'])
            st.success("Alterações salvas!")
            st.rerun()

    with tab_mensal:
        df_t = st.session_state['df_caixa']
        s_i = carregar_saldo_inicial()
        if not df_t.empty:
            ent = df_t[df_t['Tipo'] == 'Entrada']['Valor'].sum()
            sai = df_t[df_t['Tipo'] == 'Saída']['Valor'].sum()
            st.metric("SALDO ATUAL EM CONTA", f"R$ {(s_i + ent - sai):,.2f}")
            
            df_g = df_t.copy().sort_values('Data')
            df_g['V'] = df_g.apply(lambda x: x['Valor'] if x['Tipo'] == 'Entrada' else (-x['Valor'] if x['Tipo'] == 'Saída' else 0), axis=1)
            st.line_chart(df_g.set_index('Data')['V'].cumsum() + s_i)
        