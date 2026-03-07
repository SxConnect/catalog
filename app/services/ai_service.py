from groq import Groq
import json
from typing import Dict, Optional
from app.services.api_key_manager import ApiKeyManager

class AIService:
    def __init__(self):
        self.key_manager = ApiKeyManager()
    
    def structure_product_data(self, raw_text: str) -> Optional[Dict]:
        api_key = self.key_manager.get_next_key()
        if not api_key:
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
            response = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
        except Exception as e:
            print(f"AI Error: {e}")
            return None
