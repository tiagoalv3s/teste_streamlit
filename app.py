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
            f"Notificação: Endereço: {reg['Endereco']}, "
            f"Proprietário: {reg.get('Proprietario', 'Não informado')}, "
            f"Status: {reg.get('Status', 'Não informado')}, "
            f"Data: {reg.get('Data', 'Não informada')}"
            for reg in registros[:10]  # Limita a 10 registros para não sobrecarregar
        ])

        prompt = (
            "Você é um especialista em fiscalização municipal. "
            "Com base nos dados das notificações abaixo, "
            "analise a consulta do usuário e forneça informações relevantes "
            "de forma clara e objetiva. Se encontrar registros relacionados, "
            "detalhe as informações encontradas.\n\n"
            f"Dados das notificações:\n{contexto_dados}\n\n"
            f"Consulta do usuário: {query}\n\n"
            "Por favor, forneça uma resposta detalhada e profissional, "
            "incluindo todas as informações relevantes encontradas."
        )

        resposta = model.generate_content(prompt)
        return resposta.content.strip() if hasattr(resposta, "content") else "Não foi possível processar a consulta."
    except Exception as e:
        return f"Erro ao processar a consulta: {str(e)}"

# Função para consulta do código de obras (mantida como estava)
def consultar_codigo_obras(pergunta, codigo_obras, model):
    if not model:
        return "Serviço de IA não disponível no momento."
    
    if not codigo_obras:
        return "Código de obras não disponível para consulta."
    
    try:
        prompt = (
            "Você é um especialista em legislação municipal e código de obras."
            "Por favor, analise o seguinte código de obras e responda à pergunta."
            "de forma clara, objetiva e técnica, citando os artigos relevantes quando aplicável.\n\n"
            f"Código de Obras:\n{codigo_obras}\n\n"
            f"Pergunta: {pergunta}\n"
        )
        
        resposta = model.generate_content(prompt)
        if hasattr(resposta, "text"):
            return resposta.text
        elif hasattr(resposta, "content"):
            return resposta.content
        else:
            return "Não foi possível gerar uma resposta adequada."
    except Exception as e:
        return f"Erro ao processar a consulta: {str(e)}"

# Interface principal
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
        query = st.text_area("Digite sua consulta (endereço, proprietário, status, etc.):")
        
        if st.button("Buscar", key="buscar_notificacao"):
            if query:
                with st.spinner("Analisando sua consulta..."):
                    resposta = buscar_notificacao(query, df, model)
                    st.write(resposta)
            else:
                st.warning("Por favor, digite sua consulta.")
    
    # Tab do Código de Obras
    with tab2:
        st.header("Código de Obras")
        pergunta = st.text_area("Digite sua pergunta sobre o código de obras:")
        
        if st.button("Consultar", key="consultar_codigo"):
            if pergunta:
                with st.spinner("Analisando sua pergunta..."):
                    resposta = consultar_codigo_obras(pergunta, codigo_obras, model)
                    st.write(resposta)
            else:
                st.warning("Por favor, digite uma pergunta para consultar.")

if __name__ == "__main__":
    main()