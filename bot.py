import discord
import os
import sys
from groq import Groq
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# --- FORCE LOGGING (Fixes "Invisible Logs") ---
sys.stdout.reconfigure(line_buffering=True)

# --- CONFIGURATION ---
DATA_FILE = "knowledge.txt"
MODEL_NAME = "llama3-70b-8192"

print("--- BOT STARTING UP ---")

# --- 1. SETUP KNOWLEDGE BASE ---
if os.path.exists(DATA_FILE):
    print(f"Found {DATA_FILE}. Indexing data... (This may take a moment)")
    try:
        loader = TextLoader(DATA_FILE, encoding="utf-8")
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        
        # Create the Brain
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = FAISS.from_documents(chunks, embeddings)
        print("SUCCESS: Knowledge Index Created!")
    except Exception as e:
        print(f"CRITICAL ERROR loading knowledge: {e}")
        vector_store = None
else:
    print(f"WARNING: {DATA_FILE} not found. Bot will strictly hallucinate.")
    vector_store = None

# --- 2. SETUP CLIENTS ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Check for Key immediately
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
        print(f"Received message from {message.author}: {message.content}") # Log the message
        user_question = message.content.replace(f'<@{client.user.id}>', '').strip()
        
        try:
            async with message.channel.typing():
                # A. SEARCH
                context_text = ""
                if vector_store:
                    results = vector_store.similarity_search(user_question, k=3)
                    for res in results:
                        context_text += res.page_content + "\n\n"
                    print(f"Found context: {context_text[:100]}...") # Log what it found
                
                # B. THINK
                system_prompt = f"""You are an expert Reselling Assistant. 
                Use the following retrieved context to answer the user's question.
                
                CONTEXT:
                {context_text}
                
                INSTRUCTIONS:
                1. Answer STRICTLY based on the Context.
                2. If the answer is not in the Context, say "I don't have that info."
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
                print("Reply sent successfully.")
                    
        except Exception as e:
            print(f"ERROR processing message: {e}") # This will now show in logs
            await message.channel.send(f"System Error: {e}")

client.run(os.environ.get("DISCORD_TOKEN"))
