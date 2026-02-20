"""Funciones de herramientas automáticas."""
from datetime import datetime
import logging

logger = logging.getLogger("auth")

def get_current_datetime() -> str:
    """Obtiene la fecha y hora actual en español."""
    now = datetime.now()
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    
    return f"""Fecha actual: {now.day} de {meses[now.month-1]} de {now.year}
Día: {dias[now.weekday()]}
Hora: {now.strftime('%H:%M:%S')}"""

def web_search(query: str, max_results: int = 5) -> str:
    """Busca en internet usando DuckDuckGo."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return f"No se encontraron resultados para: {query}"
        
        formatted = []
        for i, r in enumerate(results, 1):
            title = r.get('title', 'Sin título')
            body = r.get('body', '')[:300]
            href = r.get('href', '')
            formatted.append(f"{i}. {title}\n   {body}\n   {href}")
        
        return f"=== RESULTADOS WEB ===\n{query}\n\n" + "\n\n".join(formatted)
    except Exception as e:
        logger.error(f"Error web_search: {e}")
        return f"Error al buscar: {str(e)}"
