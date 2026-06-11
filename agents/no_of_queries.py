from ollama import chat
from pydantic import BaseModel
from agents.models import slm_model

system_prompt = """You are a query resolution agent for a RAG (Retrieval Augmented Generation) system.

Your job is to analyze the user's latest message IN THE CONTEXT of the conversation history, and produce a list of fully self-contained, explicit search queries that can be sent to a vector database — WITHOUT any pronouns, references like "them", "it", "those", "that", "these", or vague terms that depend on prior context.

Rules:
1. ALWAYS resolve all pronouns and references using the conversation history.
   - If user says "tell me more about them" and prior context mentions "Indian laws", output: "Indian laws detailed explanation"
   - If user says "what is its capital?" and prior context mentions "France", output: "capital of France"
2. If the current message is a follow-up, enrich the query with topic keywords from the previous assistant response.
3. Split compound questions into separate focused queries.
4. Each query must be fully standalone — someone reading only the query list must understand exactly what to search for.
5. Be specific: prefer "fundamental rights in Indian Constitution Article 12-35" over "Indian laws".
6. Output ONLY the queries list. No explanation."""

class user_queries(BaseModel):
    queries: list[str]

def parse_queries(query: str, chat_context: str) -> list[str]:
    """Parse and resolve user queries using full conversation context."""

    # Build structured messages so the model sees conversation as chat history
    messages = [{"role": "system", "content": system_prompt}]

    # Add prior conversation turns as actual chat messages (not just a flat string)
    if chat_context and chat_context.strip():
        for line in chat_context.strip().splitlines():
            if line.startswith("user:"):
                messages.append({"role": "user", "content": line[5:].strip()})
            elif line.startswith("assistant:"):
                messages.append({"role": "assistant", "content": line[10:].strip()})

    # Final instruction with the new user message
    messages.append({
        "role": "user",
        "content": (
            f"New user message: \"{query}\"\n\n"
            "Resolve all references using the conversation above. "
            "Output a list of fully explicit, self-contained search queries."
        )
    })

    response = chat(
        messages=messages,
        model=slm_model,
        format=user_queries.model_json_schema()
    )
    list_queries = user_queries.model_validate_json(response['message']['content']).queries

    # Fallback: if model returns empty or fails, use original query
    if not list_queries:
        list_queries = [query]

    print("[QueryParser]", list_queries)
    return list_queries