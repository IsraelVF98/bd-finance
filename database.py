# database.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import bcrypt

# Conexão centralizada usando o Streamlit Secrets
def get_engine():
    conn_str = st.secrets["connections"]["postgresql"]["url"]
    return create_engine(conn_str)

engine = get_engine()

# =========================================================
# 🗄️ 1. ESTRUTURA DO BANCO (MIGRAÇÃO AUTOMÁTICA PARA MULTI-USUÁRIO)
# =========================================================
def criar_tabelas():
    """Cria e atualiza as tabelas no PostgreSQL se não existirem."""
    with engine.begin() as conn:
        # 1. Cria a tabela master de usuários primeiro
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """))

        # 2. Cria as tabelas financeiras caso não existam
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
                nome TEXT
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pessoas (
                id SERIAL PRIMARY KEY,
                nome TEXT
            );
        """))

        # 3. MIGRAÇÃO DINÂMICA: Adiciona a coluna 'usuario_id' se ela ainda não existir
        # Isso evita erros no seu Neon PostgreSQL sem apagar seus dados atuais!
        tabelas = ["despesas", "receitas", "categorias", "pessoas"]
        for tabela in tabelas:
            # Verifica se a coluna usuario_id já existe na tabela
            check_col = conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='{tabela}' AND column_name='usuario_id';
            """)).fetchone()
            
            if not check_col:
                # Adiciona a coluna permitindo NULL temporariamente para registros antigos
                conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN usuario_id INTEGER;"))
                # Adiciona a restrição de Chave Estrangeira apontando para a tabela usuarios
                conn.execute(text(f"""
                    ALTER TABLE {tabela} 
                    ADD CONSTRAINT fk_{tabela}_usuario 
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE;
                """))
                
        # Remove a restrição UNIQUE antiga das tabelas de categorias e pessoas, 
        # pois agora o mesmo nome pode existir para usuários diferentes!
        try:
            conn.execute(text("ALTER TABLE categorias DROP CONSTRAINT IF EXISTS categorias_nome_key;"))
            conn.execute(text("ALTER TABLE pessoas DROP CONSTRAINT IF EXISTS pessoas_nome_key;"))
        except Exception:
            pass

# =========================================================
# 🔐 2. FUNÇÕES DE AUTENTICAÇÃO (LOGIN E REGISTRO)
# =========================================================
def criar_usuario(username, password):
    """Cria um novo usuário no PostgreSQL encriptando a senha."""
    if not username.strip() or not password.strip():
        return False, "Usuário ou senha não podem ser vazios."
        
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO usuarios (username, password) VALUES (:username, :password)"),
                {"username": username.lower().strip(), "password": hashed}
            )
        return True, "Usuário registrado com sucesso!"
    except Exception:
        return False, "Este nome de usuário já está em uso."

def verificar_login(username, password):
    """Valida o login no banco de dados. Retorna (True, usuario_id) se correto."""
    if not username.strip() or not password.strip():
        return False, None
        
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, password FROM usuarios WHERE username = :username"),
            {"username": username.lower().strip()}
        )
        row = result.fetchone()
        
    if row:
        user_id, hashed_password = row[0], row[1]
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return True, user_id
            
    return False, None

# =========================================================
# 📥 3. FUNÇÕES ADAPTADAS E FILTRADAS POR USUÁRIO
# =========================================================

# --- FUNÇÕES DE CATEGORIAS ---
def obter_categorias(usuario_id):
    """Retorna categorias ordenadas exclusivas do usuário logado."""
    query = "SELECT nome FROM categorias WHERE usuario_id = :usuario_id ORDER BY nome ASC"
    df = pd.read_sql(text(query), engine, params={"usuario_id": usuario_id})
    if df.empty:
        return []
    return df["nome"].tolist()

def adicionar_categoria(nome, usuario_id):
    """Adiciona uma nova categoria vinculada ao usuário."""
    if not nome.strip():
        return False
    # Verifica se o usuário já possui essa categoria para evitar duplicados para ele
    categorias_atuais = obter_categorias(usuario_id)
    if nome.strip() in categorias_atuais:
        return False
        
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO categorias (nome, usuario_id) VALUES (:nome, :usuario_id)"),
            {"nome": nome.strip(), "usuario_id": usuario_id}
        )
    return True

def remover_categoria(nome, usuario_id):
    """Remove uma categoria pertencente ao usuário."""
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM categorias WHERE nome = :nome AND usuario_id = :usuario_id"),
            {"nome": nome, "usuario_id": usuario_id}
        )

# --- FUNÇÕES DE LANÇAMENTOS E CONSULTAS ---
def salvar_despesa(mes_ano, categoria, descricao, valor, quem_pagou, usuario_id):
    """Guarda uma nova despesa vinculada ao usuário."""
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO despesas (mes_ano, categoria, descricao, valor, quem_pagou, usuario_id)
            VALUES (:mes_ano, :categoria, :descricao, :valor, :quem_pagou, :usuario_id)
        """), {
            "mes_ano": mes_ano,
            "categoria": categoria,
            "descricao": descricao,
            "valor": float(valor),
            "quem_pagou": quem_pagou,
            "usuario_id": usuario_id
        })

