# telas/categorias.py
import streamlit as st
from database import obter_categorias, adicionar_categoria, remover_categoria

def exibir(lista_categorias_ativas):
    st.subheader("Gerenciar Categorias de Despesas")
    st.markdown("Adicione novas categorias ou remova as existentes para personalizar seus relatórios.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Adicionar Nova Categoria")
        
        # Usamos o formulário para garantir o envio correto dos dados sem renderizações "fantasma"
        with st.form("form_nova_categoria", clear_on_submit=True):
            nova_cat = st.text_input("Nova Categoria:", placeholder="Digite aqui...")
            botao_salvar = st.form_submit_button("Adicionar Nova Categoria", use_container_width=True)
            
            if botao_salvar:
                if nova_cat.strip():
                    # A função retorna True se inseriu e False se a categoria já existia (IntegrityError)
                    sucesso = adicionar_categoria(nova_cat)
                    
                    if sucesso:
                        st.success(f"Categoria '{nova_cat}' adicionada com sucesso!")
                        st.rerun()
                    else:
                        st.warning("Essa categoria já existe no sistema!")
                else:
                    st.error("O campo não pode estar vazio.")
                
    with col2:
        st.write("### Categorias Cadastradas")
        if lista_categorias_ativas:
            for cat in lista_categorias_ativas:
                c1, c2 = st.columns([3, 1])
                c1.write(f"▪️ **{cat}**")
                if c2.button("Excluir", key=f"del_cat_{cat}", type="secondary"):
                    remover_categoria(cat)
                    st.success(f"'{cat}' removida!")
                    st.rerun()
        else:
            st.info("Nenhuma categoria cadastrada ainda.")