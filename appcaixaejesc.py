import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. CONFIGURAÇÃO GERAL ---
st.set_page_config(page_title="Portal Financeiro EJESC", page_icon="🐺", layout="wide")

# --- 2. BANCO DE DADOS (Simulado) ---
USUARIOS_DB = {
    "isa_ejesc": {"senha": "123", "empresa": "EJESC", "id": 1},
    "cliente_teste": {"senha": "123", "empresa": "Cliente Teste", "id": 2}
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

# ARQUIVOS POR EMPRESA
ARQUIVO_CAIXA = f"dados_caixa_{user['id']}.csv"
ARQUIVO_CONTAS = f"contas_pagar_{user['id']}.csv"
ARQUIVO_SALDO = f"saldo_inicial_{user['id']}.txt"

# --- FUNÇÕES DE PERSISTÊNCIA ---
def carregar_csv(arquivo, colunas):
    if os.path.exists(arquivo):
        df = pd.read_csv(arquivo)
        if not df.empty and 'Data' in df.columns: df['Data'] = pd.to_datetime(df['Data']).dt.date
        if not df.empty and 'Vencimento' in df.columns: df['Vencimento'] = pd.to_datetime(df['Vencimento']).dt.date
        if not df.empty and 'Data_Efetiva' in df.columns: df['Data_Efetiva'] = pd.to_datetime(df['Data_Efetiva']).dt.date
        return df
    return pd.DataFrame(columns=colunas)

def salvar_csv(df, arquivo):
    df.to_csv(arquivo, index=False)

def carregar_saldo():
    if os.path.exists(ARQUIVO_SALDO):
        with open(ARQUIVO_SALDO, "r") as f:
            try: return float(f.read())
            except: return 0.0
    return 0.0

# Inicialização da Sessão
if 'df_caixa' not in st.session_state or st.session_state.get('ultimo_user') != user['id']:
    st.session_state['df_caixa'] = carregar_csv(ARQUIVO_CAIXA, ["Data", "Descrição", "Tipo", "Categoria", "Valor"])
    st.session_state['df_contas'] = carregar_csv(ARQUIVO_CONTAS, ["Data", "Fornecedor", "Descrição", "Valor", "Vencimento", "Data_Efetiva", "Parcela_Atual", "Total_Parcelas", "Pago", "Mes_Ref"])
    st.session_state['ultimo_user'] = user['id']

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.header(f"🏢 {user['empresa']}")
    st.divider()
    pagina = st.radio("Navegação", ["🏠 Início", "💰 Controle de Caixa", "📅 Gestão de Contas"])
    
    st.divider()
    st.subheader("⚠️ Zona de Perigo")
    if st.button("🚨 APAGAR TODO HISTÓRICO"):
        st.session_state.confirmar_reset = True
        
    if st.session_state.get('confirmar_reset'):
        st.error("Tem certeza? Isso apaga CAIXA e CONTAS.")
        if st.button("Sim, apagar tudo!"):
            for f in [ARQUIVO_CAIXA, ARQUIVO_CONTAS, ARQUIVO_SALDO]:
                if os.path.exists(f): os.remove(f)
            st.session_state['df_caixa'] = carregar_csv(ARQUIVO_CAIXA, ["Data", "Descrição", "Tipo", "Categoria", "Valor"])
            st.session_state['df_contas'] = carregar_csv(ARQUIVO_CONTAS, ["Data", "Fornecedor", "Descrição", "Valor", "Vencimento", "Data_Efetiva", "Parcela_Atual", "Total_Parcelas", "Pago", "Mes_Ref"])
            st.session_state.confirmar_reset = False
            st.success("Dados resetados!")
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
    st.write("Selecione uma ferramenta no menu ao lado para começar.")

# ==========================================
# PÁGINA: CONTROLE DE CAIXA
# ==========================================
elif pagina == "💰 Controle de Caixa":
    st.title(f"Controle de Caixa - {user['empresa']}")
    st.divider()
    
    with st.expander("⚙️ Configurar Saldo Inicial da Conta"):
        s_ini_atual = carregar_saldo()
        novo_s_ini = st.number_input("Valor em conta hoje (R$)", value=s_ini_atual, format="%.2f")
        if st.button("Confirmar Saldo Inicial"):
            with open(ARQUIVO_SALDO, "w") as f: f.write(str(novo_s_ini))
            st.success("Saldo inicial atualizado!")
            st.rerun()

    tab_lanc, tab_dia, tab_mensal = st.tabs(["📝 Novo Lançamento", "📅 Relatório e Edição", "📚 Biblioteca Mensal"])

    with tab_lanc:
        data_sel = st.date_input("Data do Registro", datetime.now(), format="DD/MM/YYYY", key="data_caixa")
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
                        salvar_csv(st.session_state['df_caixa'], ARQUIVO_CAIXA)
                        st.success("Salvo!")
                        st.rerun()
                    else:
                        st.error("Preencha a descrição.")
        else:
            if st.button("🔒 Salvar Dia Sem Movimento", use_container_width=True):
                novo = pd.DataFrame([[data_sel, "Sem Movimentação", "Neutro", "N/A", 0.0]], columns=["Data", "Descrição", "Tipo", "Categoria", "Valor"])
                st.session_state['df_caixa'] = pd.concat([st.session_state['df_caixa'], novo], ignore_index=True)
                salvar_csv(st.session_state['df_caixa'], ARQUIVO_CAIXA)
                st.success("Dia vazio registrado!")
                st.rerun()

    with tab_dia:
        st.subheader(f"Lançamentos de {data_sel.strftime('%d/%m/%Y')}")
        st.info("💡 Para apagar ou editar: dê um duplo clique na célula ou selecione a linha e aperte 'Delete'.")
        
        df_completo = st.session_state['df_caixa']
        mask_dia = df_completo['Data'] == data_sel
        df_dia = df_completo[mask_dia]

        df_editado_caixa = st.data_editor(df_dia, num_rows="dynamic", use_container_width=True, hide_index=True, key="editor_caixa")

        if st.button("Confirmar Alterações/Exclusões (Caixa)"):
            df_sem_hoje = df_completo[~mask_dia]
            st.session_state['df_caixa'] = pd.concat([df_sem_hoje, df_editado_caixa], ignore_index=True)
            salvar_csv(st.session_state['df_caixa'], ARQUIVO_CAIXA)
            st.success("Alterações salvas!")
            st.rerun()

    with tab_mensal:
        df_t = st.session_state['df_caixa']
        s_i = carregar_saldo()
        if not df_t.empty:
            ent = df_t[df_t['Tipo'] == 'Entrada']['Valor'].sum()
            sai = df_t[df_t['Tipo'] == 'Saída']['Valor'].sum()
            st.metric("SALDO ATUAL EM CONTA", f"R$ {(s_i + ent - sai):,.2f}")
            
            df_g = df_t.copy().sort_values('Data')
            df_g['V'] = df_g.apply(lambda x: x['Valor'] if x['Tipo'] == 'Entrada' else (-x['Valor'] if x['Tipo'] == 'Saída' else 0), axis=1)
            st.line_chart(df_g.set_index('Data')['V'].cumsum() + s_i)

# ==========================================
# PÁGINA: GESTÃO DE CONTAS A PAGAR
# ==========================================
elif pagina == "📅 Gestão de Contas":
    st.title(f"Gestão de Contas a Pagar - {user['empresa']}")
    
    col_mes, col_vazio = st.columns([2, 4])
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = col_mes.selectbox("Mês de Referência", meses, index=datetime.now().month - 1)
    ano_sel = col_mes.number_input("Ano", value=datetime.now().year)
    mes_ref = f"{mes_sel}/{ano_sel}"

    # --- ALERTAS DE VENCIMENTO ---
    hoje = datetime.now().date()
    contas_vencidas = st.session_state['df_contas'][(st.session_state['df_contas']['Vencimento'] <= hoje) & (st.session_state['df_contas']['Pago'] == False)]
    if not contas_vencidas.empty:
        st.error(f"🚨 ATENÇÃO: Você tem {len(contas_vencidas)} conta(s) pendente(s) ou vencendo hoje/atrasadas!")

    tab1, tab2 = st.tabs(["➕ Cadastrar Conta", "📋 Listagem Mensal e Edição"])

    with tab1:
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            data_reg = c1.date_input("Data do Registro", hoje, key="data_reg_conta")
            forn = c2.text_input("Fornecedor")
            item = c3.text_input("Descrição do Item")
            
            c4, c5, c6 = st.columns(3)
            valor_parc = c4.number_input("Valor da Parcela (R$)", min_value=0.0)
            vencimento = c5.date_input("Data de Vencimento", hoje)
            data_efetiva = c6.date_input("Data Efetiva (Pagamento)", value=None)
            
            c7, c8 = st.columns(2)
            parc_n = c7.number_input("Parcela Nº", value=1, min_value=1)
            parc_t = c8.number_input("Total de Parcelas", value=1, min_value=1)

            if st.button("💾 Salvar Conta", use_container_width=True):
                if forn and item:
                    nova_conta = pd.DataFrame([[data_reg, forn, item, valor_parc, vencimento, data_efetiva, parc_n, parc_t, False, mes_ref]], 
                                              columns=["Data", "Fornecedor", "Descrição", "Valor", "Vencimento", "Data_Efetiva", "Parcela_Atual", "Total_Parcelas", "Pago", "Mes_Ref"])
                    st.session_state['df_contas'] = pd.concat([st.session_state['df_contas'], nova_conta], ignore_index=True)
                    salvar_csv(st.session_state['df_contas'], ARQUIVO_CONTAS)
                    st.success(f"Conta registrada para {mes_ref}!")
                    st.rerun()
                else:
                    st.error("Preencha Fornecedor e Descrição.")

    with tab2:
        df_mensal = st.session_state['df_contas'][st.session_state['df_contas']['Mes_Ref'] == mes_ref]
        
        if not df_mensal.empty:
            # MÉTRICAS
            total_geral = df_mensal['Valor'].sum()
            total_pago = df_mensal[df_mensal['Pago'] == True]['Valor'].sum()
            total_pendente = df_mensal[df_mensal['Pago'] == False]['Valor'].sum()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total do Mês", f"R$ {total_geral:,.2f}")
            m2.metric("Pagas", f"R$ {total_pago:,.2f}", delta_color="normal")
            m3.metric("Pendente", f"R$ {total_pendente:,.2f}", delta="-A pagar", delta_color="inverse")

            st.divider()
            st.info("💡 **Dica de Edição:** Dê um duplo clique em qualquer palavra, data ou valor para alterar. Marque a caixinha 'Pago?' para dar baixa. Selecione a linha e aperte 'Delete' para apagar.")
            
            # EDITOR DE DADOS (Edição e checkbox de pago)
            df_editado_contas = st.data_editor(
                df_mensal,
                column_config={
                    "Pago": st.column_config.CheckboxColumn("Pago?", default=False),
                    "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
                },
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="editor_contas"
            )

            if st.button("✅ Confirmar Alterações do Mês"):
                df_outros_meses = st.session_state['df_contas'][st.session_state['df_contas']['Mes_Ref'] != mes_ref]
                st.session_state['df_contas'] = pd.concat([df_outros_meses, df_editado_contas], ignore_index=True)
                salvar_csv(st.session_state['df_contas'], ARQUIVO_CONTAS)
                st.success("Dados atualizados!")
                st.rerun()
            
            # DOWNLOAD
            csv_mensal = df_mensal.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
            st.download_button(f"📥 Baixar Relatório de {mes_sel}", csv_mensal, f"contas_{mes_sel}_{ano_sel}.csv", "text/csv")
        else:
            st.warning(f"Nenhuma conta cadastrada para {mes_ref}.")