def salvar_receita(mes_ano, fonte, valor, usuario_id):
    """Guarda uma nova receita vinculada ao usuário."""
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO receitas (mes_ano, fonte, valor, usuario_id)
            VALUES (:mes_ano, :fonte, :valor, :usuario_id)
        """), {
            "mes_ano": mes_ano,
            "fonte": fonte,
            "valor": float(valor),
            "usuario_id": usuario_id
        })

def obter_todas_despesas(usuario_id):
    """Retorna as despesas exclusivas do usuário logado."""
    query = "SELECT * FROM despesas WHERE usuario_id = :usuario_id"
    return pd.read_sql(text(query), engine, params={"usuario_id": usuario_id})

def obter_receitas_raw(usuario_id):
    """Retorna as receitas exclusivas do usuário logado."""
    query = "SELECT * FROM receitas WHERE usuario_id = :usuario_id"
    return pd.read_sql(text(query), engine, params={"usuario_id": usuario_id})

def obter_ultimos_registros(tipo, usuario_id):
    """Retorna os últimos 10 registos do usuário com base no tipo selecionado."""
    if tipo == "Despesas Avulsas":
        query = """
            SELECT id as "ID", mes_ano as "Mês/Ano", categoria as "Categoria", 
                   descricao as "Descrição", valor as "Valor (R$)", quem_pagou as "Quem Pagou" 
            FROM despesas 
            WHERE id_parcelamento IS NULL AND usuario_id = :usuario_id
            ORDER BY id DESC LIMIT 10
        """
    else:
        query = """
            SELECT id as "ID", mes_ano as "Mês/Ano", fonte as "Fonte/Membro", 
                   valor as "Valor (R$)" 
            FROM receitas 
            WHERE usuario_id = :usuario_id
            ORDER BY id DESC LIMIT 10
        """
    return pd.read_sql(text(query), engine, params={"usuario_id": usuario_id})

def remover_registro(tipo, id_registro, usuario_id):
    """Remove um registro garantindo que pertença ao usuário logado."""
    tabela = "despesas" if tipo == "Despesas Avulsas" else "receitas"
    with engine.begin() as conn:
        conn.execute(
            text(f"DELETE FROM {tabela} WHERE id = :id AND usuario_id = :usuario_id"),
            {"id": int(id_registro), "usuario_id": usuario_id}
        )

# --- FUNÇÕES DE PARCELAMENTOS ---
def salvar_parcelamento(descricao, categoria, quem_pagou, mes_inicial, qtd_parcelas, valor_total, usuario_id):
    """Gera e guarda as parcelas futuras na base de dados vinculadas ao usuário."""
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
                INSERT INTO despesas (id_parcelamento, num_parcela, categoria, descricao, valor, quem_pagou, mes_ano, usuario_id)
                VALUES (:id_parc, :num_parcela, :categoria, :desc_completa, :valor_parcela, :quem_pagou, :mes_parc, :usuario_id)
            """), {
                "id_parc": id_parc,
                "num_parcela": f"{i}/{qtd_parcelas}",
                "categoria": categoria,
                "desc_completa": desc_completa,
                "valor_parcela": valor_parcela,
                "quem_pagou": quem_pagou,
                "mes_parc": mes_parc,
                "usuario_id": usuario_id
            })
            
            data_atual += relativedelta(months=1)

def obter_parcelamentos_ativos(usuario_id):
    """Retorna os contratos de parcelamento ativos do usuário logado."""
    query = """
        SELECT id_parcelamento as "ID Contrato", 
               categoria as "Categoria", 
               quem_pagou as "Responsável", 
               COUNT(*) as "Parcelas Totais",
               SUM(valor) as "Valor Total"
        FROM despesas 
        WHERE id_parcelamento IS NOT NULL AND usuario_id = :usuario_id
        GROUP BY id_parcelamento, categoria, quem_pagou
    """
    return pd.read_sql(text(query), engine, params={"usuario_id": usuario_id})

def remover_parcelamento(id_parcelamento, usuario_id):
    """Remove um parcelamento específico pertencente ao usuário logado."""
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM despesas WHERE id_parcelamento = :id_parc AND usuario_id = :usuario_id"),
            {"id_parc": id_parcelamento, "usuario_id": usuario_id}
        )

# --- SEÇÃO: GERENCIAMENTO DE PESSOAS ---
def obter_pessoas(usuario_id):
    """Retorna a lista de pessoas cadastradas pelo usuário logado."""
    query = "SELECT nome FROM pessoas WHERE usuario_id = :usuario_id ORDER BY nome ASC"
    df = pd.read_sql(text(query), engine, params={"usuario_id": usuario_id})
    if df.empty:
        return []
    return df["nome"].tolist()

def adicionar_pessoa(nome, usuario_id):
    """Adiciona uma nova pessoa vinculada ao usuário logado."""
    if not nome.strip():
        return False
    # Evita duplicados para o mesmo usuário
    pessoas_atuais = obter_pessoas(usuario_id)
    if nome.strip() in pessoas_atuais:
        return False
        
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO pessoas (nome, usuario_id) VALUES (:nome, :usuario_id)"),
            {"nome": nome.strip(), "usuario_id": usuario_id}
        )
    return True

def remover_pessoa(nome, usuario_id):
    """Remove a pessoa pertencente ao usuário logado."""
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM pessoas WHERE nome = :nome AND usuario_id = :usuario_id"),
            {"nome": nome, "usuario_id": usuario_id}
        )