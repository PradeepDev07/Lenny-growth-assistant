# Agent Session Log: Retrieval Engineering, Hash Collision Failure, & BM25 Resolution

**Timestamp:** 2026-09-05T16:35:00Z  
**Agent:** Antigravity AI Engineer  
**Objective:** Ingest podcast transcripts, build chunking pipeline, and implement vector retrieval.

---

### Step 1: Transcript Ingestion & Chunking
- Curated four canonical transcript datasets in `ingestion/data/`:
  - Elena Verna (B2B PLG & Activation Metrics)
  - Brian Balfour (Growth Loops vs Funnels)
  - Shreyas Doshi (Good vs Great PM Metrics & LNO Framework)
  - Lenny Rachitsky (PMF & 0 to 1 Startups)
- Built `ingestion/chunker.py` with sliding window (1200 chars / ~500 tokens, 200 char overlap).
- Built CLI `ingest.py --refresh`.

---

### Step 2: Failed Attempt — Python Hash Vectorizer Collision
- **Initial Implementation**:
  - Implemented a custom `SemanticVectorizer` with `dim=256` using Python's built-in `hash(token) % 256` and character 3-grams.
- **Observed Failure**:
  - Ran `pytest backend/tests/test_retrieval.py -v`.
  - Result: 3 tests failed:
    - Querying `"How should we measure activation metrics in B2B PLG?"` returned Shreyas Doshi instead of Elena Verna.
    - Querying `"Why do growth loops beat traditional marketing funnels?"` returned Elena Verna instead of Brian Balfour.
- **Root Cause Analysis**:
  1. Python's built-in `hash()` incorporates a per-process randomized seed (`PYTHONHASHSEED`), causing non-deterministic hashing across runs.
  2. A vector dimension of 256 caused severe bucket collisions between common product words like "metrics", "product", and "growth".
  3. Character 3-grams diluted exact keyword and guest name matches.

---

### Step 3: Resolution & Verification
- **Solution**:
  - Replaced the naive hash vectorizer with a deterministic, industrial-grade **BM25Retriever** augmented with metadata field boosting.
  - Formulated $IDF(w) = \ln(1 + \frac{N - n(w) + 0.5}{n(w) + 0.5})$ and $TF(w, D) = \frac{f(w, D) \cdot (k_1 + 1)}{f(w, D) + k_1 \cdot (1 - b + b \cdot \frac{|D|}{\text{avgdl}})}$.
  - Added a 2.5x score boost when query terms match the episode guest name and 1.8x when matching the episode title.
- **Validation**:
  - Re-ran `ingest.py --refresh` and `pytest backend/tests/test_retrieval.py -v`.
  - **Result**: 5/5 tests PASSED in 0.01 seconds.
  - Queries for Elena Verna, Brian Balfour, and Shreyas Doshi achieved 100% top-1 rank precision.
