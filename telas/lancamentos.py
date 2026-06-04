# telas/lancamentos.py
import streamlit as st
from datetime import datetime
import pandas as pd
from database import salvar_despesa, salvar_receita, remover_registro, engine

# Adicionado usuario_id na assinatura da função
def exibir(lista_categories_ativas, lista_pessoas_ativas, usuario_id):
    st.subheader("Adicionar Novos Lançamentos")
    
    meses_nomes = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    meses_mapa = {nome: f"{i:02d}" for i, nome in enumerate(meses_nomes, 1)}
    
    ano_atual = datetime.now().year
    anos_opcoes = [ano_atual - 2, ano_atual - 1, ano_atual, ano_atual + 2, ano_atual + 1]
    anos_opcoes = sorted(list(set(anos_opcoes)))
    
    tab_desp, tab_rec = st.tabs(["Inserir Despesa", "Inserir Receita"])
    
    with tab_desp:
        with st.form("form_despesa", clear_on_submit=True):
            st.write("### Nova Despesa")
            col_m1, col_a1 = st.columns(2)
            mes_d_nome = col_m1.selectbox("Mês de Competência", meses_nomes, index=datetime.now().month - 1, key="mes_desp")
            ano_d_num = col_a1.selectbox("Ano de Competência", anos_opcoes, index=anos_opcoes.index(ano_atual), key="ano_desp")
            
            st.divider()
            col_d1, col_d2 = st.columns(2)
            cat_d = col_d1.selectbox("Categoria", lista_categories_ativas)
            quem_d = col_d1.selectbox("Pagante", lista_pessoas_ativas)
            
            desc_d = col_d2.text_input("Descrição (Opcional)")
            val_d_texto = col_d2.text_input("Valor (R$)", value="0.00", placeholder="00.00")
            
            sub_d = st.form_submit_button("Inserir Despesa", use_container_width=True)
            if sub_d:
                if quem_d:
                    mes_codigo = meses_mapa[mes_d_nome]
                    mes_d_formatado = f"{mes_codigo}/{ano_d_num}"

                    try:
                        val_d = float(val_d_texto.replace(",", "."))
                    except ValueError:
                        st.error("Valor inválido. Use números como 10.50 ou 10,50")
                        st.stop()
                    if val_d <= 0:
                        st.error("O valor deve ser maior que zero.")
                        st.stop()

                    # Chamada com o usuario_id
                    salvar_despesa(mes_d_formatado, cat_d, desc_d, val_d, quem_d, usuario_id)
                    st.success(f"Despesa adicionada com sucesso para {mes_d_nome}/{ano_d_num}!")
                    st.rerun()
                else:
                    st.error("Por favor, cadastre uma pessoa na aba 'Gerenciar Pessoas' primeiro!")
                
    with tab_rec:
        with st.form("form_receita", clear_on_submit=True):
            st.write("### Nova Receita")
            col_m2, col_a2 = st.columns(2)
            mes_r_nome = col_m2.selectbox("Mês de Competência", meses_nomes, index=datetime.now().month - 1, key="mes_rec")
            ano_r_num = col_a2.selectbox("Ano de Competência", anos_opcoes, index=anos_opcoes.index(ano_atual), key="ano_rec")
            
            st.divider()
            fonte_r = st.selectbox("Fonte/Membro", lista_pessoas_ativas)
            val_r = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
            
            sub_r = st.form_submit_button("Inserir Receita", use_container_width=True)
            if sub_r:
                if fonte_r:
                    mes_codigo = meses_mapa[mes_r_nome]
                    mes_r_formatado = f"{mes_codigo}/{ano_r_num}"
                    
                    # Chamada com o usuario_id
                    salvar_receita(mes_r_formatado, fonte_r, val_r, usuario_id)
                    st.success(f"Receita adicionada com sucesso para {mes_r_nome}/{ano_r_num}!")
                    st.rerun()
                else:
                    st.error("Por favor, cadastre uma pessoa na aba 'Gerenciar Pessoas' primeiro!")

    # --- SEÇÃO DE GERENCIAMENTO E EXCLUSÃO AVANÇADA ---
    st.markdown("---")
    st.subheader("Imprimir / Corrigir Lançamentos Recentes")
    
    tipo_excluir = st.radio("Selecione o tipo de registro que deseja remover:", ["Despesas Avulsas", "Receitas"], horizontal=True)
    
    col_b1, col_b2 = st.columns([2, 1])
    termo_busca = col_b1.text_input("🔍 Buscar por Palavra-chave (Descrição, Categoria, Quem Pagou):", placeholder="Ex: Financiamento, Seguro, Cachorro...")
    qtd_exibir = col_b2.selectbox("Quantidade de registros exibidos:", [10, 20, 50, 100, "Todos"], index=0)
    
    # Query SQL filtrada pelo usuario_id
    try:
        if tipo_excluir == "Despesas Avulsas":
            query = f'SELECT id AS "ID", mes_ano AS "Mês/Ano", categoria AS "Categoria", descricao AS "Descrição", valor AS "Valor (R$)", quem_pagou AS "Quem Pagou" FROM despesas WHERE usuario_id = {usuario_id} ORDER BY id DESC'
        else:
            query = f'SELECT id AS "ID", mes_ano AS "Mês/Ano", fonte AS "Fonte/Membro", descricao AS "Descrição", valor AS "Valor (R$)" FROM receitas WHERE usuario_id = {usuario_id} ORDER BY id DESC'
            
        with engine.connect() as conn:
            df_del = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        df_del = pd.DataFrame()
        
    if not df_del.empty and termo_busca:
        mascara_busca = df_del.astype(str).apply(lambda x: x.str.contains(termo_busca, case=False, na=False)).any(axis=1)
        df_del = df_del[mascara_busca]
        
    if not df_del.empty:
        if qtd_exibir != "Todos":
            df_exibicao = df_del.head(int(qtd_exibir))
        else:
            df_exibicao = df_del
            
        st.write(f"Foram encontrados {len(df_del)} registros ao todo (Exibindo os primeiros {len(df_exibicao)}):")
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
        
        col_del1, col_del2 = st.columns([2, 1])
        id_para_deletar = col_del1.selectbox("Selecione o ID exato do registro que deseja apagar:", df_del['ID'].tolist())
        
        if col_del2.button("Confirmar Exclusão", type="primary", use_container_width=True):
            # Chamada com o usuario_id para segurança
            remover_registro(tipo_excluir, id_para_deletar, usuario_id)
            st.success(f"Registro ID {id_para_deletar} removido com sucesso!")
            st.rerun()
    else:
        st.info("Nenhum lançamento encontrado correspondente aos filtros de busca.")