import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from rapidfuzz import process, fuzz
from PyPDF2 import PdfReader

# [Código anterior mantido até a função buscar_notificacao]

# Nova função de busca inteligente em notificações
def buscar_notificacao(query, df, model):
    if df is None or model is None:
        return "Sistema indisponível no momento."
    
    try:
        # Preparar dados para análise
        dados_formatados = []
        for _, row in df.iterrows():
            dados_formatados.append({
                'endereco': str(row.get('Endereco', '')),
                'proprietario': str(row.get('Proprietario', '')),
                'status': str(row.get('Status', '')),
                'data': str(row.get('Data', '')),
                'setor': str(row.get('Setor', '')),
                'artigo': str(row.get('Artigo', '')),
                'observacao': str(row.get('Observacao', ''))
            })

        # Criar contexto para a IA
        prompt = f"""
        Você é um assistente especializado em fiscalização municipal. Analise os dados das notificações e responda à consulta do usuário.
        
        Consulta do usuário: {query}
        
        Dados disponíveis das notificações:
        {str(dados_formatados)}
        
        Instruções:
        1. Analise a consulta e os dados disponíveis
        2. Identifique padrões e informações relevantes
        3. Forneça um resumo estruturado das informações encontradas
        4. Se a consulta mencionar um setor, endereço, ou proprietário específico, foque nesses dados
        5. Inclua estatísticas relevantes quando apropriado
        6. Se não encontrar dados específicos, forneça informações gerais relacionadas
        7. Organize a resposta de forma clara e profissional
        8. Caso não encontre informações relacionadas, indique isso claramente
        
        Por favor, forneça uma resposta detalhada e útil.
        """

        # Gerar resposta
        resposta = model.generate_content(prompt)
        if not hasattr(resposta, "content"):
            return "Não foi possível gerar uma resposta adequada."
            
        # Processar e formatar a resposta
        texto_resposta = resposta.content.strip()
        
        # Adicionar cabeçalho informativo
        return f"""### Resultado da Análise

{texto_resposta}

---
*Nota: Esta análise foi gerada com base nos dados disponíveis no sistema.*
"""

    except Exception as e:
        return f"""### Erro na Consulta

Ocorreu um erro ao processar sua consulta: {str(e)}

Por favor, tente reformular sua pergunta ou entre em contato com o suporte técnico se o problema persistir."""

# [Resto do código mantido como estava]

# Modificação na interface principal (dentro da função main())
def main():
    st.title("Fiscalização - PMT")
    
    # Inicialização dos componentes
    model = inicializar_api()
    df = carregar_planilha()
    codigo_obras = ler_pdf()
    
    # Tabs principais
    tab1, tab2 = st.tabs(["NOTIFICAÇÕES", "CÓDIGO DE OBRAS"])
    
    # Tab de Notificações
    with tab1:
        st.header("Consulta de notificações")
        
        # Adicionar exemplos de consultas
        with st.expander("📝 Exemplos de consultas"):
            st.markdown("""
            - "Mostre todas as notificações do Setor 1"
            - "Quantas notificações existem no status pendente?"
            - "Quais são as notificações mais recentes?"
            - "Resumo das notificações por setor"
            - "Buscar notificações do proprietário João"
            - "Notificações da Rua Principal"
            """)
        
        query = st.text_area(
            "Digite sua consulta:",
            placeholder="Ex: Mostre todas as notificações do Setor 1",
            help="Você pode perguntar sobre setores, endereços, proprietários, status, etc."
        )
        
        if st.button("Buscar", key="buscar_notificacao"):
            if query:
                with st.spinner("Analisando dados e gerando resposta..."):
                    resposta = buscar_notificacao(query, df, model)
                    st.markdown(resposta)
            else:
                st.warning("Por favor, digite sua consulta.")
    
    # [Resto do código mantido como estava]

if __name__ == "__main__":
    main()