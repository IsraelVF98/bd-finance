import streamlit as st
import pandas as pd
from datetime import datetime

# Importações de base de dados e utilitários
from database import criar_tabelas, obter_categorias, obter_todas_despesas, obter_receitas_raw, obter_pessoas

# Importações dos módulos da pasta telas (Incluindo o novo módulo de pessoas)
from telas import dashboard, lancamentos, parcelamentos, categorias, pessoas

# Configuração do Layout Premium
st.set_page_config(page_title="B&D Finance", layout="wide", initial_sidebar_state="expanded")

# Inicialização do estado do mês selecionado para o calendário em grade (Evita bugs ao mudar de página)
if "mes_selecionado" not in st.session_state:
    st.session_state.mes_selecionado = "Ano Inteiro"

# Inicialização da base de dados e tabelas novas
criar_tabelas()

st.markdown(
    """
    <style>
        [data-testid="stSidebarUserContent"] {
            padding-top: 0rem !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0rem !important;
        }
        [data-testid="stSidebar"] hr {
            margin-top: 0rem !important;
            margin-bottom: 0rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Mantém a proporção de colunas que gostaste
col_logo1, col_logo2, col_logo3 = st.sidebar.columns([0.5, 3, 0.5])

with col_logo2:
    st.image("assets/logo.png", use_container_width=True)

st.sidebar.markdown("---")

# Menu de navegação lateral expandido (Atualizado para usar 'tela' em vez de 'aba')
st.sidebar.header("Menu")
tela = st.sidebar.radio("Ir para:", [
    "Dashboard", 
    "Receitas/Despesas", 
    "Parcelamentos", 
    "Gerenciar Categorias",
    "Gerenciar Pessoas"
])

# Título dinâmico baseado na tela atual
st.title(f"{tela}")
st.markdown("<br>", unsafe_allow_html=True) # Dá um espacinho elegante abaixo do título

# Carga de dados dinâmicos do banco
lista_categorias_ativas = obter_categorias()
lista_pessoas_ativas = obter_pessoas()
df_despesas_all = obter_todas_despesas()
df_receitas_all = obter_receitas_raw()

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

# Botão principal de Ano Inteiro com destaque visual dinâmico
is_ano_inteiro = (st.session_state.mes_selecionado == "Ano Inteiro")
if st.sidebar.button("Ano Inteiro", use_container_width=True, type="primary" if is_ano_inteiro else "secondary"):
    st.session_state.mes_selecionado = "Ano Inteiro"
    st.rerun()

# Mapeamento com abreviações para os botões caberem perfeitamente na barra lateral
meses_grid = [
    ("01", "Jan", "Janeiro"), ("02", "Fev", "Fevereiro"), ("03", "Mar", "Março"), ("04", "Abr", "Abril"),
    ("05", "Mai", "Maio"), ("06", "Jun", "Junho"), ("07", "Jul", "Julho"), ("08", "Ago", "Agosto"),
    ("09", "Set", "Setembro"), ("10", "Out", "Outubro"), ("11", "Nov", "Novembro"), ("12", "Dez", "Dezembro")
]

# Montagem da estrutura de Grade 3x4 integrada na Sidebar
with st.sidebar:
    for r in range(3):
        cols = st.columns(4)
        for c in range(4):
            idx = r * 4 + c
            mes_codigo, mes_nome_curto, mes_nome_completo = meses_grid[idx]
            
            # Regras dinâmicas do botão
            disponivel = mes_codigo in meses_numeros
            is_active = (st.session_state.mes_selecionado == mes_nome_completo)
            
            with cols[c]:
                if st.button(
                    mes_nome_curto, 
                    key=f"cal_{ano_selecionado}_{mes_codigo}", 
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                    disabled=not disponivel # Desativa meses sem dados cadastrados no ano
                ):
                    st.session_state.mes_selecionado = mes_nome_completo
                    st.rerun()

# Atribuição da variável para manter a compatibilidade perfeita com os teus filtros originais
mes_selecionado_nome = st.session_state.mes_selecionado


# 3º Filtro: Filtro de Pessoa Alimentado Dinamicamente do banco de dados
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


# =========================================================
# 🧭 DIRECIONAMENTO SEGURO DAS TELAS (AGORA NO LUGAR CERTO!)
# =========================================================
if tela == "Dashboard":
    dashboard.exibir(df_despesas_filtrado, df_receitas_filtrado, visao_anual)
elif tela == "Receitas/Despesas":
    lancamentos.exibir(lista_categorias_ativas, lista_pessoas_ativas)
elif tela == "Parcelamentos":
    parcelamentos.exibir(lista_categorias_ativas, lista_pessoas_ativas)
elif tela == "Gerenciar Categorias":
    categorias.exibir(lista_categorias_ativas)
elif tela == "Gerenciar Pessoas":
    pessoas.exibir()