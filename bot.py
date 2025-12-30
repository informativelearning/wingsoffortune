import discord
import os
import sys
from groq import Groq
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# CHANGE: Using FastEmbed instead of HuggingFace (Prevents Crashing)
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS

# --- FORCE LOGGING ---
sys.stdout.reconfigure(line_buffering=True)

# --- CONFIGURATION ---
DATA_FOLDER = "knowledge"
MODEL_NAME = "llama-3.3-70b-versatile"

print("--- BOT STARTING UP (FastEmbed Edition) ---")

# --- 1. SETUP KNOWLEDGE BASE ---
documents = []
vector_store = None

try:
    if os.path.exists(DATA_FOLDER):
        print(f"Scanning folder: {DATA_FOLDER}...")
        for filename in os.listdir(DATA_FOLDER):
            if filename.endswith(".txt"):
                file_path = os.path.join(DATA_FOLDER, filename)
                try:
                    print(f"Loading: {filename}")
                    loader = TextLoader(file_path, encoding="utf-8")
                    documents.extend(loader.load())
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")

        if documents:
            print(f"Indexing {len(documents)} documents...")
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            chunks = text_splitter.split_documents(documents)
            
            print(f"Creating embeddings for {len(chunks)} chunks...")
            embeddings = FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = FAISS.from_documents(chunks, embeddings)
            print("SUCCESS: Knowledge Index Created!")
        else:
            print("WARNING: No .txt files found in knowledge folder!")
    else:
        print(f"WARNING: Folder '{DATA_FOLDER}' not found.")
except Exception as e:
    print(f"CRITICAL ERROR during knowledge base setup: {e}")
    import traceback
    traceback.print_exc()
    vector_store = None

# --- 2. SETUP CLIENTS ---
print("Setting up Discord intents...")
intents = discord.Intents.default()
intents.message_content = True

print("Creating Discord client...")
client = discord.Client(intents=intents)

print(f"Initializing Groq client with API key: {os.environ.get('GROQ_API_KEY')[:10] if os.environ.get('GROQ_API_KEY') else 'NOT SET'}...")
try:
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    print("Groq client initialized successfully!")
except Exception as e:
    print(f"ERROR initializing Groq client: {e}")
    import traceback
    traceback.print_exc()
