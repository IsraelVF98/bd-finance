# telas/dashboard.py
import streamlit as st
import plotly.express as px
import pandas as pd

def exibir(df_despesas_filtrado, df_receitas_filtrado, visao_anual=False):
    # Garantir que lidamos corretamente com maiúsculas/minúsculas vindas do banco de dados
    if 'valor' in df_receitas_filtrado.columns:
        df_receitas_filtrado = df_receitas_filtrado.rename(columns={'valor': 'Valor', 'fonte': 'Fonte', 'descricao': 'Descricao', 'mes_ano': 'Mes_Ano'})
    if 'valor' in df_despesas_filtrado.columns:
        df_despesas_filtrado = df_despesas_filtrado.rename(columns={'valor': 'Valor', 'categoria': 'Categoria', 'descricao': 'Descricao', 'quem_pagou': 'Quem_Pagou', 'mes_ano': 'Mes_Ano'})

    # Agora sim, fazemos as somas com a coluna padronizada como 'Valor'
    rec_total = df_receitas_filtrado['Valor'].sum() if not df_receitas_filtrado.empty else 0.0
    desp_total = df_despesas_filtrado['Valor'].sum() if not df_despesas_filtrado.empty else 0.0
    saldo_total = rec_total - desp_total
    
    # Cards de KPI superiores
    col1, col2, col3 = st.columns(3)
    col1.metric("Receitas Totais", f"R$ {rec_total:,.2f}", delta_color="normal")
    col2.metric("Despesas Totais", f"R$ {desp_total:,.2f}", delta_color="inverse")
    col3.metric("Saldo Líquido", f"R$ {saldo_total:,.2f}", delta="Positivo" if saldo_total >= 0 else "Negativo")
    
    st.markdown("---")
    
    # Gráfico de Linha de Evolução Mensal (Visão Anual)
    if visao_anual:
        st.subheader("📈 Evolução Financeira Mensal")
        
        if not df_despesas_filtrado.empty:
            df_desp_mes = df_despesas_filtrado.groupby('Mes_Ano')['Valor'].sum().reset_index().rename(columns={'Valor': 'Despesas'})
        else:
            df_desp_mes = pd.DataFrame(columns=['Mes_Ano', 'Despesas'])
            
        if not df_receitas_filtrado.empty:
            df_rec_mes = df_receitas_filtrado.groupby('Mes_Ano')['Valor'].sum().reset_index().rename(columns={'Valor': 'Receitas'})
        else:
            df_rec_mes = pd.DataFrame(columns=['Mes_Ano', 'Receitas'])
            
        df_evolucao = pd.merge(df_desp_mes, df_rec_mes, on='Mes_Ano', how='outer').fillna(0)
        
        if not df_evolucao.empty and 'Mes_Ano' in df_evolucao.columns:
            df_evolucao['Data_Obj'] = pd.to_datetime(df_evolucao['Mes_Ano'], format='%m/%Y', errors='coerce')
            df_evolucao = df_evolucao.sort_values('Data_Obj')
            df_melted = df_evolucao.melt(id_vars=['Mes_Ano'], value_vars=['Receitas', 'Despesas'], 
                                         var_name='Fluxo', value_name='Valor')
            
            fig_line = px.line(df_melted, x='Mes_Ano', y='Valor', color='Fluxo', markers=True,
                               color_discrete_map={'Receitas': '#2ecc71', 'Despesas': '#e74c3c'},
                               labels={'Valor': 'Montante (R$)', 'Mes_Ano': 'Competência'})
            fig_line.update_layout(height=350, hovermode="x unified")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Dados insuficientes para gerar a linha histórica de tendência anual.")
        st.markdown("---")
        
    # Gráfico de Gasto por Categoria
    st.subheader("🛍️ Gastos por Categoria")
    if not df_despesas_filtrado.empty:
        cat_chart_df = df_despesas_filtrado.groupby('Categoria')['Valor'].sum().reset_index().sort_values(by='Valor', ascending=False)
        
        fig_cat = px.bar(cat_chart_df, x='Categoria', y='Valor', 
                         text='Valor', color='Valor', color_continuous_scale='Blues',
                         labels={'Valor':'Total Gasto (R$)', 'Categoria':''})
        
        fig_cat.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
        fig_cat.update_layout(showlegend=False, height=450, coloraxis_showscale=False)
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("Nenhuma despesa registrada para este filtro.")

    # --- NOVO GRÁFICO: AVULSO VS PARCELADO ---
    st.markdown("---")
    st.subheader("📊 Origem das Despesas: Avulsas vs. Parcelamentos")
    if not df_despesas_filtrado.empty:
        df_analise = df_despesas_filtrado.copy()
        
        # Identifica se a despesa veio de um parcelamento ou se é avulsa
        if 'id_parcelamento' in df_analise.columns:
            df_analise['Tipo Despesa'] = df_analise['id_parcelamento'].apply(
                lambda x: 'Parcelamento' if pd.notna(x) and str(x).strip() != '' and str(x) != 'None' else 'Despesa Avulsa'
            )
        else:
            df_analise['Tipo Despesa'] = 'Despesa Avulsa'
            
        # Agrupa os valores utilizando a coluna 'Valor' (já padronizada)
        df_resumo_tipo = df_analise.groupby('Tipo Despesa')['Valor'].sum().reset_index()
        
        # Monta o gráfico de rosca (donut chart)
        fig_proporcao = px.pie(
            df_resumo_tipo, 
            values='Valor', 
            names='Tipo Despesa', 
            hole=0.5,
            color='Tipo Despesa',
            color_discrete_map={
                'Despesa Avulsa': '#2ecc71',   # Mesmo verde amigável das receitas
                'Parcelamento': '#e67e22'      # Um laranja/coral elegante para parcelas
            }
        )
        
        fig_proporcao.update_traces(
            textinfo='percent+label', 
            hovertemplate="<b>%{label}</b><br>Total: R$ %{value:,.2f}<br>Proporção: %{percent}<extra></extra>"
        )
        
        fig_proporcao.update_layout(
            height=380,
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=20, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_proporcao, use_container_width=True)
    else:
        st.info("Nenhuma despesa registrada para analisar a composição.")

    st.markdown("---")
    st.subheader("📄 Extrato Detalhado de Despesas do Período")
    if not df_despesas_filtrado.empty:
        df_exibicao = df_despesas_filtrado.rename(columns={
            'Mes_Ano': 'Mês/Ano',
            'Categoria': 'Categoria',
            'Descricao': 'Descrição',
            'Valor': 'Valor (R$)',
            'Quem_Pagou': 'Quem Pagou'
        })
        colunas_exibicao = ['Mês/Ano', 'Categoria', 'Descrição', 'Valor (R$)', 'Quem Pagou'] if visao_anual else ['Categoria', 'Descrição', 'Valor (R$)', 'Quem Pagou']
        colunas_validas = [c for c in colunas_exibicao if c in df_exibicao.columns]
        st.dataframe(df_exibicao[colunas_validas], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado de despesa para exibir no extrato.")