# database.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Conexão centralizada usando o Streamlit Secrets
def get_engine():
    conn_str = st.secrets["connections"]["postgresql"]["url"]
    return create_engine(conn_str)

engine = get_engine()

def criar_tabelas():
    """Cria as tabelas na base de dados PostgreSQL (Neon) se não existirem."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS despesas (
                id SERIAL PRIMARY KEY,
                id_parcelamento TEXT,
                num_parcela TEXT,
                categoria TEXT,
                descricao TEXT,
                valor REAL,
                quem_pagou TEXT,
                mes_ano TEXT
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS receitas (
                id SERIAL PRIMARY KEY,
                fonte TEXT,
                descricao TEXT,
                valor REAL,
                mes_ano TEXT
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                nome TEXT UNIQUE
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pessoas (
                id SERIAL PRIMARY KEY,
                nome TEXT UNIQUE
            );
        """))

# --- FUNÇÕES DE CATEGORIAS ---
def obter_categorias():
    """Retorna uma lista com o nome de todas as categorias ordenadas."""
    df = pd.read_sql("SELECT nome FROM categorias ORDER BY nome ASC", engine)
    if df.empty:
        return []
    return df["nome"].tolist()

def adicionar_categoria(nome):
    """Adiciona uma nova categoria à base de dados."""
    if not nome.strip():
        return False
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO categorias (nome) VALUES (:nome)"),
                {"nome": nome.strip()}
            )
        return True
    except Exception:
        return False  # Retorna False se a categoria já existir (Erro de Integridade)

def remover_categoria(nome):
    """Remove uma categoria da base de dados."""
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM categorias WHERE nome = :nome"),
            {"nome": nome}
        )

# --- FUNÇÕES DE LANÇAMENTOS E CONSULTAS ---
def salvar_despesa(mes_ano, categoria, descricao, valor, quem_pagou):
    """Guarda uma nova despesa na base de dados."""
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO despesas (mes_ano, categoria, descricao, valor, quem_pagou)
            VALUES (:mes_ano, :categoria, :descricao, :valor, :quem_pagou)
        """), {
            "mes_ano": mes_ano,
            "categoria": categoria,
            "descricao": descricao,
            "valor": float(valor),
            "quem_pagou": quem_pagou
        })

def salvar_receita(mes_ano, fonte, valor):
    """Guarda uma nova receita na base de dados."""
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO receitas (mes_ano, fonte, valor)
            VALUES (:mes_ano, :fonte, :valor)
        """), {
            "mes_ano": mes_ano,
            "fonte": fonte,
            "valor": float(valor)
        })

def obter_todas_despesas():
    """Retorna todas as despesas em formato DataFrame."""
    return pd.read_sql("SELECT * FROM despesas", engine)

def obter_receitas_raw():
    """Retorna todas as receitas em formato DataFrame."""
    return pd.read_sql("SELECT * FROM receitas", engine)

def obter_ultimos_registros(tipo):
    """Retorna os últimos 10 registos com base no tipo selecionado."""
    if tipo == "Despesas Avulsas":
        query = """
            SELECT id as "ID", mes_ano as "Mês/Ano", categoria as "Categoria", 
                   descricao as "Descrição", valor as "Valor (R$)", quem_pagou as "Quem Pagou" 
            FROM despesas 
            WHERE id_parcelamento IS NULL 
            ORDER BY id DESC LIMIT 10
        """
    else:
        query = """
            SELECT id as "ID", mes_ano as "Mês/Ano", fonte as "Fonte/Membro", 
                   valor as "Valor (R$)" 
            FROM receitas 
            ORDER BY id DESC LIMIT 10
        """
    return pd.read_sql(query, engine)

def remover_registro(tipo, id_registro):
    """Remove um registo específico (despesa ou receita) pelo ID."""
    tabela = "despesas" if tipo == "Despesas Avulsas" else "receitas"
    with engine.begin() as conn:
        conn.execute(
            text(f"DELETE FROM {tabela} WHERE id = :id"),
            {"id": int(id_registro)}
        )

# --- FUNÇÕES DE PARCELAMENTOS ---
def salvar_parcelamento(descricao, categoria, quem_pagou, mes_inicial, qtd_parcelas, valor_total):
    """Gera e guarda as parcelas futuras na base de dados na nuvem."""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    id_parc = f"PARC_{int(datetime.now().timestamp())}"
    valor_parcela = round(float(valor_total) / int(qtd_parcelas), 2)
    data_atual = datetime.strptime(mes_inicial, "%m/%Y")
    
    with engine.begin() as conn:
        for i in range(1, int(qtd_parcelas) + 1):
            mes_parc = data_atual.strftime("%m/%Y")
            desc_completa = f"{descricao} ({i}/{qtd_parcelas})"
            
            conn.execute(text("""
                INSERT INTO despesas (id_parcelamento, num_parcela, categoria, descricao, valor, quem_pagou, mes_ano)
                VALUES (:id_parc, :num_parcela, :categoria, :desc_completa, :valor_parcela, :quem_pagou, :mes_parc)
            """), {
                "id_parc": id_parc,
                "num_parcela": f"{i}/{qtd_parcelas}",
                "categoria": categoria,
                "desc_completa": desc_completa,
                "valor_parcela": valor_parcela,
                "quem_pagou": quem_pagou,
                "mes_parc": mes_parc
            })
            
            data_atual += relativedelta(months=1)

def obter_parcelamentos_ativos():
    """Retorna o resumo dos contratos de parcelamento ativos."""
    query = """
        SELECT id_parcelamento as "ID Contrato", 
               categoria as "Categoria", 
               quem_pagou as "Responsável", 
               COUNT(*) as "Parcelas Totais",
               SUM(valor) as "Valor Total"
        FROM despesas 
        WHERE id_parcelamento IS NOT NULL 
        GROUP BY id_parcelamento
    """
    return pd.read_sql(query, engine)

# --- SECÇÃO: GERENCIAMENTO DE PESSOAS ---
def obter_pessoas():
    """Retorna uma lista com o nome de todas as pessoas cadastradas."""
    df = pd.read_sql("SELECT nome FROM pessoas ORDER BY nome ASC", engine)
    if df.empty:
        return []
    return df["nome"].tolist()

def adicionar_pessoa(nome):
    """Adiciona uma nova pessoa à base de dados."""
    if not nome.strip():
        return False
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO pessoas (nome) VALUES (:nome)"),
                {"nome": nome.strip()}
            )
        return True
    except Exception:
        return False  # Nome duplicado ou erro de integridade

def remover_pessoa(nome):
    """Remove o nome da pessoa da tabela de cadastros ativos."""
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM pessoas WHERE nome = :nome"),
            {"nome": nome}
        )