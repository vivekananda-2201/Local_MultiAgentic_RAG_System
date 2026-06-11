import ollama
import colorama
from colorama import init
from agents.models import slm_model

def rag_query_agent(query: str, context):
    system_prompt = "You are an AI agent that generate rag search query to search in rag. generate the best possible query to search in rag."
    response = ollama.chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}"}
        ],
        model=slm_model
    )
    answer = response['message']['content']
    # Instead of printing, just return (printing can be done by caller if needed)
    print(colorama.Fore.LIGHTMAGENTA_EX + "\n[RAG Query Agent] Generated RAG Search Query:" + colorama.Style.RESET_ALL + f" {answer}\n")
    return answer
