from pinecone import Pinecone
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

PINECONE_API_KEY = "pcsk_srS9t_9xDJm8hoZJz4RhM9SE6UnfYPAuurasVDWtW5zyt7uBHusZ3wF9YsRdABHQAT1Yo"
PINECONE_ENV = "us-east-1"
INDEX_NAME = "pddl-retry"

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)


def get_embedding(text):
    embeddings = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=[text],
        parameters={"input_type": "passage", "truncate": "END"}
    )
    # print("Full embeddings response:", embeddings)
    if hasattr(embeddings, 'data') and embeddings.data:
        return embeddings.data[0].get('values', [])
    else:
        print("Error: Invalid embedding response.")
        return []

# Create index if not exists
try:
    index = pc.Index(INDEX_NAME)
    print(f"Using existing index {INDEX_NAME}")
except Exception as e:
    print(f"Creating new index {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=1024,
        metric="cosine",
        spec={"serverless": {"cloud": "aws", "region": PINECONE_ENV}}
    )
    index = pc.Index(INDEX_NAME)


urls = [
    "https://openrouter.ai/docs/api-reference/overview.md",
    "https://openrouter.ai/docs/api-reference/streaming.md",
    "https://openrouter.ai/docs/api-reference/authentication.md",
    "https://openrouter.ai/docs/api-reference/parameters.md",
    "https://openrouter.ai/docs/api-reference/limits.md",
    "https://openrouter.ai/docs/api-reference/errors.md",
    "https://openrouter.ai/docs/api-reference/completion.md",
    "https://openrouter.ai/docs/api-reference/chat-completion.md",
    "https://openrouter.ai/docs/api-reference/get-a-generation.md",
    "https://openrouter.ai/docs/api-reference/list-available-models.md",
    "https://openrouter.ai/docs/api-reference/list-endpoints-for-a-model.md"
    "https://openrouter.ai/docs/api-reference/get-credits.md",
    "https://openrouter.ai/docs/features/model-routing.md",
    "https://openrouter.ai/docs/features/provider-routing.md",
    "https://openrouter.ai/docs/features/prompt-caching.md",
    "https://openrouter.ai/docs/features/structured-outputs.md"
]

loader = WebBaseLoader(urls)
docs = loader.load()

# Split docs semantically
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = splitter.split_documents(docs)

vectors_to_upsert = []
for i, chunk in enumerate(chunks):
    chunk_id = f"chunk-{i}" 
    embedding = get_embedding(chunk.page_content)  # Corrected this line
    chunk.metadata["text"] = chunk.page_content
    if embedding:
        vectors_to_upsert.append({
            "id": chunk_id,
            "values": embedding,
            "metadata": chunk.metadata  # Corrected metadata reference
        })

if vectors_to_upsert:
    response = index.upsert(vectors=vectors_to_upsert)
    # print(f"Upsert response: {response}")
else:
    print("No vectors to upsert.")
