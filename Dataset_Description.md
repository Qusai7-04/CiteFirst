## 3.1 Dataset Description and Selection Criteria

The dataset functions as a dynamic retrieval corpus rather than a traditional labelled training set. It comprises two parts: (i) a collection of source documents that form the searchable knowledge base, and (ii) an LLM-synthesized "golden dataset" used exclusively for quantitative evaluation.

### 3.1.1 Source Documents
A custom set of 66 peer-reviewed research papers and academic texts was assembled into a local `papers` directory. The documents span several technical and scientific domains auto-detected during ingestion:

- **Machine Learning** – 25 papers
- **Computer Networks** – 21 papers 
- **Database Systems** – 10 papers
- **Signal Processing** – 6 papers
- **Computer Vision** – 2 papers
- **NLP** – 2 papers

Each paper was processed into a dual-tier chunk structure as described in Section 3.2. Specifically, papers were parsed producing **7,456 child chunks** (maximum 100 words, with a 20-word overlap) optimized for precise retrieval via embedded embeddings, and **2,166 parent chunks** (maximum 350 words, with a 75-word overlap) designated exclusively to provide extensive generative context for the LLM. The system employs `BAAI/bge-small-en-v1.5` as the dense embedding model. All pipeline components operate locally using pre-trained foundational models.

### 3.1.2 Golden Dataset for Evaluation
To enable quantitative measurement of retrieval and generation quality, a golden dataset of 18 challenging question-answer pairs was constructed via highly customized synthetic generation utilizing the DeepSeek-R1 model API. 

**Step 1 – Source Sampling and Question Formulation**
Instead of manual ideation, a robust generation script (`generate_dataset.py`) sampled chunks uniformly from the processed document pool (split natively at a 1200-character chunk size strictly for training-set generation). DeepSeek-R1 was prompted in the persona of a Research Professor writing a certification exam to formulate complex questions that strictly require logical reasoning based on the provided text. Ambiguous or opinion-based questions were structurally circumvented.

**Step 2 – Ground Truth Answer Construction**
For every question, DeepSeek-R1 jointly produced a verifiable "ground_truth" answer that can be perfectly derived from the exact document chunk provided in its prompt. The ground truth answer was recorded in a structured JSON dataset alongside the verbatim context extract to enforce strict deterministic relevance scoring during evaluation.

**Step 3 – Search Strategy & Hybrid Retrieval Evaluation**
During logic engine validation against the golden dataset, the retrieval mechanism relies on a hybrid execution strategy combining Dense embeddings and Sparse BM25 retrieval without manual grading. A thresholding function dynamically filters out candidate documents exceeding a pre-defined distance threshold (`0.70`), and reciprocal rank fusion (RRF) evaluates final component relevance. Accurate retrieval is measured based on overlapping context from the synthesized golden set records versus retrieved chunks.

**Step 4 – Dataset Statistics**

| Domain | Papers | Child Chunks | Parent Chunks | Queries (Sampled) |
| :--- | :--- | :--- | :--- | :--- |
| Machine Learning | 25 | 3,453 | ~1,003 | * |
| Computer Networks | 21 | 1,797 | ~522 | * |
| Database Systems | 10 | 1,131 | ~328 | * |
| Signal Processing | 6 | 810 | ~235 | * |
| Computer Vision | 2 | 161 | ~47 | * |
| NLP | 2 | 104 | ~31 | * |
| **Total** | **66** | **7,456** | **2,166** | **18** |

*(Note: The 18 Queries are uniformly randomized across domains depending on the seed.)*

**Example QA Pair from the Golden Dataset**

**Query:** "Based on the text, deduce the logical reasoning that connects the experimental observation of sinuous motion in fluids under specific resistance conditions to the conclusion that properties of matter causing energy transformation have effects beyond heat-motions."

**Ground Truth Answer:** "The experiments with colour bands show that when resistance in steady mean flow varies with a power of velocity higher than the first, the fluid is in a state of sinuous motion. Sinuous motion indicates the presence of eddying motion, which represents relative-motion with finite periods. This prevalence of such resistance serves as direct evidence that energy from mean-motion (with infinite periods) is transformed into energy of relative-motion (eddying motion). This transformation maintains the eddying motion despite the continual conversion of some energy into heat-motions. Therefore, the properties of matter that determine this cause of transformation produce general and important effects, as the sustained eddying motion demonstrates that these effects are not confined to heat-motions alone."

**Source Context Included for Evaluation Mapping:** *"In considering the first of the instances mentioned, it will be seen that the evidence it affords as to the general effect of the properties, on which depends transformation of energy from mean- to relative-motion, is very direct. For, since my experiments with colour bands have shown that when the resistance of fluids, in steady mean flow, varies with a power of the velocity higher than the first the fluid is always in a state of sinuous motion..."*

This golden dataset (`golden_dataset.json`) is isolated entirely from index ingestion or optimization, used exclusively to benchmark the pipeline mechanics out-of-sample.
