# DocuMind: Enterprise RAG System Presentation Script

## Slide 1: Introduction
**Speaker:**
"Good morning/afternoon everyone. Today I'd like to present **DocuMind**, an intelligent document question-answering system we've built.

The core problem we addressed is that traditional 'Ctrl+F' keyword search fails for complex enterprise documents. It misses context and can't answer semantic questions like 'What is the policy for remote work?'.

DocuMind is a **Retrieval-Augmented Generation (RAG)** system that allows users to chat with their PDF documents naturally, providing accurate, cited, and trustworthy answers."

---

## Slide 2: The Tech Stack
**Speaker:**
"To build this, we used a modern, open-source friendly stack centered around Python:

*   **LangChain:** This is our orchestration framework. It handles the glue logic between our documents, the database, and the AI model.
*   **Unstructured.io:** We use this for robust PDF processing. It doesn't just grab text; it understands document layout, which is crucial for enterprise files.
*   **Pinecone:** This is our Serverless Vector Database. It stores the 'semantic meaning' of our data, allowing for lightning-fast retrieval of relevant information.
*   **HuggingFace (`all-MiniLM-L6-v2`):** This is our embedding model. It runs locally and converts text into numerical vectors.
*   **Ollama (Llama 3):** For the intelligence layer, we are using a local instance of Llama 3 via Ollama. This ensures data privacy and zero inference costs."

---

## Slide 3: Architecture Overview
**Speaker:**
"Our system operates in two distinct pipelines:
1.  **Ingestion Pipeline:** Prepares the data.
2.  **Retrieval Engine:** Answers the questions.

Let's break them down."

---

## Slide 4: The Ingestion Pipeline (Step-by-Step)
**Speaker:**
"First, how do we get data *in*? We built a robust ingestion script (`ingestion.py`):

1.  **Loading:** We iterate through a directory of PDFs. We use `UnstructuredPDFLoader` with a 'fast' strategy to extract text while explicitly tracking metadata like **Page Numbers**. This is critical for citations later.
2.  **Cleaning:** We apply a cleaning layer to normalize whitespace and remove noise.
3.  **Chunking:** We use the `RecursiveCharacterTextSplitter`. Instead of arbitrarily cutting text, we split it into 1000-character chunks with a 200-character overlap. This ensures that sentences aren't cut in half and context is preserved.
4.  **Embedding & Storage:** These chunks are converted into vectors using our HuggingFace model and upserted into **Pinecone**, along with their metadata (Filename, Page Number)."

---

## Slide 5: The Retrieval Engine (The "Brain")
**Speaker:**
"Once data is indexed, users can ask questions using our engine (`retrieval.py`):

1.  **History Awareness:** If a user asks a follow-up question like 'What about the second option?', raw search fails. We implemented a **Query Rewriter** that looks at the chat history and transforms that vague question into a specific search query.
2.  **Semantic Search:** We search Pinecone for the top 5 most similar chunks to the user's question.
3.  **Confidence Gating:** This is a key safety feature. If the most relevant document has a similarity score below **50% (0.50)**, the system immediately refuses to answer. This prevents the model from hallucinating specific answers from irrelevant documents."

---

## Slide 6: Generating Trustworthy Answers
**Speaker:**
"Finally, we generate the answer. We use a **Strict System Prompt** for Llama 3.
We enforce three rules:
1.  Answer **ONLY** using the provided context.
2.  If you don't know, say 'I don't know'. **Do not make things up.**
3.  **Cite your sources.**

Every answer DocuMind provides includes the exact filename and page number where the information was found, creating a fully auditable trail."

---

## Slide 7: Conclusion
**Speaker:**
"In summary, DocuMind is not just a chatbot. It is a strictly controlled, history-aware, and auditable research assistant providing Enterprise-grade reliability using open-source tools.

Thank you."
