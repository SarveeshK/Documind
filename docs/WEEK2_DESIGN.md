# WEEK 2: RETRIEVAL & ANSWERING ENGINE DESIGN

## STEP 6: ADVANCED RETRIEVAL STRATEGY

### WHAT is implemented
**Hybrid Search** (simulated via Metadata Filtering + Semantic Search).
- While pure hybrid search (bm25 + vector) usually requires external libraries or specific Pinecone configurations, for this "Core Intelligence" phase, we implement **Metadata-Guided Semantic Search**.
- **Process:** We retrieve more chunks than needed (e.g., k=10), then apply a client-side reranking or filtering step if metadata (like 'department') is available in the query context.
- *Future Upgrade:* Full Hybrid Search with Sparse/Dense vectors (Week 3/4).

### WHY it is required
- **Naive similarity search (k-NN) is insufficient** because vectors capture *meaning*, not *keywords*. Searching for "Section 4.2" might retrieve "Chapter 5" because they are semantically similar (both are structural markers), but the user specifically needed Section 4.2.
- **Parent Document Retrieval** (enabled by our Week 1 chunking) allows us to fetch the *surrounding* context of a match, ensuring complete answers.

### WHAT fails if skipped
- **False Positives:** The system returns confident but irrelevant chunks.
- **Missing Specifics:** It fails to find exact IDs, dates, or specific clause numbers that don't have strong semantic "embeddings" but are critical keywords.

---

## STEP 7: SYSTEM PROMPT (ANTI-HALLUCINATION CORE)

### WHAT is implemented
A **STRICT** System Prompt that overrides default LLM behaviors.
- **Core Directive:** "You are an assistant for Question-Answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know. Use three sentences maximum and keep the answer concise."
- **Restraint:** "DO NOT use your own knowledge."
- **Mandatory Failure:** If context is empty, return "I don't know."

### WHY it is required
- **Hallucinations occur** because LLMs are trained to be helpful completions engines. They *want* to finish the sentence, even if they have to make it up.
- **System Prompts are the first line of defense.** They set the "rules of engagement" before the user even speaks.

### WHAT fails if skipped
- **Lying:** The bot comfortably invents a new "Work From Home Policy" because it saw one in its training data from 2021, which conflicts with your actual 2024 policy.
- **Liability:** Legal advice or safety procedures being hallucinated can cause real-world harm.

---

## STEP 8: HISTORY-AWARE RETRIEVAL

### WHAT is implemented
A "Condense Question" Chain.
- **Process:** Before searching, we check if there is chat history. If yes, we ask the LLM to *rewrite* the latest question to stand alone.
- **Example:** User says "What about the second one?" -> System rewrites to "What are the details of the Performance Bonus outlined in the previous answer?" -> Search uses *that*.

### WHY it is required
- **Naive chat memory breaks RAG.** If you search for "What about the second one?", the vector database returns nothing relevant. It has no concept of "the second one".
- **Retrieval must be history-aware** to maintain the illusion of conversation while performing stateless searches.

### WHAT fails if skipped
- **Frustration:** Users cannot ask follow-up questions. They must restate the full context every single time. "Tell me about PTO." -> "How many days?" (Fails) -> "How many days of PTO do I get?" (Succeeds).

---

## STEP 9: ANSWER GENERATION WITH CITATIONS

### WHAT is implemented
Structured Output Parsing.
- **Format:** The LLM is instructed to append `[Source: filename, Page: X]` to every assertion.
- **Verification:** The code post-processes the answer to ensure these citations exist in the *retrieved* context.

### WHY it is required
- **Trust:** "Enterprise Trust" means verifiable truth.
- **Auditability:** If the bot says "You can fire him," you need to know *exactly* which page of the HR manual justifies that.

### WHAT fails if skipped
- **Opacity:** Users get an answer but don't know if it came from the Draft Policy or the Final Policy.
- **Unverifiable Answers:** Critical in legal/medical contexts where "trust me bro" is not acceptable.

---

## STEP 10: REFUSAL LOGIC (HALLUCINATION GUARDRAIL)

### WHAT is implemented
**Confidence Gating.**
- **Similarity Threshold:** If the top retrieved chunk has a cosine similarity score < 0.70 (configurable), we assume the documents are irrelevant.
- **Action:** We immediately return the refusal message *without* even calling the LLM for an answer.

### WHY it is required
- **Refusal is safer than guessing.** If the user asks "How do I bake a cake?" and our manual is about IT Security, the most similar chunk might be "layering security protocols."
- **Forcing an answer** on low-confidence chunks leads to hallucination (e.g., "Layering security protocols is like baking a cake...").

### WHAT fails if skipped
- **Nonsense Answers:** The system tries to connect unrelated concepts to satisfy the query.
- **Erosion of Confidence:** Users stop trusting the system if it answers clearly irrelevant questions.
