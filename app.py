import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import extra_streamlit_components as stx
import time

# Importações de base de dados e utilitários
from database import (
    criar_tabelas, obter_categorias, obter_todas_despesas, 
    obter_receitas_raw, obter_pessoas, verificar_login, criar_usuario
)

# Importações dos módulos da pasta telas
from telas import dashboard, lancamentos, parcelamentos, categorias, pessoas

# =========================================================
# ⚙️ CONFIGURAÇÃO INICIAL (OBRIGATÓRIO SER O PRIMEIRO COMANDO)
# =========================================================
st.set_page_config(page_title="B&D Finance", layout="wide", initial_sidebar_state="expanded")

# Redução dos espaços em branco no topo
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 💾 ESTADOS DE SESSÃO E BANCO DE DADOS
# =========================================================
if "mes_selecionado" not in st.session_state:
    st.session_state.mes_selecionado = "Ano Inteiro"
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "clicou_sair" not in st.session_state:
    st.session_state.clicou_sair = False

# Garante que as tabelas existem no banco
criar_tabelas()


# =========================================================
# 🍪 INICIALIZAÇÃO SEGURA DO GERENCIADOR DE COOKIES
# =========================================================
if "cookie_manager" not in st.session_state:
    st.session_state.cookie_manager = stx.CookieManager(key="gerenciador_cookies_bd")

cookie_manager = st.session_state.cookie_manager

@st.cache_data(ttl=600) # Guarda os dados na memória por 10 minutos (600 segundos)
def carregar_despesas_com_cache(user_id):
    df = obter_todas_despesas(user_id)
    if not df.empty:
        df['Ano'] = df['mes_ano'].str.split('/').str[1]
        df['Mes_Num'] = df['mes_ano'].str.split('/').str[0]
    else:
        df['Ano'] = pd.Series(dtype='str')
        df['Mes_Num'] = pd.Series(dtype='str')
    return df

@st.cache_data(ttl=600)
def carregar_receitas_com_cache(user_id):
    df = obter_receitas_raw(user_id)
    if not df.empty:
        df['Ano'] = df['mes_ano'].str.split('/').str[1]
        df['Mes_Num'] = df['mes_ano'].str.split('/').str[0]
    else:
        df['Ano'] = pd.Series(dtype='str')
        df['Mes_Num'] = pd.Series(dtype='str')
    return df

# Para listas simples, também podemos cachear para poupar o banco
@st.cache_data(ttl=600)
def carregar_filtros_com_cache(user_id):
    categorias_ativas = obter_categorias(user_id)
    pessoas_ativas = obter_pessoas(user_id)
    return categorias_ativas, pessoas_ativas


# =========================================================
# 🔄 LÓGICA DE LOGIN AUTOMÁTICO (MANTER CONECTADO)
# =========================================================
if not st.session_state.logado and not st.session_state.clicou_sair:
    # Pequeno respiro para o componente conseguir ler os dados do navegador no primeiro frame
    if not cookie_manager.get_all():
        time.sleep(0.1)

    cookie_id = cookie_manager.get("bd_user_id")
    cookie_user = cookie_manager.get("bd_username")
    
    # Se encontrou os cookies salvos no navegador:
    if cookie_id and cookie_user:
        st.session_state.logado = True
        st.session_state.usuario_id = int(cookie_id) 
        st.session_state.username = cookie_user
        
        st.rerun() # Pula a tela de login para o painel principal


# =========================================================
# 🔐 SESSÃO DE AUTENTICAÇÃO (TELA DE LOGIN / REGISTRO)
# =========================================================
if not st.session_state.logado:
    
    st.write("") 
    
    # Layout em 2 colunas
    col_esq, col_dir = st.columns([0.6, 1.4], gap="large")
    
    with col_esq:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("assets/logo.png", use_container_width=True)
        
    with col_dir:
        st.markdown("<h2 style='text-align: left;'>Bem-vindo ao B&D Finance</h2>", unsafe_allow_html=True)
        
        aba_auth = st.tabs(["🔒 Entrar no Sistema", "📝 Criar Nova Conta"])
        
        # --- ABA 1: LOGIN ---
        with aba_auth[0]:
            user_input = st.text_input("Usuário:", key="login_user").strip()
            pass_input = st.text_input("Senha:", type="password", key="login_pass")

            manter_logado = st.checkbox("Manter conectado")

            if st.button("Login", use_container_width=True, type="primary"):
                sucesso, user_id = verificar_login(user_input, pass_input)

                if sucesso:
                    st.session_state.logado = True
                    st.session_state.usuario_id = user_id
                    st.session_state.username = user_input.capitalize()
                    
                    # Reseta a flag de logout para permitir futuros logins automáticos normais
                    st.session_state.clicou_sair = False

                    if manter_logado:
                        validade = datetime.now() + timedelta(days=30)
                        cookie_manager.set("bd_user_id", str(user_id), expires_at=validade, key="set_cookie_id")
                        cookie_manager.set("bd_username", user_input.capitalize(), expires_at=validade, key="set_cookie_user")

                    st.success(f"Bem-vindo de volta, {st.session_state.username}!")
                    
                    if manter_logado:
                        time.sleep(0.5)
                        
                    st.rerun()

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
                        
    # Para a execução aqui se não estiver logado
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

