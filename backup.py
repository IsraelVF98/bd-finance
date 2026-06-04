# backup.py
import streamlit as st
import os
import shutil
from datetime import datetime

def exibir_sidebar():
    st.sidebar.divider()
    st.sidebar.header("Backup dos Dados")

    # Botão 1: Salvar cópia local na pasta do projeto
    if st.sidebar.button("Criar Cópia de Segurança Local", use_container_width=True):
        if not os.path.exists("backups"):
            os.makedirs("backups")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_backup = f"backups/financeiro_backup_{timestamp}.db"
        
        try:
            shutil.copy("financeiro.db", nome_backup)
            st.sidebar.success(f"Salvo em: {nome_backup}")
        except Exception as e:
            st.sidebar.error(f"Erro ao salvar: {e}")

    # Botão 2: Download direto para o computador do utilizador
    try:
        if os.path.exists("financeiro.db"):
            with open("financeiro.db", "rb") as f:
                st.sidebar.download_button(
                    label="Baixar Arquivo de Banco (.db)",
                    data=f,
                    file_name=f"financeiro_backup_{datetime.now().strftime('%Y%m%d')}.db",
                    mime="application/x-sqlite3",
                    use_container_width=True
                )
    except:
        st.sidebar.warning("Banco de dados ainda não gerado para download.")    