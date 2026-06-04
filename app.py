# app.py
import streamlit as st
import pandas as pd
from datetime import datetime

# Importações de banco de dados e utilitários
from database import criar_tabelas, obter_categorias, obter_todas_despesas, obter_receitas_raw, obter_pessoas
import backup 

# Importações dos módulos da pasta telas (Incluindo o novo modulo de pessoas)
from telas import dashboard, lancamentos, parcelamentos, categorias, pessoas

# Configuração do Layout Premium
st.set_page_config(page_title="B&D Finance", layout="wide", initial_sidebar_state="expanded")

# Inicialização do banco de dados e tabelas novas
criar_tabelas()

st.title("B&D Finance")

# Menu de navegação lateral expandido
st.sidebar.header("Menu")
aba = st.sidebar.radio("Ir para:", [
    "Dashboard", 
    "Receitas/Despesas", 
    "Parcelamentos", 
    "Gerenciar Categorias",
    "Gerenciar Pessoas"
])

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

# 2º Filtro: Mês condicional (Cascata)
opcoes_meses = ["Ano Inteiro"] + [meses_traducao[m] for m in meses_numeros if m in meses_traducao]
mes_selecionado_nome = st.sidebar.selectbox("Selecione o Mês:", opcoes_meses)

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
    # Aqui os filtros de Quem Pagou e Fonte também foram ajustados para o padrão do banco
    df_despesas_filtrado = df_despesas_filtrado[df_despesas_filtrado['quem_pagou'] == pessoa_selecionada]
    df_receitas_filtrado = df_receitas_filtrado[df_receitas_filtrado['fonte'] == pessoa_selecionada]

# Chamada do módulo de segurança
backup.exibir_sidebar()

# Direcionamento para as telas correspondentes
if aba == "Dashboard":
    dashboard.exibir(df_despesas_filtrado, df_receitas_filtrado, visao_anual)
elif aba == "Receitas/Despesas":
    # Passamos a lista de categorias e a lista de pessoas ativas dinâmicas do banco
    lancamentos.exibir(lista_categorias_ativas, lista_pessoas_ativas)
elif aba == "Parcelamentos":
    parcelamentos.exibir(lista_categorias_ativas, lista_pessoas_ativas)
elif aba == "Gerenciar Categorias":
    categorias.exibir(lista_categorias_ativas)
elif aba == "Gerenciar Pessoas":
    pessoas.exibir()