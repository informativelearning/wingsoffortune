import discord
import os
import sys
from groq import Groq
from langchain_community.document_loaders import TextLoader
# This matches your requirement:
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS

# --- FORCE LOGGING ---
sys.stdout.reconfigure(line_buffering=True)

# --- CONFIGURATION ---
DATA_FOLDER = "knowledge"
MODEL_NAME = "llama-3.3-70b-versatile"

print("--- BOT STARTING UP (FastEmbed + Strict Mode) ---")

# --- 1. SETUP KNOWLEDGE BASE ---
vector_store = None

try:
    if os.path.exists(DATA_FOLDER):
        print(f"Scanning folder: {DATA_FOLDER}...")
        documents = []
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
            # Using the Diet Model (20MB) to prevent Storage Crashes
            embeddings = FastEmbedEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = FAISS.from_documents(chunks, embeddings)
            print("SUCCESS: Knowledge Index Created!")
        else:
            print("WARNING: No .txt files found in knowledge folder!")
    else:
        print(f"WARNING: Folder '{DATA_FOLDER}' not found.")

except Exception as e:
    print(f"CRITICAL ERROR during knowledge base setup: {e}")
    # We continue anyway so the bot stays online, even if the brain is empty
    vector_store = None

# --- 2. SETUP CLIENTS ---
print("Setting up Discord...")
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

print("Setting up Groq...")
groq_key = os.environ.get("GROQ_API_KEY")
if not groq_key:
    print("CRITICAL: GROQ_API_KEY not found!")
groq_client = Groq(api_key=groq_key)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print("Bot is ready to serve.")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user in message.mentions:
        print(f"Query from {message.author}: {message.content}") 
        user_question = message.content.replace(f'<@{client.user.id}>', '').strip()
        
        try:
            async with message.channel.typing():
                # A. SEARCH
                context_text = ""
                if vector_store:
                    try:
                        results = vector_store.similarity_search(user_question, k=4)
                        for res in results:
                            context_text += res.page_content + "\n\n"
                    except Exception as search_err:
                        print(f"Search Error: {search_err}")
                
                # B. THINK (THE "STRICT PARTNER" MODE)
                system_prompt = f"""You are a senior Reselling and Liquidation Strategist.
                
                CONTEXT FROM DATABASE:
                {context_text}
                
                INSTRUCTIONS:
                1. MENTALITY: You are focused entirely on value, risk, and logistics. You do not chat; you analyze.
                2. CONNECTION: Attempt to relate EVERY user input to reselling, sourcing, or operations.
                   - If the user asks something vague, assume it relates to inventory and ask for the specific data points needed to assess it.
                3. MISSING DATA: If the Context Database doesn't have the answer, do not simply say "I don't know." State what specific variable is missing from the user's input that prevents a calculation.
                4. TONE: Minimal, literal, direct. No filler.
                """

                completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_question}
                    ],
                    model=MODEL_NAME, 
                    temperature=0.3, 
                )
                
                response = completion.choices[0].message.content
                
                # C. REPLY
                if len(response) > 2000:
                    for i in range(0, len(response), 2000):
                        await message.channel.send(response[i:i+2000])
                else:
                    await message.channel.send(response)
                    
        except Exception as e:
            print(f"Operational Error: {e}")
            await message.channel.send(f"Operational Error: {e}")

# --- 3. RUN ---
print("Attempting to connect to Discord Gateway...")
client.run(os.environ.get("DISCORD_TOKEN"))
