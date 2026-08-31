# Technology Stack

## Backend

- **Python** — Main programming language used to build the AI pipeline and backend logic.
- **FastAPI** — Builds the REST API that connects the React frontend with the AI and database services.
- **Pydantic** — Validates API requests and responses so the system receives and returns structured data.
- **SQLAlchemy** — Connects the Python backend with PostgreSQL and manages database operations using Python.
- **PostgreSQL** — Stores structured meeting data such as meeting details, users, transcripts, summaries, and action items.
- **Alembic** — Manages database schema changes and migrations safely as the project evolves.
- **Uvicorn** — Runs the FastAPI application as a high-performance web server.

## Frontend

- **React** — Builds the interactive user interface for uploading meetings, viewing results, and asking questions.
- **Vite** — Provides a fast development and build environment for the React application.
- **TypeScript** — Adds type safety to the frontend code and helps prevent common JavaScript errors.
- **REST API** — Allows the React frontend to communicate with the FastAPI backend without directly accessing databases or AI services.

## AI — Speech Processing

- **Whisper** — Converts the uploaded meeting audio into text through automatic speech recognition.
- **FFmpeg** — Processes and converts audio files into formats that Whisper and other audio-processing components can work with.

## AI — Speaker Diarization

- **pyannote.audio** — Identifies different speakers and determines which parts of the transcript were spoken by each speaker.

## AI — LLM

- **Google Gemini** — Understands the meeting transcript and generates summaries, decisions, action items, deadlines, and answers to user questions.
- **LangChain** — Provides the framework for connecting Gemini with prompts, retrieval, documents, and the RAG pipeline.
- **langchain-google-genai** — Integrates Google Gemini with LangChain.

## AI — Embeddings

- **Sentence Transformers** — Converts meeting text into numerical vectors that represent the meaning of the text.
- **Embedding Model** — The configured model generates embeddings used for semantic search across previous meetings.

## Vector Database

- **Qdrant** — Stores the meeting embeddings and finds semantically similar pieces of previous meetings during searches.

## RAG — Retrieval-Augmented Generation

- **Document Preparation** — Converts transcripts and meeting information into clean documents suitable for retrieval.
- **Text Chunking** — Splits long transcripts into smaller meaningful pieces so relevant information can be retrieved accurately.
- **Embedding** — Converts each text chunk into a vector representation.
- **Indexing** — Stores the vectors and associated metadata in Qdrant for efficient searching.
- **Retrieval** — Finds the most relevant meeting chunks for a user's question.
- **Reranking** — Optionally reorders retrieved chunks so the most useful information is placed first.
- **Context Construction** — Combines the retrieved information into relevant context for the LLM.
- **Answer Generation** — Gemini uses the retrieved context to generate an answer to the user's question.
- **Evaluation** — Measures whether the RAG system retrieves relevant information and produces correct answers.

## Database & Storage

- **PostgreSQL** — Stores structured application data and metadata.
- **Qdrant** — Stores vector representations for semantic meeting search.
- **Local/File Storage** — Temporarily stores uploaded meeting audio and generated processing outputs during development.

## Configuration & Security

- **python-dotenv / Environment Variables** — Loads configuration such as database URLs, API keys, and model names without hardcoding them.
- **.env** — Stores local secrets and configuration; it must never be committed to GitHub.
- **Pydantic Settings** — Provides structured and validated application configuration.

## Testing & Evaluation

- **Pytest** — Tests backend functions, API endpoints, and AI pipeline components.
- **pytest-asyncio** — Tests asynchronous FastAPI functions and endpoints.
- **Pandas** — Helps prepare and analyze evaluation datasets and experiment results.
- **Scikit-learn** — Provides metrics and utilities that can be useful for evaluating AI components.
- **RAG Evaluation Dataset** — A collection of questions and expected answers used to measure RAG performance.

## Development & Version Control

- **Git** — Tracks changes to the project and allows you to safely manage development stages.
- **GitHub** — Hosts the source code, documentation, issues, and project history.
- **Docker** — Packages the application and its dependencies into consistent environments so it works reliably across machines.
- **Docker Compose** — Runs multiple services such as FastAPI, PostgreSQL, and Qdrant together during development and deployment.

## Documentation

- **Markdown** — Used to maintain the problem definition, architecture, feature specifications, experiments, evaluation reports, and README.
- **OpenAPI / Swagger** — Automatically documents and allows testing of the FastAPI REST APIs through `/docs`.