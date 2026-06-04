# database.py
import sqlite3
import pandas as pd

def conectar():
    return sqlite3.connect("financeiro.db")

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    
    # Tabela de despesas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_parcelamento TEXT,
        num_parcela TEXT,
        categoria TEXT,
        descricao TEXT,
        valor REAL,
        quem_pagou TEXT,
        mes_ano TEXT
    )""")
    
    # Tabela de receitas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS receitas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fonte TEXT,
        descricao TEXT,
        valor REAL,
        mes_ano TEXT
    )""")
    
    # Tabela de categorias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )""")
    
    # Tabela de Pessoas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pessoas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )""")
    
    conn.commit()
    conn.close()

# --- FUNÇÕES DE CATEGORIAS ---
def obter_categorias():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM categorias ORDER BY nome ASC")
    dados = cursor.fetchall()
    conn.close()
    return [linha[0] for linha in dados]

def adicionar_categoria(nome):
    """Adiciona uma nova categoria ao banco de dados"""
    if not nome.strip():
        return False
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categorias (nome) VALUES (?)", (nome.strip(),))
        conn.commit()
        sucesso = True
    except sqlite3.IntegrityError:
        sucesso = False  # Categoria já existe
    conn.close()
    return sucesso

def remover_categoria(nome):
    """Remove uma categoria do banco de dados"""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorias WHERE nome = ?", (nome,))
    conn.commit()
    conn.close()

# --- FUNÇÕES DE LANÇAMENTOS E CONSULTAS ---
def salvar_despesa(mes_ano, categoria, descricao, valor, quem_pagou):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO despesas (mes_ano, categoria, descricao, valor, quem_pagou)
    VALUES (?, ?, ?, ?, ?)
    """, (mes_ano, categoria, descricao, valor, quem_pagou))
    conn.commit()
    conn.close()

def salvar_receita(mes_ano, fonte, valor):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO receitas (mes_ano, fonte, valor)
    VALUES (?, ?, ?)
    """, (mes_ano, fonte, valor))
    conn.commit()
    conn.close()

def obter_todas_despesas():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM despesas", conn)
    conn.close()
    return df

def obter_receitas_raw():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM receitas", conn)
    conn.close()
    return df

def obter_ultimos_registros(tipo):
    conn = conectar()
    if tipo == "Despesas Avulsas":
        df = pd.read_sql_query("SELECT id as ID, mes_ano as 'Mês/Ano', categoria as Categoria, descricao as 'Descrição', valor as 'Valor (R$)', quem_pagou as 'Quem Pagou' FROM despesas WHERE id_parcelamento IS NULL ORDER BY id DESC LIMIT 10", conn)
    else:
        df = pd.read_sql_query("SELECT id as ID, mes_ano as 'Mês/Ano', fonte as 'Fonte/Membro', valor as 'Valor (R$)' FROM receitas ORDER BY id DESC LIMIT 10", conn)
    conn.close()
    return df

def remover_registro(tipo, id_registro):
    conn = conectar()
    cursor = conn.cursor()
    if tipo == "Despesas Avulsas":
        cursor.execute("DELETE FROM despesas WHERE id = ?", (id_registro,))
    else:
        cursor.execute("DELETE FROM receitas WHERE id = ?", (id_registro,))
    conn.commit()
    conn.close()

# --- FUNÇÕES DE PARCELAMENTOS ---
def salvar_parcelamento(descricao, categoria, quem_pagou, mes_inicial, qtd_parcelas, valor_total):
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    conn = conectar()
    cursor = conn.cursor()
    
    id_parc = f"PARC_{int(datetime.now().timestamp())}"
    valor_parcela = round(valor_total / qtd_parcelas, 2)
    data_atual = datetime.strptime(mes_inicial, "%m/%Y")
    
    for i in range(1, qtd_parcelas + 1):
        mes_parc = data_atual.strftime("%m/%Y")
        desc_completa = f"{descricao} ({i}/{qtd_parcelas})"
        
        cursor.execute("""
        INSERT INTO despesas (id_parcelamento, num_parcela, categoria, descricao, valor, quem_pagou, mes_ano)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (id_parc, f"{i}/{qtd_parcelas}", categoria, desc_completa, valor_parcela, quem_pagou, mes_parc))
        
        data_atual += relativedelta(months=1)
        
    conn.commit()
    conn.close()

def obter_parcelamentos_ativos():
    conn = conectar()
    query = """
    SELECT id_parcelamento as 'ID Contrato', 
           categoria as Categoria, 
           quem_pagou as 'Responsável', 
           COUNT(*) as 'Parcelas Totais',
           SUM(valor) as 'Valor Total'
    FROM despesas 
    WHERE id_parcelamento IS NOT NULL 
    GROUP BY id_parcelamento
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# --- SEÇÃO: GERENCIAMENTO DE PESSOAS ---

def obter_pessoas():
    """Retorna uma lista simples com o nome de todas as pessoas cadastradas"""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS pessoas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)")
    cursor.execute("SELECT nome FROM pessoas ORDER BY nome ASC")
    dados = cursor.fetchall()
    conn.close()
    return [linha[0] for linha in dados]

def adicionar_pessoa(nome):
    """Adiciona uma nova pessoa ao banco de dados se não existir duplicada"""
    if not nome.strip():
        return False
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO pessoas (nome) VALUES (?)", (nome.strip(),))
        conn.commit()
        sucesso = True
    except sqlite3.IntegrityError:
        sucesso = False  # Nome duplicado
    conn.close()
    return sucesso

def remover_pessoa(nome):
    """Remove o nome da pessoa da tabela de cadastros ativos"""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pessoas WHERE nome = ?", (nome,))
    conn.commit()
    conn.close()