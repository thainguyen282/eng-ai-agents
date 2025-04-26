from build_database import get_embedding
from pinecone import Pinecone
from openai import OpenAI
import re

def write_pddl_files(domain_text, problem_text, domain_filename="domain.pddl", problem_filename="problem.pddl"):
    with open(domain_filename, "w") as domain_file:
        domain_file.write(domain_text)
    print(f"✅ Domain written to {domain_filename}")

    with open(problem_filename, "w") as problem_file:
        problem_file.write(problem_text)
    print(f"✅ Problem written to {problem_filename}")

def similarity_search(query_text, top_k=3, score_threshold=0.5):
    # Step 1: Embed the query
    query_embedding = get_embedding(query_text)
    if not query_embedding:
        print("Failed to get embedding for query.")
        return []

    # Step 2: Query the Pinecone index
    search_response = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    filtered_matches = [
        match for match in search_response["matches"]
        if match["score"] > score_threshold
    ]

    # Step 3: Display results
    # print("Similarity Search Results:")
    # for match in filtered_matches:
    #     print(f"- ID: {match['id']}, Score: {match['score']}")
    #     print(f"  Metadata: {match['metadata']}")
    return filtered_matches

def clean_and_format_context(raw_text: str) -> str:
    """
    Cleans, deduplicates, and structures the raw concatenated context text.
    """
    # Step 1: Split into chunks based on bullet points, newlines, etc.
    chunks = re.split(r'\n\s*[-*]\s*|\n{2,}', raw_text)

    # Step 2: Trim and filter empty chunks
    cleaned_chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

    # Step 3: Deduplicate
    seen = set()
    unique_chunks = []
    for chunk in cleaned_chunks:
        if chunk not in seen:
            unique_chunks.append(chunk)
            seen.add(chunk)

    # Step 4: Reformat into clean bullets
    formatted_text = "\n".join(f"- {chunk}" for chunk in unique_chunks)

    return formatted_text

def split_pddl_and_write_files(mixed_pddl_text: str):
    domain_parts = []
    problem_parts = []

    lines = mixed_pddl_text.strip().splitlines()
    for line in lines:
        line = line.strip()

        # Classify which parts belong to domain or problem
        if line.startswith("(:types") or line.startswith("(:predicates") or line.startswith("(:action"):
            domain_parts.append(line)
        elif line.startswith("(:objects") or line.startswith("(:init") or line.startswith("(:goal"):
            problem_parts.append(line)
        else:
            # If it's a continuation line, add to last item
            if domain_parts and (domain_parts[-1].count("(") > domain_parts[-1].count(")")):
                domain_parts[-1] += " " + line
            elif problem_parts and (problem_parts[-1].count("(") > problem_parts[-1].count(")")):
                problem_parts[-1] += " " + line

    # Assemble domain and problem text
    domain_text = f"""(define (domain openrouter-domain)
{chr(10).join(domain_parts)}
)"""

    problem_text = f"""(define (problem openrouter-problem)
(:domain openrouter-domain)
{chr(10).join(problem_parts)}
)"""

    # Write to files
    with open("./assignment/assignment-4/domain.pddl", "w") as f:
        f.write(domain_text)

    with open("problem.pddl", "w") as f:
        f.write(problem_text)

    print("Generated domain.pddl and problem.pddl successfully!")

# Optional: test run
if __name__ == "__main__":
    query = """Detailed explanation of how OpenRouter selects and routes requests to model providers based on fallback logic, cost-effectiveness, and availability. Include how the /v1/chat/completions endpoint supports this behavior and what parameters are involved."""
    PINECONE_API_KEY = "pcsk_srS9t_9xDJm8hoZJz4RhM9SE6UnfYPAuurasVDWtW5zyt7uBHusZ3wF9YsRdABHQAT1Yo"
    PINECONE_ENV = "us-east-1"
    INDEX_NAME = "pddl-retry"

    # Initialize Pinecone client
    pc = Pinecone(api_key=PINECONE_API_KEY)
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

    matches = similarity_search(query, top_k=50)
    context = "\n".join(match["metadata"].get("text", "") for match in matches)

    cleaned_context = clean_and_format_context(context)
    # print("=== CLEANED CONTEXT ===")
    # print(cleaned_context)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="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"
    )

    completion = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": f"""
                    You are an expert technical documentation editor.

                    You are given a set of messy, overlapping, and out-of-order documentation snippets.

                    Your tasks:
                    - Carefully **analyze and reorganize** the information into a logical structure
                    - **Group** related pieces of information under appropriate **section headers**
                    - **Merge** overlapping or redundant snippets intelligently
                    - **Fix** incomplete or fragmented sentences if possible
                    - Ensure the final document is **clear, readable, and technically accurate**
                    - **DO NOT invent** any new information. Only reorganize what is provided.

                    Here is the context to organize:
                    \"\"\"
                    {cleaned_context}
                    \"\"\"

                    Return the organized documentation clearly with section headings like:

                    ## Section Title
                    (Content)

                    ## Section Title
                    (Content)
                    """
            }
        ],
        temperature=0.2
    )

    organized_context = completion.choices[0].message.content
    # print(organized_context)


    completion = client.chat.completions.create(
        model="openai/gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": f"""
                You are an expert in PDDL planning. Based on the context provided below, generate a **complete, solvable PDDL domain and problem**. The problem must be fixable by the domain — i.e., all actions, predicates, objects, and goals must be coherent and lead to a plan.
                ### Step 1: Context
                You are given a real-world planning context. Extract all relevant **types**, then build predicates, actions, and finally generate both the **PDDL domain** and **PDDL problem** file.
                ### Context:
                {organized_context}
                ### Requirements:
                1. **Types**
                Extract types from the context and represent them as:
                ```lisp
                (:types
                    type1
                    type2
                    ...
                )
                Predicates
                Based on the types and context, write meaningful predicates:
                (:predicates
                    (predicate1 ?x - type1 ?y - type2)
                    ...
                )
                Actions
                Define how objects interact with the world using PDDL actions. Format each action like this
                (:action action-name
                    :parameters (?x - type1 ?y - type2)
                    :precondition (and (...))
                    :effect (and (...))
                )
                Objects
                Create realistic and solvable objects based on types and predicates:
                (:objects
                    obj1 - type1
                    obj2 - type2
                    ...
                )
                Initial State
                Define the starting facts of the world using predicates:
                (:init
                    (fact1 ...)
                    (fact2 ...)
                )
                Goal
                Define the goal the planner should achieve. The goal must be achievable with the actions and objects:
                (:goal
                    (and
                        (condition1 ...)
                        (condition2 ...)
                    )
                )
                Output Format:
                Domain File:
                Wrap the types, predicates, and actions into a domain definition:
                (define (domain my-domain)
                    (:requirements :strips :typing)
                    (:types
                        ...
                    )
                    (:predicates
                        ...
                    )
                    (:action action-name
                        ...
                    )
                    ...
                )
                Problem File:
                Use objects, init, and goal to create the problem definition:
                (define (problem my-problem)
                    (:domain my-domain)
                    (:objects
                        ...
                    )
                    (:init
                        ...
                    )
                    (:goal
                        (and
                            ...
                        )
                    )
                )
                Rules:
                The goal must be achievable based on the domain.

                Add any additional predicates or types if necessary.

                Use valid PDDL syntax only.

                DO NOT include any explanation or text. Output code only.
                """
            }
        ]
    )

    print(f"this is pddl: {completion.choices[0].message.content}")
    mixed_pddl = completion.choices[0].message.content
    split_pddl_and_write_files(mixed_pddl)
