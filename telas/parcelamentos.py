# telas/parcelamentos.py
import streamlit as st
from datetime import datetime
from database import salvar_parcelamento, obter_parcelamentos_ativos

def exibir(lista_categorias_ativas, lista_pessoas_ativas):
    st.subheader("Inserir Compra Parcelada")
    
    # Lista de meses para o seletor visual
    meses_nomes = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    # Dicionário para transformar o nome do mês no número com dois dígitos (ex: "Junho" -> "06")
    meses_mapa = {nome: f"{i:02d}" for i, nome in enumerate(meses_nomes, 1)}
    
    # Lista de anos dinâmica (Ano atual, 2 passados e 2 futuros)
    ano_atual = datetime.now().year
    anos_opcoes = [ano_atual - 2, ano_atual - 1, ano_atual, ano_atual + 1, ano_atual + 2]
    
    with st.form("form_parc", clear_on_submit=True):
        col_p1, col_p2 = st.columns(2)
        
        # Coluna 1: Informações gerais
        desc_p = col_p1.text_input("Descrição (Opcional)")
        cat_p = col_p1.selectbox("Categoria", lista_categorias_ativas)
        quem_p = col_p1.selectbox("Pagante", lista_pessoas_ativas)
        
        # Coluna 2: Regras do parcelamento e a Nova Seleção de Mês/Ano
        st.write("**Início do Contrato:**")
        col_m, col_a = col_p2.columns(2)
        mes_p_nome = col_m.selectbox("Mês da 1ª Parcela", meses_nomes, index=datetime.now().month - 1)
        ano_p_num = col_a.selectbox("Ano da 1ª Parcela", anos_opcoes, index=anos_opcoes.index(ano_atual))
        
        num_p = col_p2.number_input("Número de Parcelas", min_value=2, max_value=48, value=12, step=1)
        total_p_texto = col_p2.text_input("Valor Total da Compra (R$)", value="0.00", placeholder="Ex: 00.00")
        
        sub_p = st.form_submit_button("Inserir Parcelamento", use_container_width=True)
        if sub_p:
            if quem_p:
                # 🔄 Junta e formata os seletores para o padrão string "MM/AAAA"
                mes_codigo = meses_mapa[mes_p_nome]
                mes_p_formatado = f"{mes_codigo}/{ano_p_num}"

                try:
                    total_p = float(total_p_texto.replace(",", "."))
                except ValueError:
                    st.error("Valor inválido. Use números como 1500.00 ou 1500,00")
                    st.stop()
                if total_p <= 0:
                    st.error("O valor total deve ser maior que zero.")
                    st.stop()

                salvar_parcelamento(desc_p, cat_p, quem_p, mes_p_formatado, num_p, total_p)
                st.success(f"Parcelamento cadastrado com sucesso iniciando em {mes_p_nome}/{ano_p_num}!")
                st.rerun()
            else:
                st.error("Por favor, cadastre uma pessoa na aba 'Gerenciar Pessoas' primeiro!")
            
    st.markdown("---")
    st.subheader("Contratos de Parcelamento Ativos")
    df_ativos = obter_parcelamentos_ativos()
    st.dataframe(df_ativos, use_container_width=True, hide_index=True)