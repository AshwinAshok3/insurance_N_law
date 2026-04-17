import os
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from groq import Groq
from dotenv import load_dotenv

# Explicitly load from project root
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path)

# Initialize API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

index_name = "insurance-law"
pc_index = None

# Initialize Pinecone index using a singleton pattern
def get_pinecone_index():
    global pc_index
    if pc_index is not None:
        return pc_index
        
    try:
        if index_name not in pc.list_indexes().names():
            pc.create_index(name=index_name, dimension=384, metric="cosine", spec=ServerlessSpec(cloud="aws", region="us-east-1"))
        pc_index = pc.Index(index_name)
        return pc_index
    except Exception as e:
        print(f"Error initializing pinecone: {e}")
        return None

# Initialize Embedder
embedder = SentenceTransformer('all-MiniLM-L6-v2') 

# Define system prompt
SYSTEM_PROMPT = """
You are a domain assistant that answers questions in two domains:

1) Insurance Policy Guidance (Banks + IRDAI regulations)
2) Legal Reference Assistant (Indian law sections and penalties)

Determine the correct domain from the user query and respond accordingly.

GENERAL BEHAVIOR
- Be respectful, helpful, and slightly humorous without insulting the user.
- Use verified information only.
- Never invent laws, penalties, or policies.
- Provide structured and clear responses.

------------------------------------------------

DOMAIN 1: INSURANCE POLICY GUIDANCE
Goal: Help users find insurance policies offered by banks or answer IRDAI rule queries.
Steps:
1. Understand the user's need.
2. Identify relevant insurance plans or rules.
3. Recommend suitable plans or explain the rule.

Response format:
[If searching for policies]
Recommended Insurance Options
1. Bank Name / Policy Name
   Key Benefits
   Why it fits the user's needs
Estimated Cost: Approx Monthly Cost

[If explaining rules]
Provide the IRDAI rule and what it means clearly.

------------------------------------------------

DOMAIN 2: LEGAL REFERENCE ASSISTANT
Goal: Explain relevant legal sections and penalties.
Steps:
1. Understand the user's legal question.
2. Identify related acts and sections.
3. Present the relevant legal information clearly.

Response format:
### Relevant Legal Sections
- **Act / Section**: Description

### Penalty Information
- Minimum Sentence: X years  
- Maximum Sentence: Y years

### Explanation
Explain why the law applies and how penalties are determined. Tone can be slightly humorous but focus on explaining consequences.

------------------------------------------------
Always format output in Markdown.
"""

def generate_ai_response(user_question: str, domain_namespace: str) -> str:
    """
    Given a question and a domain namespace ('law', 'banks', 'irdai'),
    retrieves context from Pinecone and asks Groq Llama-3 for a response.
    """
    index = get_pinecone_index()
    if index is None:
        return "Internal Error: Could not connect to AI Knowledge Base"
        
    # 1. Embed query
    query_vector = embedder.encode(user_question).tolist()
    
    # 2. Retrieve from Pinecone
    try:
        search_results = index.query(vector=query_vector, top_k=4, include_metadata=True, namespace=domain_namespace)
        matches = search_results.get('matches', [])
    except Exception as e:
        print(f"Error querying pinecone: {e}")
        matches = []
        
    context_blocks = [match['metadata']['text'] for match in matches if 'metadata' in match and 'text' in match['metadata']]
    full_context = "\n\n".join(context_blocks)
    
    user_prompt = f"Context:\n{full_context}\n\nQuestion: {user_question}"
    
    try:
        # 3. Call Groq
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error contacting AI: {str(e)}"
