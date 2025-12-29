import discord
import os
import sys
from groq import Groq
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# --- FORCE LOGGING ---
sys.stdout.reconfigure(line_buffering=True)

# --- CONFIGURATION ---
DATA_FOLDER = "knowledge"  # Name of your folder
MODEL_NAME = "llama3-70b-8192"

print("--- BOT STARTING UP ---")

# --- 1. SETUP KNOWLEDGE BASE (FOLDER EDITION) ---
documents = []

if os.path.exists(DATA_FOLDER):
    print(f"Scanning folder: {DATA_FOLDER}...")
    # Loop through every file in the folder
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
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        
        # Create the Brain
        print(f"Indexing {len(chunks)} knowledge chunks...")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = FAISS.from_documents(chunks, embeddings)
        print("SUCCESS: Knowledge Index Created!")
    else:
        print("WARNING: No .txt files found in the folder!")
        vector_store = None
else:
    print(f"WARNING: Folder '{DATA_FOLDER}' not found.")
    vector_store = None

# --- 2. SETUP CLIENTS ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

groq_key = os.environ.get("GROQ_API_KEY")
if not groq_key:
    print("CRITICAL ERROR: GROQ_API_KEY is missing from Zeabur Variables!")

groq_client = Groq(api_key=groq_key)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.user in message.mentions:
        print(f"Msg from {message.author}: {message.content}") 
        user_question = message.content.replace(f'<@{client.user.id}>', '').strip()
        
        try:
            async with message.channel.typing():
                # A. SEARCH
                context_text = ""
                if vector_store:
                    # Retrieve top 4 relevant chunks (More info for better answers)
                    results = vector_store.similarity_search(user_question, k=4)
                    for res in results:
                        context_text += res.page_content + "\n\n"
                    print("Context found.")
                
                # B. THINK
                system_prompt = f"""You are an expert Reselling Assistant. 
                Use the following retrieved context to answer the user's question.
                
                CONTEXT FROM DATABASE:
                {context_text}
                
                INSTRUCTIONS:
                1. Answer STRICTLY based on the Context.
                2. If the answer is not in the Context, say "I don't have that info."
                3. Keep it professional.
                """

                completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_question}
                    ],
                    model=MODEL_NAME, 
                )
                
                response = completion.choices[0].message.content
                
                # C. REPLY
                if len(response) > 2000:
                    for i in range(0, len(response), 2000):
                        await message.channel.send(response[i:i+2000])
                else:
                    await message.channel.send(response)
                    
        except Exception as e:
            print(f"ERROR: {e}")
            await message.channel.send(f"System Error: {e}")

client.run(os.environ.get("DISCORD_TOKEN"))
