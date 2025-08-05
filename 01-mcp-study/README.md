# Gerador de Blog com Google Gemini

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-4285F4?style=for-the-badge&logo=google-gemini&logoColor=white)

Uma aplicação web interativa que utiliza a API do Google Gemini para gerar títulos e conteúdos de blog de forma automatizada.

## 🚀 Funcionalidades

- Geração automática de títulos de blog com base em um tópico
- Geração de conteúdo completo para o título selecionado
- Interface intuitiva e fácil de usar
- Integração com a API do Google Gemini para geração de texto

## 📋 Pré-requisitos

- Python 3.8+
- Conta no [Google AI Studio](https://makersuite.google.com/) para obter uma chave de API
- Conexão com a internet

## 🛠️ Instalação

1. Clone o repositório:
   ```bash
   git clone [URL_DO_REPOSITÓRIO]
   cd mcp-study
   ```

2. Crie e ative um ambiente virtual (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows use: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
   
   Ou instale manualmente:
   ```bash
   pip install google-generativeai python-dotenv streamlit
   ```

4. Crie um arquivo `.env` na raiz do projeto com sua chave de API:
   ```
   GEMINI_API_KEY=sua_chave_aqui
   ```
   > **Nota:** Nunca compartilhe sua chave de API. Adicione `.env` ao seu `.gitignore`.

## 🚀 Como Usar

1. Inicie a aplicação:
   ```bash
   streamlit run main.py
   ```

2. Acesse `http://localhost:8501` no seu navegador

3. No painel da aplicação:
   - Digite um tópico para o seu blog
   - Gere títulos sugeridos
   - Selecione um título e gere o conteúdo completo
   - Copie o conteúdo gerado para usar onde desejar

## 🏗️ Estrutura do Projeto

```
mcp-study/
├── main.py              # Aplicação principal Streamlit
├── pyproject.toml       # Dependências do projeto
├── .env-examples        # Exemplo de configuração
├── .env                 # Configurações locais (não versionado)
└── README.md            # Este arquivo
```

## 🔧 Configuração

Copie o arquivo `.env-examples` para `.env` e preencha com suas credenciais:

```
# Exemplo de .env
GEMINI_API_KEY=sua_chave_aqui
```

## 🤝 Contribuição

Contribuições são bem-vindas! Siga estes passos:

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Adicione suas mudanças (`git add .`)
4. Comite suas mudanças (`git commit -m 'Add some AmazingFeature'`)
5. Faça o Push da Branch (`git push origin feature/AmazingFeature`)
6. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📧 Contato

Seu Nome - [@seu_twitter](https://twitter.com/seu_twitter) - email@exemplo.com

Link do Projeto: [https://github.com/seuusuário/mcp-study](https://github.com/seuusuário/mcp-study)

## 🙏 Agradecimentos

- [Google Gemini](https://gemini.google.com/) pela poderosa API de IA
- [Streamlit](https://streamlit.io/) pelo framework incrível
- A todos os contribuidores que ajudaram a melhorar este projeto