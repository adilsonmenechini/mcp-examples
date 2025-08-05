import streamlit as st
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiChatbot:
    def __init__(self, model="gemini-2.0-flash"):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = model
        self.config = types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=8192,
            response_modalities=["TEXT"],
        )

    async def generate(self, prompt):
        response = self.client.models.generate_content(
            model=self.model,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=self.config
        )
        return response.text

    # Function to generate 10 blog titles
    def generate_titles(self, topic):
        prompt = f"Gere 10 títulos de blog envolventes em português sobre: {topic}"
        response = self.client.models.generate_content(
            model=self.model,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=self.config
        )
        titles = [title.strip() for title in response.text.split("\n") if title.strip()]
        return titles[:10]  # Ensure only 10 titles are returned

    # Function to generate blog content based on selected title
    def generate_content(self, selected_title):
        prompt = f"Escreva um blog detalhado e bem estruturado sobre: {selected_title}"
        response = self.client.models.generate_content(
            model=self.model,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=self.config
        )
        return response.text

def main():
    # Initialize the chatbot
    chatbot = GeminiChatbot()
    
    # Streamlit UI
    st.title("📝 AI Blog Generator")

    # User Input for Topic
    topic = st.text_input("Enter a topic: ")

    # Generate Titles Button
    if st.button("Generate Titles") and topic:
        with st.spinner('Generating titles...'):
            st.session_state["titles"] = chatbot.generate_titles(topic)

    # Display Titles for Selection
    if "titles" in st.session_state and st.session_state["titles"]:
        st.subheader("📌 Select a Title:")
        selected_title = st.radio("Generated Titles:", st.session_state["titles"])

        # Option to Regenerate Titles
        if st.button("Regenerate Titles") and topic:
            with st.spinner('Regenerating titles...'):
                st.session_state["titles"] = chatbot.generate_titles(topic)
                st.session_state.pop("blog_content", None)  # Clear previous content

        # Generate Blog Button
        if st.button("Generate Blog"):
            with st.spinner('Generating blog content...'):
                st.session_state["blog_content"] = chatbot.generate_content(selected_title)
                st.session_state["selected_title"] = selected_title

    # Show Generated Blog
    if "blog_content" in st.session_state:
        st.subheader("📖 Generated Blog")
        st.markdown(f"### {st.session_state['selected_title']}")
        st.markdown(st.session_state["blog_content"])

if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("GEMINI_API_KEY"):
        st.error("❌ GEMINI_API_KEY not found. Please create a .env file with your API key.")
        st.info("Create a .env file with: GEMINI_API_KEY=your_api_key_here")
    else:
        main()