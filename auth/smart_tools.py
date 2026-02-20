"""Sistema de herramientas inteligente que usa el LLM para decidir cuándo buscar."""
import httpx
import json
import logging
from typing import Optional, Tuple
from .auto_tools import get_current_datetime, web_search

logger = logging.getLogger("auth")

VLLM_BASE = "http://127.0.0.1:8000"
API_KEY = "token-llm-chat-secret-2025"

async def ask_llm_if_needs_tools(user_message: str) -> Optional[Tuple[str, str]]:
    """Pregunta al LLM si necesita usar herramientas."""
    
    classification_prompt = f"""Analiza esta pregunta y determina si necesitas información externa.

Pregunta: "{user_message}"

OPCIONES:
1. DATE - Si necesitas la fecha/hora actual
2. WEB - Si necesitas buscar información actualizada en internet
3. NONE - Si puedes responder con tu conocimiento interno

Responde SOLO con: DATE, WEB, o NONE.
Si eliges WEB, agrega dos puntos y la consulta: "WEB: consulta aquí"

Tu respuesta:"""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{VLLM_BASE}/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "model": "Qwen/Qwen2-VL-7B-Instruct",
                    "messages": [{"role": "user", "content": classification_prompt}],
                    "max_tokens": 100,
                    "temperature": 0.1,
                }
            )
        
        if response.status_code != 200:
            return None
        
        result = response.json()
        llm_answer = result["choices"][0]["message"]["content"].strip().upper()
        
        logger.info(f"Clasificación LLM: {llm_answer}")
        
        if llm_answer.startswith("DATE"):
            return ("date", "")
        elif llm_answer.startswith("WEB"):
            query = user_message
            if ":" in llm_answer:
                extracted_query = llm_answer.split(":", 1)[1].strip()
                if extracted_query and len(extracted_query) > 3:
                    query = extracted_query
            return ("web", query)
        else:
            return None
    except Exception as e:
        logger.error(f"Error en clasificación: {e}")
        return None

async def detect_and_execute_smart_tools(user_message: str) -> Optional[Tuple[str, str]]:
    """Usa el LLM para decidir si necesita herramientas."""
    decision = await ask_llm_if_needs_tools(user_message)
    
    if not decision:
        return None
    
    tool_type, query = decision
    
    if tool_type == "date":
        result = get_current_datetime()
        return ("get_current_datetime", result)
    elif tool_type == "web":
        result = web_search(query if query else user_message)
        return ("web_search", result)
    
    return None

def augment_message_with_tool_result(messages: list, tool_name: str, tool_result: str) -> list:
    """Agrega el resultado de una herramienta al contexto."""
    augmented = messages.copy()
    
    if augmented and augmented[-1].get("role") == "user":
        original_content = augmented[-1].get("content", "")
        if isinstance(original_content, list):
            for item in original_content:
                if item.get("type") == "text":
                    original_content = item.get("text", "")
                    break
        
        augmented[-1]["content"] = f"""{original_content}

INFORMACIÓN ACTUALIZADA (obtenida justo ahora):
{tool_result}

INSTRUCCIONES: Responde basándote ÚNICAMENTE en la información actualizada proporcionada arriba."""
    
    return augmented
