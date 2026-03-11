from groq import Groq
import json
from typing import Dict, Optional
from app.services.api_key_manager import ApiKeyManager
from app.utils.retry import retry_groq_api
from app.monitoring.metrics import record_groq_error, record_product_processed
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.key_manager = ApiKeyManager()
    
    @retry_groq_api(max_attempts=3)
    def structure_product_data(self, raw_text: str) -> Optional[Dict]:
        """
        Estrutura dados de produto usando IA com retry automático e circuit breaker.
        
        Args:
            raw_text: Texto bruto extraído do PDF
            
        Returns:
            Dicionário com dados estruturados do produto ou None se falhar
        """
        api_key = self.key_manager.get_next_key()
        if not api_key:
            logger.error("No API key available for Groq service")
            return None
        
        client = Groq(api_key=api_key)
        
        prompt = f"""
        Analise o texto abaixo e extraia informações de produto pet.
        Retorne APENAS um JSON válido com esta estrutura:
        {{
            "name": "nome do produto",
            "brand": "marca",
            "weight": "peso/tamanho",
            "category": "categoria",
            "description": "descrição",
            "possible_ean": "código EAN se encontrado"
        }}
        
        Texto: {raw_text}
        """
        
        try:
            logger.debug(f"Making Groq API call for text length: {len(raw_text)}")
            response = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            structured_data = json.loads(result)
            
            logger.info(f"Successfully structured product data: {structured_data.get('name', 'Unknown')}")
            return structured_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Groq API: {e}")
            record_groq_error("json_decode_error")
            return None
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            # Registrar tipo de erro específico
            if "rate limit" in str(e).lower():
                record_groq_error("rate_limit")
            elif "timeout" in str(e).lower():
                record_groq_error("timeout")
            else:
                record_groq_error("api_error")
            raise  # Re-raise para que o retry funcione
