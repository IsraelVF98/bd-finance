# telas/pessoas.py
import streamlit as st
from database import obter_pessoas, adicionar_pessoa, remover_pessoa

# Adicionado usuario_id na assinatura da função
def exibir(usuario_id):
    st.subheader("Gerenciar Usuários")
    st.markdown("Adicione ou remova as pessoas que realizam movimentações financeiras no app.")
    
    # Passando o usuario_id para buscar apenas as pessoas deste usuário
    lista_pessoas = obter_pessoas(usuario_id)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Adicionar Novo Usuário")
        nova_pessoa = st.text_input("Nome do Usuário:", placeholder="Ex: João, Maria...")
        if st.button("Cadastrar Usuário", use_container_width=True):
            if nova_pessoa:
                # Passando o usuario_id para a função de salvar
                sucesso = adicionar_pessoa(nova_pessoa, usuario_id)
                if sucesso:
                    st.success(f"'{nova_pessoa}' adicionado(a) com sucesso!")
                    st.rerun()
                else:
                    st.warning("Usuário já existente.")
            else:
                st.error("O campo Usuário não pode estar vazio.")
                
    with col2:
        st.write("### Pessoas Cadastradas")
        if lista_pessoas:
            for pessoa in lista_pessoas:
                c1, c2 = st.columns([3, 1])
                c1.write(f"▪️ **{pessoa}**")
                if c2.button("Excluir", key=f"del_{pessoa}", type="secondary"):
                    # Passando o usuario_id para a função de remover
                    remover_pessoa(pessoa, usuario_id)
                    st.success(f"'{pessoa}' removido!")
                    st.rerun()
        else:
            st.info("Nenhuma pessoa cadastrada ainda.")