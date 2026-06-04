import pandas as pd
import sqlite3
import math

ARQUIVO_EXCEL = 'Controle_Financeiro_Dashboard.xlsx'
BANCO_DADOS = 'financeiro.db'

def importar_dados():
    conn = sqlite3.connect(BANCO_DADOS)
    cursor = conn.cursor()
    
    print("⏳ Iniciando leitura do Excel...")
    
    try:
        # Lendo a aba de despesas primeiro para extrair as bases
        print("📊 Lendo aba 'Despesas'...")
        df_despesas = pd.read_excel(ARQUIVO_EXCEL, sheet_name='Despesas')

        # ==========================================
        # 1. EXTRAIR E SALVAR PESSOAS ÚNICAS
        # ==========================================
        # Pega todos os nomes da coluna, remove vazios e pega só os únicos
        pessoas_unicas = df_despesas['Quem Pagou'].dropna().unique()
        print(f"👥 Encontradas {len(pessoas_unicas)} pessoas. Inserindo no banco...")
        for pessoa in pessoas_unicas:
            # Assumindo que sua tabela de pessoas tem uma coluna 'nome'
            cursor.execute("INSERT INTO pessoas (nome) VALUES (?)", (str(pessoa).strip(),))

        # ==========================================
        # 2. EXTRAIR E SALVAR CATEGORIAS ÚNICAS
        # ==========================================
        categorias_unicas = df_despesas['Categoria'].dropna().unique()
        print(f"🏷️ Encontradas {len(categorias_unicas)} categorias. Inserindo no banco...")
        for cat in categorias_unicas:
            # Assumindo que sua tabela de categorias tem uma coluna 'nome'
            cursor.execute("INSERT INTO categorias (nome) VALUES (?)", (str(cat).strip(),))

        # ==========================================
        # 3. IMPORTAR DESPESAS
        # ==========================================
        print("💸 Importando histórico de Despesas...")
        for index, row in df_despesas.iterrows():
            mes = str(row['Mês/Ano'])       
            cat = str(row['Categoria']).strip()     
            desc = str(row['Descrição']) if not pd.isna(row['Descrição']) else ""
            valor = float(row['Valor'])
            quem = str(row['Quem Pagou']).strip()  
            
            cursor.execute('''
                INSERT INTO despesas (mes_ano, categoria, descricao, valor, quem_pagou)
                VALUES (?, ?, ?, ?, ?)
            ''', (mes, cat, desc, valor, quem))
            
        print(f"✅ {len(df_despesas)} Despesas importadas com sucesso!")

        # ==========================================
        # 4. IMPORTAR RECEITAS
        # ==========================================
        print("📈 Lendo aba 'Receitas' e importando...")
        df_receitas = pd.read_excel(ARQUIVO_EXCEL, sheet_name='Receitas')
        
        for index, row in df_receitas.iterrows():
            mes = str(row['Mês/Ano'])
            fonte = str(row['Fonte']).strip()       
            valor = float(row['Valor'])
            
            cursor.execute('''
                INSERT INTO receitas (mes_ano, fonte, valor)
                VALUES (?, ?, ?)
            ''', (mes, fonte, valor))
            
        print(f"✅ {len(df_receitas)} Receitas importadas com sucesso!")

        # Salva tudo de uma vez
        conn.commit()
        print("🎉 Migração completa finalizada perfeitamente!")

    except Exception as e:
        print(f"❌ Ocorreu um erro durante a importação: {e}")
        print("Se o erro for de 'coluna não encontrada', verifique se a tabela do seu banco usa 'nome' ou 'descricao'.")
    
    finally:
        conn.close()

if __name__ == "__main__":
    importar_dados()