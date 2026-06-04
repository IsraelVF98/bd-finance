import streamlit as st
import pandas as pd
from datetime import datetime
import extra_streamlit_components as stx

cookie_manager = stx.CookieManager()
# Importações de base de dados e utilitários (Incluindo as novas funções de login/registro)
from database import (
    criar_tabelas, obter_categorias, obter_todas_despesas, 
    obter_receitas_raw, obter_pessoas, verificar_login, criar_usuario
)

# Importações dos módulos da pasta telas
from telas import dashboard, lancamentos, parcelamentos, categorias, pessoas

# Configuração do Layout Premium
st.set_page_config(page_title="B&D Finance", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        /* Reduz o espaço em branco no topo da página principal */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        /* Oculta o menu padrão do Streamlit e o header (opcional, deixa mais limpo) */
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Inicialização das variáveis de estado (Session State)
if "mes_selecionado" not in st.session_state:
    st.session_state.mes_selecionado = "Ano Inteiro"

# Estados para controlar o Login
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "username" not in st.session_state:
    st.session_state.username = ""

# Inicialização automática das tabelas/migrações no PostgreSQL
criar_tabelas()


# =========================================================
# 🔐 SESSÃO DE AUTENTICAÇÃO (TELA DE LOGIN / REGISTRO)
# =========================================================

if not st.session_state.logado:
    
    # Adicionamos um pequeno respiro no topo para não ficar colado demais
    st.write("") 
    
    # Criamos 2 colunas proporcionais (50% esquerda, 50% direita) com um espaço grande entre elas
    # Dica: se o seu Streamlit estiver atualizado, você pode adicionar: vertical_alignment="center"
    col_esq, col_dir = st.columns([0.6, 1.4], gap="large")
    
    # --- COLUNA DA ESQUERDA (IMAGEM) ---
    with col_esq:
        # Colocamos um pequeno espaçamento para a imagem descer e ficar alinhada com o formulário
        st.markdown("<br><br>", unsafe_allow_html=True)
        # O use_container_width=True garante que ela fique grande, preenchendo o espaço da coluna
        st.image("assets/logo.png", use_container_width=True)
        
    # --- COLUNA DA DIREITA (FORMULÁRIOS) ---
    with col_dir:
        st.markdown("<h2 style='text-align: left;'>Bem-vindo ao B&D Finance</h2>", unsafe_allow_html=True)
        
        # Cria abas internas para alternar entre Fazer Login e Criar Conta
        aba_auth = st.tabs(["🔒 Entrar no Sistema", "📝 Criar Nova Conta"])
        
        # --- ABA 1: LOGIN ---
        with aba_auth[0]:
            user_input = st.text_input("Usuário:", key="login_user").strip()
            pass_input = st.text_input("Senha:", type="password", key="login_pass")

            manter_logado = st.checkbox("Manter conectado")

            if st.button("Aceder ao Painel", use_container_width=True, type="primary"):
                sucesso, user_id = verificar_login(user_input, pass_input)

                if sucesso:
                    st.session_state.logado = True
                    st.session_state.usuario_id = user_id
                    st.session_state.username = user_input.capitalize()

                    if manter_logado:
                        cookie_manager.set("bd_user_id", str(user_id))
                        cookie_manager.set("bd_username", user_input.capitalize())

                    st.success(f"Bem-vindo de volta, {st.session_state.username}!")
                    st.rerun()

                else:
                    st.error("Usuário ou senha incorretos.")

        # --- ABA 2: REGISTRO ---
        with aba_auth[1]:
            new_user = st.text_input("Escolha um Usuário:", key="reg_user").strip()
            new_pass = st.text_input("Escolha uma Senha:", type="password", key="reg_pass")
            confirm_pass = st.text_input("Confirme a Senha:", type="password", key="reg_pass_conf")
            
            if st.button("Cadastrar Conta", use_container_width=True):
                if new_pass != confirm_pass:
                    st.error("As senhas não coincidem!")
                elif len(new_pass) < 4:
                    st.error("A senha deve ter pelo menos 4 caracteres.")
                else:
                    sucesso, msg = criar_usuario(new_user, new_pass)
                    if sucesso:
                        st.success(msg)
                        st.info("Agora já pode voltar à aba de Login e entrar!")
                    else:
                        st.error(msg)
                        
    # Interrompe a execução aqui para não mostrar o sistema por trás sem login
    st.stop()


# =========================================================
# 📐 SISTEMA LIBERADO (A PARTIR DAQUI SÓ SE ESTIVER LOGADO)
# =========================================================
user_id_ativo = st.session_state.usuario_id

st.markdown(
    """
    <style>
        [data-testid="stSidebarUserContent"] { padding-top: 0rem !important; }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0rem !important; }
        [data-testid="stSidebar"] hr { margin-top: 0rem !important; margin-bottom: 0rem !important; }
    </style>
    """,
    unsafe_allow_html=True
)

col_logo1, col_logo2, col_logo3 = st.sidebar.columns([0.4, 3.2, 0.4])
with col_logo2:
    st.image("assets/logo.png", use_container_width=True)

st.sidebar.markdown("---")

# Menu de navegação lateral expandido
st.sidebar.header("Menu")
tela = st.sidebar.radio("Ir para:", [
    "Dashboard", 
    "Receitas/Despesas", 
    "Parcelamentos", 
    "Gerenciar Categorias",
    "Gerenciar Pessoas"
])

# Título dinâmico baseado na tela atual
st.title(f"B&D Finance — {tela}")
st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# 📊 CARGA E FILTRAGEM DE DADOS (PASSANDO O USER ID ATIVO)
# =========================================================
# Nota: Adicionado 'user_id_ativo' para isolar os dados de cada conta
lista_categorias_ativas = obter_categorias(user_id_ativo)
lista_pessoas_ativas = obter_pessoas(user_id_ativo)
df_despesas_all = obter_todas_despesas(user_id_ativo)
df_receitas_all = obter_receitas_raw(user_id_ativo)

# Trata as colunas temporárias de filtragem temporal em memória
if not df_despesas_all.empty:
    df_despesas_all['Ano'] = df_despesas_all['mes_ano'].str.split('/').str[1]
    df_despesas_all['Mes_Num'] = df_despesas_all['mes_ano'].str.split('/').str[0]
else:
    df_despesas_all['Ano'] = pd.Series(dtype='str')
    df_despesas_all['Mes_Num'] = pd.Series(dtype='str')

if not df_receitas_all.empty:
    df_receitas_all['Ano'] = df_receitas_all['mes_ano'].str.split('/').str[1]
    df_receitas_all['Mes_Num'] = df_receitas_all['mes_ano'].str.split('/').str[0]
else:
    df_receitas_all['Ano'] = pd.Series(dtype='str')
    df_receitas_all['Mes_Num'] = pd.Series(dtype='str')

# Descobre anos disponíveis para os Seletores
anos_disponiveis = sorted(list(set(df_despesas_all['Ano'].dropna().unique()).union(set(df_receitas_all['Ano'].dropna().unique()))), reverse=True)
if not anos_disponiveis:
    anos_disponiveis = [datetime.now().strftime("%Y")]

st.sidebar.divider()
st.sidebar.header("Filtros Globais")

# 1º Filtro: Seleção do Ano
ano_selecionado = st.sidebar.selectbox("Selecione o Ano:", anos_disponiveis)

df_desp_ano = df_despesas_all[df_despesas_all['Ano'] == ano_selecionado]
df_rec_ano = df_receitas_all[df_receitas_all['Ano'] == ano_selecionado]

meses_traducao = {
    "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
    "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
    "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"
}
meses_numeros = sorted(list(set(df_desp_ano['Mes_Num'].dropna().unique()).union(set(df_rec_ano['Mes_Num'].dropna().unique()))))


# 2º Filtro: CALENDÁRIO EM GRADE
st.sidebar.write("Selecione o Mês:")

is_ano_inteiro = (st.session_state.mes_selecionado == "Ano Inteiro")
if st.sidebar.button("Ano Inteiro", use_container_width=True, type="primary" if is_ano_inteiro else "secondary"):
    st.session_state.mes_selecionado = "Ano Inteiro"
    st.rerun()

meses_grid = [
    ("01", "Jan", "Janeiro"), ("02", "Fev", "Fevereiro"), ("03", "Mar", "Março"), ("04", "Abr", "Abril"),
    ("05", "Mai", "Maio"), ("06", "Jun", "Junho"), ("07", "Jul", "Julho"), ("08", "Ago", "Agosto"),
    ("09", "Set", "Setembro"), ("10", "Out", "Outubro"), ("11", "Nov", "Novembro"), ("12", "Dez", "Dezembro")
]

with st.sidebar:
    for r in range(3):
        cols = st.columns(4)
        for c in range(4):
            idx = r * 4 + c
            mes_codigo, mes_nome_curto, mes_nome_completo = meses_grid[idx]
            
            disponivel = mes_codigo in meses_numeros
            is_active = (st.session_state.mes_selecionado == mes_nome_completo)
            
            with cols[c]:
                if st.button(
                    mes_nome_curto, 
                    key=f"cal_{ano_selecionado}_{mes_codigo}", 
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    disabled=not disponivel
                ):
                    st.session_state.mes_selecionado = mes_nome_completo
                    st.rerun()

mes_selecionado_nome = st.session_state.mes_selecionado

# 3º Filtro: Filtro de Pessoa
opcoes_filtro_pessoas = ["Todos"] + lista_pessoas_ativas
pessoa_selecionada = st.sidebar.selectbox("Filtrar por Pessoa:", opcoes_filtro_pessoas)

# Executa lógica de filtragem final antes de mandar para o Dashboard
visao_anual = (mes_selecionado_nome == "Ano Inteiro")

if visao_anual:
    df_despesas_filtrado = df_desp_ano
    df_receitas_filtrado = df_rec_ano
else:
    mes_codigo = [k for k, v in meses_traducao.items() if v == mes_selecionado_nome][0]
    df_despesas_filtrado = df_desp_ano[df_desp_ano['Mes_Num'] == mes_codigo]
    df_receitas_filtrado = df_rec_ano[df_rec_ano['Mes_Num'] == mes_codigo]

if pessoa_selecionada != "Todos":
    df_despesas_filtrado = df_despesas_filtrado[df_despesas_filtrado['quem_pagou'] == pessoa_selecionada]
    df_receitas_filtrado = df_receitas_filtrado[df_receitas_filtrado['fonte'] == pessoa_selecionada]

st.sidebar.markdown(f"👤 *Logado como:* **{st.session_state.username}**")

if st.sidebar.button("🚪 Sair / Logout", type="secondary", use_container_width=True):

    cookie_manager.delete("bd_user_id")
    cookie_manager.delete("bd_username")

    st.session_state.logado = False
    st.session_state.usuario_id = None
    st.session_state.username = ""

    st.rerun()
# =========================================================
# 🧭 DIRECIONAMENTO SEGURO DAS TELAS
# =========================================================
if tela == "Dashboard":
    dashboard.exibir(df_despesas_filtrado, df_receitas_filtrado, visao_anual)
elif tela == "Receitas/Despesas":
    # Passamos o user_id_ativo para que as sub-telas saibam quem está operando!
    lancamentos.exibir(lista_categorias_ativas, lista_pessoas_ativas, user_id_ativo)
elif tela == "Parcelamentos":
    parcelamentos.exibir(lista_categorias_ativas, lista_pessoas_ativas, user_id_ativo)
elif tela == "Gerenciar Categorias":
    categorias.exibir(lista_categorias_ativas, user_id_ativo)
elif tela == "Gerenciar Pessoas":
    pessoas.exibir(user_id_ativo)