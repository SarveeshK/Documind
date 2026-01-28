import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableBranch
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Configuration
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "llama3" # Free Local Model
SIMILARITY_THRESHOLD = 0.50 # Strictness level

class RAGEngine:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(INDEX_NAME)
        print(f"Loading local embedding model: {EMBEDDING_MODEL}...")
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.llm = ChatOllama(model=LLM_MODEL, temperature=0) # Temp 0 for determinism

    def get_relevant_context(self, query: str) -> List[Dict]:
        """
        Step 6 & 10: Retrieval with Confidence Gating
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Search Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True
        )
        
        # Step 10: Refusal Logic (Similarity Threshold)
        valid_matches = []
        for match in results['matches']:
            if match['score'] >= SIMILARITY_THRESHOLD:
                valid_matches.append(match)
            else:
                # Log dumped matches for debugging
                # print(f"Skipped low confidence match: {match['score']}")
                pass
                
        if not valid_matches:
            return [] # Logic will trigger refusal
            
        return valid_matches

    def format_docs_for_prompt(self, docs) -> str:
        """
        Formats retrieved docs into a string for the strict prompt.
        Includes Source and Page Number explicitly.
        """
        formatted_string = ""
        for doc in docs:
            meta = doc['metadata']
            formatted_string += f"---\nSource: {meta.get('source', 'Unknown')}\nPage: {meta.get('page_number', 'N/A')}\nContent: {meta.get('text', '')}\n"
        return formatted_string

    def get_system_prompt(self) -> ChatPromptTemplate:
        """
        Step 7: Strict System Prompt
        """
        system_template = """You are DocuMind, a strictly context-aware assistant.
        
        RULES:
        1. Answer the user's question LITERALLY based ONLY on the provided context below.
        2. If the answer is not in the context, say EXACTLY: "I don't know. This information is outside my provided documents."
        3. DO NOT use your own outside knowledge.
        4. Cite your sources. Every claim must have a reference. 
           Format: (Source: [filename], Page: [number])
        
        CONTEXT:
        {context}
        """
        return ChatPromptTemplate.from_messages([
            ("system", system_template),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])

    def get_history_aware_query(self, query: str, chat_history: List) -> str:
        """
        Step 8: History-Aware Retrieval
        Rewrites the query if there is history.
        """
        if not chat_history:
            return query
            
        prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
            ("system", "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation. Only return the query, no other text.")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        new_query = chain.invoke({"chat_history": chat_history, "question": query})
        print(f"Rewritten Query: {new_query}")
        return new_query

    def query(self, user_question: str, chat_history: List = []) -> str:
        """
        Main RAG Pipeline
        """
        # 1. Contextualize Query
        search_query = self.get_history_aware_query(user_question, chat_history)
        
        # 2. Retrieve & Gate
        matches = self.get_relevant_context(search_query)
        
        if not matches:
            # Step 10: Immediate Refusal
            return "I don't know. This information is outside my provided documents. (No relevant matches found above confidence threshold)"
            
        context_str = self.format_docs_for_prompt(matches)
        
        # 3. Generate Answer
        prompt = self.get_system_prompt()
        chain = prompt | self.llm | StrOutputParser()
        
        response = chain.invoke({
            "context": context_str,
            "chat_history": chat_history,
            "question": user_question
        })
        
        return response

# CLI for Verification
if __name__ == "__main__":
    engine = RAGEngine()
    
    print("--- DocuMind Enterprise CLI (Week 2) ---")
    print("Type 'exit' to quit.")
    
    history = []
    
    while True:
        q = input("\nQuery: ")
        if q.lower() == "exit":
            break
            
        print("\nThinking...")
        try:
            ans = engine.query(q, history)
            print(f"\nAnswer:\n{ans}")
            
            # Simple history management
            history.append(HumanMessage(content=q))
            history.append(AIMessage(content=ans))
        except Exception as e:
            print(f"Error: {e}")
