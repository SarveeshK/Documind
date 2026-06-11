# WEEK 1: DOCUMENT INGESTION PIPELINE DESIGN

## STEP 1: DOCUMENT LOADING

### WHAT is implemented
A robust document loading pipeline using `Unstructured.io` specifically configured for heavy enterprise PDFs.
- **Input:** Directory of PDF files (Policies, SOPs).
- **Process:** Extracts raw text while Strictly preserving page numbers and document metadata.
- **Output:** List of `LangChain` Document objects, each containing `page_content`, `source`, and `page_number`.

### WHY it is required
Enterprise documents are complex. They contain columns, tables, headers, and footers.
- **Naive loaders (like PyPDF2)** often merge headers into body text or fail to handle multi-column layouts, resulting in "sentence salad."
- **Page number preservation is mandatory** for compliance. You cannot just say "Source: HR Policy"; you must say "Source: HR Policy, Page 12" to be legally defensible.

### WHAT fails if skipped
- **Loss of context:** Inaccurate text extraction leads to garbage embeddings.
- **Compliance failure:** Users cannot verify the answer if they don't know exactly where it came from.
- **Hallucination trigger:** Mixed-up text (e.g., reading across columns instead of down) creates non-existent sentences.

### Common Mistakes & Best Practices
- **Mistake:** Using simple text extraction that ignores layout.
- **Mistake:** Discarding page numbers to "save space."
- **Best Practice:** Use "hi_res" or "fast" strategy in Unstructured based on doc complexity. Focus on capturing the *structure*, not just the characters.

---

## STEP 2: DOCUMENT CLEANING & NORMALIZATION

### WHAT is implemented
A preprocessing layer that runs *before* chunking.
- **Regex Cleaning:** Removes repetitive headers/footers (e.g., "Company Confidential 2024" on every page).
- **Whitespace Normalization:** Collapses multiple spaces/newlines into single separators.
- **De-hyphenation:** Recombines words split across lines (e.g., "responsi-\nbility" -> "responsibility").

### WHY it is required
- **Noise Reduction:** "Company Confidential" appearing 500 times in your vector store biases search results towards that phrase rather than actual content.
- **Semantic Integrity:** Random newlines break sentences, confusing the embedding model which expects coherent thought vectors.

### WHAT fails if skipped
- **Poor Retrieval:** Searching for "confidential" returns every single page instead of relevant security policies.
- **Fragmented Embeddings:** Split words result in different tokens, missing the semantic meaning of the original word.

---

## STEP 3: CHUNKING STRATEGY (CRITICAL)

### WHAT is implemented
`RecursiveCharacterTextSplitter` with `parent_document` tracking.
- **Chunk Size:** 1000 characters (Optimized for `text-embedding-3-small`).
- **Overlap:** 200 characters (Ensures context continuity across boundaries).
- **Metadata Injection:** Every chunk *inherits* `filename` and `page_number` from the parent.

### WHY it is required
- **Fixed-size chunking fails** because it cuts sentences in half ("The policy states that employees must... [CUT]").
- **Recursive chunking** attempts to split on paragraphs, then sentences, preserving semantic wholes.
- **Parent IDs** allow for future "Parent Document Retrieval" strategies (Week 2), where specific chunks fetch larger context windows.

### WHAT fails if skipped
- **Context Loss:** Answers become fragmented or nonsensical.
- **Orphaned Chunks:** If a chunk lacks metadata, you can retrieve it but you won't know where it came from.

---

## STEP 4: EMBEDDING GENERATION

### WHAT is implemented
Generation of vector representations using `openai.embeddings.create` with model `text-embedding-3-small`.
- **Dimensions:** 1536 (Standard for this model).
- **Batching:** Documents are embedded in batches to handle rate limits and network efficiency.

### WHY it is required
- **Semantic Search:** We don't just want keyword matches (Ctrl+F). We want to find "remuneration" when searching for "salary". Embeddings map text to a high-dimensional semantic space where similar concepts are close together.
- **Cost/Performance:** `text-embedding-3-small` allows for massive scale at low cost while outperforming older Ada-002 models.

### WHAT fails if skipped
- **Keyword-only search limits:** Users must guess the exact words used in the policy.
- **Zero Intelligence:** The system cannot understand intent or nuance.

---

## STEP 5: VECTOR DATABASE STORAGE

### WHAT is implemented
`Pinecone` Vector Database integration.
- **Index:** Serverless index configured for cosine similarity.
- **Upsert:** Batched upload of (ID, Vector, Metadata) tuples.
- **Metadata:** `text`, `source`, `page`, `chunk_index`.

### WHY it is required
- **Speed:** RAG needs to search millions of tokens in milliseconds. SQL databases are too slow for high-dimensional vector math.
- **Enterprise-Grade:** Pinecone handles infrastructure, scaling, and filtering (e.g., "Search only within 'HR Manual'").

### WHAT fails if skipped
- **Scalability:** Local vector stores (like FAISS in memory) crash with large datasets.
- **Filtering capability:** You cannot efficiently restrict answers to specific documents without robust metadata indexing.