st.title(f"B&D Finance — {tela}")
st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# 📊 CARGA E FILTRAGEM DE DADOS (AGORA COM CACHE VIA MEMÓRIA)
# =========================================================
# Busca as listas simples do banco (ou do cache se já foram chamadas)
lista_categorias_ativas, lista_pessoas_ativas = carregar_filtros_com_cache(user_id_ativo)

# Busca os DataFrames já devidamente tratados e splitados de dentro do cache
df_despesas_all = carregar_despesas_com_cache(user_id_ativo)
df_receitas_all = carregar_receitas_com_cache(user_id_ativo)

# Identifica os anos disponíveis na base calculando direto das colunas cacheadas
anos_disponiveis = sorted(list(set(df_despesas_all['Ano'].dropna().unique()).union(set(df_receitas_all['Ano'].dropna().unique()))), reverse=True)
if not anos_disponiveis:
    anos_disponiveis = [datetime.now().strftime("%Y")]

st.sidebar.divider()
st.sidebar.header("Filtros Globais")

ano_selecionado = st.sidebar.selectbox("Selecione o Ano:", anos_disponiveis)

df_desp_ano = df_despesas_all[df_despesas_all['Ano'] == ano_selecionado]
df_rec_ano = df_receitas_all[df_receitas_all['Ano'] == ano_selecionado]

meses_traducao = {
    "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
    "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
    "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"
}
meses_numeros = sorted(list(set(df_desp_ano['Mes_Num'].dropna().unique()).union(set(df_rec_ano['Mes_Num'].dropna().unique()))))


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

opcoes_filtro_pessoas = ["Todos"] + lista_pessoas_ativas
pessoa_selecionada = st.sidebar.selectbox("Filtrar por Pessoa:", opcoes_filtro_pessoas)

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

# =========================================================
# 🚪 BOTÃO DE SAIR / LOGOUT 
# =========================================================
if st.sidebar.button("🚪 Sair / Logout", type="secondary", use_container_width=True):
    # 1. Ativa a trava temporária da sessão
    st.session_state.clicou_sair = True

    # 2. Força o esvaziamento imediato dos valores no navegador (limpa o conteúdo)
    cookie_manager.set("bd_user_id", "", key="clear_cookie_id")
    cookie_manager.set("bd_username", "", key="clear_cookie_user")
    
    # 3. Manda o navegador deletar os arquivos de cookie de vez
    cookie_manager.delete("bd_user_id", key="del_cookie_id")
    cookie_manager.delete("bd_username", key="del_cookie_user")

    # 4. Limpa o estado da sessão do Streamlit
    st.session_state.logado = False
    st.session_state.usuario_id = None
    st.session_state.username = ""
    
    # 5. Damos um tempo ligeiramente maior (0.7s) para garantir que o navegador
    # limpe o cache do disco antes do próximo reload.
    time.sleep(0.7) 
    st.rerun()


# =========================================================
# 🧭 DIRECIONAMENTO SEGURO DAS TELAS
# =========================================================
if tela == "Dashboard":
    dashboard.exibir(df_despesas_filtrado, df_receitas_filtrado, visao_anual)
elif tela == "Receitas/Despesas":
    lancamentos.exibir(lista_categorias_ativas, lista_pessoas_ativas, user_id_ativo)
elif tela == "Parcelamentos":
    parcelamentos.exibir(lista_categorias_ativas, lista_pessoas_ativas, user_id_ativo)
elif tela == "Gerenciar Categorias":
    categorias.exibir(lista_categorias_ativas, user_id_ativo)
elif tela == "Gerenciar Pessoas":
    pessoas.exibir(user_id_ativo)