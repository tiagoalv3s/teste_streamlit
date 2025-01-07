import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from rapidfuzz import process, fuzz
from PyPDF2 import PdfReader

# Configuração inicial do Streamlit
st.set_page_config(
    page_title="Fiscalização",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# Funções de carregamento de dados
def carregar_planilha():
    try:
        df = pd.read_excel('planilha_notif.xlsx')
        if df.empty:
            st.error("A planilha está vazia.")
            return None
        # Padronizar os nomes das colunas
        df.columns = [col.strip().lower() for col in df.columns]
        return df
    except FileNotFoundError:
        st.error("Arquivo 'planilha_notif.xlsx' não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")
        return None

def ler_pdf():
    try:
        with open("codigo_obras.pdf", "rb") as file:
            pdf_reader = PdfReader(file)
            return " ".join([page.extract_text() for page in pdf_reader.pages])
    except FileNotFoundError:
        st.error("Arquivo 'codigo_obras.pdf' não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar o código de obras: {e}")
        return None

# Inicialização da API
def inicializar_api():
    load_dotenv()
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        st.error("Chave da API não encontrada no arquivo .env")
        return None
    
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name="gemini-1.5-flash")
    except Exception as e:
        st.error(f"Erro ao inicializar a API: {e}")
        return None

# Função de busca inteligente em notificações
def buscar_notificacao(query, df, model):
    if df is None:
        return "Dados não disponíveis para consulta."
    
    try:
        # Converte o DataFrame para texto para contextualização
        registros = df.to_dict('records')
        contexto_dados = "\n".join([
            f"Notificação {idx + 1}:\n"
            f"- Endereço: {reg.get('endereco', 'Não informado')}\n"
            f"- Proprietário: {reg.get('proprietario', 'Não informado')}\n"
            f"- Status: {reg.get('status', 'Não informado')}\n"
            f"- Data: {reg.get('data', 'Não informada')}\n"
            for idx, reg in enumerate(registros[:10])
        ])

        prompt = """
        Você é um agente de fiscalização municipal experiente. Analise a consulta do usuário sobre as notificações 
        e forneça uma resposta profissional e detalhada. Siga estas diretrizes:

        1. Identifique as informações mais relevantes para a consulta
        2. Organize a resposta de forma clara e estruturada
        3. Use linguagem técnica apropriada
        4. Cite números específicos quando disponíveis
        5. Sugira próximos passos ou recomendações quando apropriado

        Dados das notificações disponíveis:
        {contexto}

        Consulta do usuário: {query}

        Responda como um agente de fiscalização, mantendo um tom profissional e prestativo.
        """.format(contexto=contexto_dados, query=query)

        resposta = model.generate_content(prompt)
        return resposta.text if hasattr(resposta, "text") else resposta.content

    except Exception as e:
        return f"Erro ao processar a consulta: {str(e)}"

# Função para consulta do código de obras
def consultar_codigo_obras(pergunta, codigo_obras, model):
    if not model:
        return "Serviço de IA não disponível no momento."
    
    if not codigo_obras:
        return "Código de obras não disponível para consulta."
    
    try:
        prompt = """
        Você é um especialista em legislação municipal e código de obras. Analise a pergunta do usuário 
        e forneça uma resposta técnica e precisa, seguindo estas diretrizes:

        1. Cite os artigos específicos do código de obras relevantes à pergunta
        2. Explique as regulamentações de forma clara e objetiva
        3. Use linguagem técnica apropriada
        4. Forneça exemplos práticos quando pertinente
        5. Indique possíveis exceções ou casos especiais
        
        Código de Obras:
        {codigo}
        
        Pergunta do usuário: {pergunta}
        
        Responda como um especialista em legislação municipal, mantendo um tom técnico e profissional.
        """.format(codigo=codigo_obras, pergunta=pergunta)
        
        resposta = model.generate_content(prompt)
        return resposta.text if hasattr(resposta, "text") else resposta.content

    except Exception as e:
        return f"Erro ao processar a consulta: {str(e)}"

# Interface principal
def main():
    st.title("Sistema de Fiscalização ")
    
    # Inicialização dos componentes
    model = inicializar_api()
    df = carregar_planilha()
    codigo_obras = ler_pdf()
    
    # Tabs principais
    tab1, tab2 = st.tabs(["NOTIFICAÇÕES", "CÓDIGO DE OBRAS"])
    
    # Tab de Notificações
    with tab1:
        st.header("Consulta de Notificações")
        st.markdown("""
        Digite sua consulta sobre notificações. Você pode perguntar sobre:
        - Endereços específicos
        - Status de notificações
        - Informações sobre proprietários
        - Datas de notificações
        """)
        
        query = st.text_area("Digite sua consulta:")
        
        if st.button("Buscar", key="buscar_notificacao"):
            if query:
                with st.spinner("Analisando sua consulta..."):
                    resposta = buscar_notificacao(query, df, model)
                    st.markdown("### Resultado da Consulta")
                    st.write(resposta)
            else:
                st.warning("Por favor, digite sua consulta.")
    
    # Tab do Código de Obras
    with tab2:
        st.header("Consulta ao Código de Obras")
        st.markdown("""
        Digite sua pergunta sobre o código de obras. Você pode perguntar sobre:
        - Regulamentações específicas
        - Requisitos de construção
        - Procedimentos de aprovação
        - Normas técnicas
        """)
        
        pergunta = st.text_area("Digite sua pergunta:")
        
        if st.button("Consultar", key="consultar_codigo"):
            if pergunta:
                with st.spinner("Analisando sua pergunta..."):
                    resposta = consultar_codigo_obras(pergunta, codigo_obras, model)
                    st.markdown("### Resposta")
                    st.write(resposta)
            else:
                st.warning("Por favor, digite uma pergunta para consultar.")

if __name__ == "__main__":
    main()