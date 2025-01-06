import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from rapidfuzz import process, fuzz
from PyPDF2 import PdfReader

# Configuração inicial do Streamlit
st.set_page_config(
    page_title="Sistema de Fiscalização",
    page_icon="🏢",
    layout="wide",
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

# Função de busca
def buscar_com_fuzzy(nome, coluna, df, limite_score=60):
    if df is None:
        return None, "Dados não disponíveis"
    
    try:
        valores_unicos = df[coluna].dropna().unique()
        if not valores_unicos.size:
            return None, "Não há dados disponíveis para busca."
            
        correspondencia = process.extractOne(nome, valores_unicos, scorer=fuzz.ratio)
        if correspondencia and correspondencia[1] >= limite_score:
            return df[df[coluna] == correspondencia[0]], None
        return None, "Nenhuma correspondência encontrada com similaridade suficiente."
    except Exception as e:
        return None, f"Erro na busca: {str(e)}"

# Função para gerar respostas
def resposta_humanizada(contexto, model):
    if model is None:
        return "Serviço de IA não disponível no momento."
    
    try:
        prompt = f"{contexto}\nPor favor, forneça uma explicação clara e objetiva sobre essas informações."
        resposta = model.generate_content(prompt)
        return resposta.content.strip() if hasattr(resposta, "content") else "Conteúdo não disponível."
    except Exception as e:
        return f"Erro ao gerar resposta: {str(e)}"

# Função específica para consulta do código de obras
def consultar_codigo_obras(pergunta, codigo_obras, model):
    if not model:
        return "Serviço de IA não disponível no momento."
    
    if not codigo_obras:
        return "Código de obras não disponível para consulta."
    
    try:
        prompt = (
            "Você é um especialista em legislação municipal e código de obras. "
            "Por favor, analise o seguinte código de obras e responda à pergunta "
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
    st.title("Sistema de Fiscalização - PMT")
    
    # Inicialização dos componentes
    model = inicializar_api()
    df = carregar_planilha()
    codigo_obras = ler_pdf()
    
    # Tabs principais
    tab1, tab2 = st.tabs(["Consulta de Imóvel", "Código de Obras"])
    
    # Tab de Consulta de Imóvel
    with tab1:
        st.header("Consulta de Imóvel")
        endereco = st.text_input("Digite o endereço do imóvel:")
        
        if st.button("Buscar", key="buscar_endereco"):
            if endereco:
                resultado, msg = buscar_com_fuzzy(endereco, 'Endereco', df)
                if resultado is not None:
                    registro = resultado.iloc[0]
                    
                    # Exibição dos resultados
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Dados do Imóvel")
                        st.write(f"**Endereço:** {registro['Endereco']}")
                        st.write(f"**Proprietário:** {registro.get('Proprietario', 'Não informado')}")
                        
                    with col2:
                        st.subheader("Informações da Fiscalização")
                        st.write(f"**Status:** {registro.get('Status', 'Não informado')}")
                        st.write(f"**Data:** {registro.get('Data', 'Não informada')}")
                    
                    # Análise do caso
                    st.subheader("Análise do Caso")
                    contexto = f"Imóvel localizado em {registro['Endereco']}, " \
                             f"propriedade de {registro.get('Proprietario', 'proprietário não informado')}, " \
                             f"com status {registro.get('Status', 'não informado')}."
                    
                    with st.spinner("Gerando análise..."):
                        analise = resposta_humanizada(contexto, model)
                        st.write(analise)
                else:
                    st.warning(msg)
            else:
                st.warning("Por favor, digite um endereço para buscar.")
    
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