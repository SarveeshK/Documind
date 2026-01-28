# DocuMind: Code-Level Technical Deep Dive

**Format:** This presentation is designed as a live code walkthrough. Open your IDE to the project folder and follow the script below, pointing to the specific files and lines mentioned.

---

## 1. Introduction & Tech Stack
**Action:** Open `requirements.txt` or `ingestion.py` (top imports).

**Speaker:**
"Hello everyone. Today I will walk you through the codebase of **DocuMind**, our Enterprise RAG system. We built this using a modern Python stack.

If we look at our imports in `ingestion.py` (Lines 1-9), you can see the core technologies:
*   **LangChain**: For orchestration.
*   **Pinecone**: Our vector database for storing semantic data.
*   **Unstructured**: For heavy-duty PDF parsing.
*   **HuggingFace**: For generating embeddings locally."

---

## 2. The Ingestion Pipeline (`ingestion.py`)
**Action:** Open `ingestion.py`.

### Step 1: Loading Documents
**Action:** Scroll to `class DocumentLoader` (Line 20) and specifically **Line 40**.

**Speaker:**
"The process starts here. We use `UnstructuredPDFLoader` with `strategy='fast'`.
*   **Why?** Standard loaders just dump text. Unstructured helps us preserve metadata.
*   **Look at Lines 53-54:** We explicitly capture the `page_number`. This is crucial because our system needs to cite exactly where information comes from."

### Step 2: Chunking Strategy
**Action:** Scroll to `class ContentProcessor` (Lines 63-70).

**Speaker:**
"Once loaded, we don't just shove text into the database. We use the `RecursiveCharacterTextSplitter`.
*   **Line 66 (`chunk_size=1000`):** We split text into 1000-character blocks.
*   **Line 67 (`chunk_overlap=200`):** We keep a 200-character overlap. This ensures that if a sentence is split between two chunks, the context isn't lost. The model sees the connection."

### Step 3: Vector Storage
**Action:** Scroll to `upsert_chunks` method (Line 144) and specifically **Lines 160-190**.

**Speaker:**
"Here is where the magic happens.
1.  **Line 161:** We take the text content.
2.  **Line 163:** We use `self.embeddings.embed_documents(texts)` to convert that text into a list of floating-point numbers (vectors).
3.  **Line 189:** We send these vectors to Pinecone. Note that we also send the **Metadata** (Page number, Source file) so we can retrieve it later."

---

## 3. The Retrieval Engine (`retrieval.py`)
**Action:** Open `retrieval.py`.

### Step 1: The Brain (LLM Setup)
**Action:** Scroll to `__init__` (Line 27).

**Speaker:**
"For the reasoning engine, we are using **Ollama** running **Llama 3**.
*   **Line 27:** `ChatOllama(model='llama3', temperature=0)`.
*   We set `temperature=0` to make the model deterministic. We don't want it to be creative; we want it to be factual."

### Step 2: History Awareness
**Action:** Scroll to `get_history_aware_query` (Line 91).

**Speaker:**
"A major challenge in RAG is chat history. If I ask 'matches?' after asking about 'vacation policy', a standard search fails.
*   **Line 105:** We use a LangChain chain here (`prompt | llm`).
*   **Logic:** It takes the chat history and rewrites the user's question to be self-contained *before* we search the database."

### Step 3: Confidence Gating (Safety)
**Action:** Scroll to `get_relevant_context` (Line 29) -> **Lines 43-51**.

**Speaker:**
"This is our safety layer.
*   **Line 46:** We check `if match['score'] >= SIMILARITY_THRESHOLD`.
*   If the retrieved documents aren't similar enough (below 50%), we simply ignore them. This prevents the model from trying to answer questions using irrelevant data."

### Step 4: The Strict System Prompt
**Action:** Scroll to `get_system_prompt` (Line 69).

**Speaker:**
"Finally, this is the instruction manual for our AI.
*   **Rules 1-3:** We explicitly tell it: 'If you don't know, say you don't know.' and 'DO NOT use your own knowledge.'
*   **Rule 4:** We mandate citations: `Format: (Source: [filename], Page: [number])`.
This ensures that every answer DocuMind gives is grounded in your actual documents."

---

## 4. Conclusion
**Speaker:**
"So, referencing the code:
1.  `ingestion.py` handles the ETL (Extract, Transform, Load) process.
2.  `retrieval.py` manages the semantic search and strict generation.

This code structure gives us a verifiable, enterprise-grade Q&A system."
