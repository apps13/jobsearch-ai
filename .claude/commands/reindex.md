# /reindex

Re-run the RAG embedding and indexing pipeline against a sample resume to verify
the full chunker → embedder → retriever chain is working correctly.

## What to do when this command is invoked

1. Read `backend/app/services/chunker.py`, `embedder.py`, and `retriever.py` to
   confirm they are present and unmodified.

2. Run a quick smoke test by calling `retrieve_relevant_bullets` with a short
   sample resume string and a sample job description. Print the returned bullets
   to confirm the pipeline executes end-to-end without errors.

   Example invocation (run from `backend/` with the venv active):
   ```
   python - <<'EOF'
   from app.services.retriever import retrieve_relevant_bullets

   resume = """
   Software Engineer with 4 years of experience.
   Built distributed data pipelines using Python and Apache Spark.
   Led a team of 4 engineers on a real-time analytics platform.
   Proficient in AWS, Docker, and Kubernetes.
   B.S. Computer Science, University of Michigan.
   """

   jd = "Looking for a backend engineer with Python, AWS, and data pipeline experience."

   bullets = retrieve_relevant_bullets(resume, jd, top_k=3)
   for b in bullets:
       print("-", b)
   EOF
   ```

3. Confirm the output contains 3 bullets ordered by hybrid relevance (not document
   order), and that no errors are raised from the OpenAI API or BM25.

4. If the OpenAI API call fails (quota, key issue), report the error clearly rather
   than silently returning an empty list.

## Notes

- This command requires `OPENAI_API_KEY` to be set in `backend/.env` (local) or
  Railway environment variables (production). The embedding step makes real API calls.
- No database interaction — the pipeline is stateless and runs entirely in memory.
- If `rank_bm25` or `numpy` are missing, install dependencies first:
  `pip install -r requirements.txt`
