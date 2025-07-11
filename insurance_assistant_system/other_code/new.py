import os
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI
import agno
from agno.vectordb.milvus import Milvus
from agno.embedder.openai import OpenAIEmbedder
from agno.models.google import Gemini
from typing import List, Dict

load_dotenv()

# Configuration
MILVUS_HOST = os.getenv("MILVUS_HOST")
MILVUS_PORT = os.getenv("MILVUS_PORT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
COLLECTION_NAME = "insurance_customers"
EMBEDDING_DIMENSION = 1536

# Initialize Embedder and Vector Database
openai_embedder = OpenAIEmbedder(id="text-embedding-3-large", api_key=OPENAI_API_KEY, dimensions=EMBEDDING_DIMENSION)
milvus_vector_db = Milvus(collection=COLLECTION_NAME, uri="http://localhost:19530", embedder=openai_embedder)

class MilvusRetriever:
    def __init__(self, vector_db: Milvus, top_k: int = 3):
        self.vector_db = vector_db
        self.top_k = top_k

    def retrieve(self, query: str) -> List[Dict]:
        results = self.vector_db.similarity_search(
            query=query,
            k=self.top_k,
            output_fields=["customer_name", "policy_types", "metadata"]
        )
        return results

class GeminiLLM:
    def __init__(self, google_api_key: str):
        self.model = Gemini(id="gemini-2.0-flash", api_key=google_api_key)

    def generate(self, prompt: str) -> str:
        response = self.model(prompt)
        return response

class SimpleChatbot:
    def __init__(self, retriever: MilvusRetriever, llm: GeminiLLM):
        self.retriever = retriever
        self.llm = llm

    def chat(self, query: str) -> str:
        relevant_docs = self.retriever.retrieve(query)
        context = "\n\n".join([f"Customer Name: {doc['customer_name']}, Policies: {doc['policy_types']}, Details: {doc['metadata']}" for doc in relevant_docs])
        prompt = f"""You are a helpful chatbot answering questions about insurance customers based on the provided context.
        Answer the question concisely.

        Context:
        {context}

        Question: {query}

        Answer:"""
        response = self.llm.generate(prompt)
        return response

# Initialize components
retriever = MilvusRetriever(milvus_vector_db)
llm = GeminiLLM(GOOGLE_API_KEY)
chatbot = SimpleChatbot(retriever, llm)

# Streamlit UI
st.title("Insurance Customer Chatbot")
query = st.text_input("Ask a question about our customers:")

if query:
    with st.spinner("Searching and generating answer..."):
        answer = chatbot.chat(query)
        st.write("Answer:", answer)