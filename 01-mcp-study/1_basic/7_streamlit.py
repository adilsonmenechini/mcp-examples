# Importa a biblioteca Streamlit para criar a interface web
import streamlit as st

# Configura o título principal da página
st.title("Chatbot")
# Adiciona uma legenda explicativa abaixo do título
st.caption("Este é um chatbot simples criado com Streamlit")

# Cria uma barra lateral para configurações adicionais
with st.sidebar:
    # Adiciona uma caixa de seleção para habilitar/desabilitar o histórico de conversa
    st.checkbox("Habilitar histórico de conversa", value=True)
    
    # Adiciona um menu suspenso para selecionar o modelo de IA
    st.selectbox("Selecione um modelo", ["gpt-3.5-turbo", "gpt-4o"])

# Cria um campo de entrada de texto para o usuário digitar sua mensagem
# A função retorna o texto digitado pelo usuário ou None se nenhum texto foi digitado
user_input = st.chat_input("Digite sua mensagem aqui...")

# Exibe a mensagem do usuário na interface do chat
# A mensagem só é exibida se o usuário digitou algo (user_input não é None)
if user_input:
    st.chat_message("User").write(user_input)