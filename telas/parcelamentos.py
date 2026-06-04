# telas/parcelamentos.py
import streamlit as st
from datetime import datetime
from database import salvar_parcelamento, obter_parcelamentos_ativos, remover_parcelamento

# Adicionado usuario_id na assinatura da função
def exibir(lista_categorias_ativas, lista_pessoas_ativas, usuario_id):
    st.subheader("Inserir Compra Parcelada")
    
    meses_nomes = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    meses_mapa = {nome: f"{i:02d}" for i, nome in enumerate(meses_nomes, 1)}
    
    ano_atual = datetime.now().year
    anos_opcoes = [ano_atual - 2, ano_atual - 1, ano_atual, ano_atual + 1, ano_atual + 2]
    
    with st.form("form_parc", clear_on_submit=True):
        col_p1, col_p2 = st.columns(2)
        
        desc_p = col_p1.text_input("Descrição (Opcional)")
        cat_p = col_p1.selectbox("Categoria", lista_categorias_ativas)
        quem_p = col_p1.selectbox("Pagante", lista_pessoas_ativas)
        
        st.write("**Início do Contrato:**")
        col_m, col_a = col_p2.columns(2)
        mes_p_nome = col_m.selectbox("Mês da 1ª Parcela", meses_nomes, index=datetime.now().month - 1)
        ano_p_num = col_a.selectbox("Ano da 1ª Parcela", anos_opcoes, index=anos_opcoes.index(ano_atual))
        
        num_p = col_p2.number_input("Número de Parcelas", min_value=2, max_value=48, value=12, step=1)
        total_p_texto = col_p2.text_input("Valor Total da Compra (R$)", value="0.00", placeholder="Ex: 00.00")
        
        sub_p = st.form_submit_button("Inserir Parcelamento", use_container_width=True)
        if sub_p:
            if quem_p:
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

                # Passando usuario_id para a função de salvar
                salvar_parcelamento(desc_p, cat_p, quem_p, mes_p_formatado, num_p, total_p, usuario_id)
                st.success(f"Parcelamento cadastrado com sucesso iniciando em {mes_p_nome}/{ano_p_num}!")
                st.rerun()
            else:
                st.error("Por favor, cadastre uma pessoa na aba 'Gerenciar Pessoas' primeiro!")
            
    st.markdown("---")
    st.subheader("Contratos de Parcelamento Ativos")
    
    # Passando usuario_id para buscar apenas os parcelamentos do usuário logado
    df_ativos = obter_parcelamentos_ativos(usuario_id)
    
    if not df_ativos.empty:
        st.dataframe(df_ativos, use_container_width=True, hide_index=True)
        
        st.markdown("Cancelar / Excluir Contrato de Parcelamento")
        st.caption("Aviso: Isso apagará TODAS as parcelas vinculadas a este contrato de uma vez só.")
        
        col_del1, col_del2 = st.columns([2, 1])
        
        contrato_selecionado = col_del1.selectbox(
            "Selecione o ID do Contrato para remover:", 
            df_ativos["ID Contrato"].tolist()
        )
        
        if col_del2.button("Apagar Contrato Inteiro", type="primary", use_container_width=True):
            # Passando usuario_id para segurança na remoção
            remover_parcelamento(contrato_selecionado, usuario_id)
            st.success(f"Contrato {contrato_selecionado} e todas as suas parcelas foram removidos!")
            st.rerun()
    else:
        st.info("Nenhum contrato de parcelamento cadastrado.")