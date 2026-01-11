"""
LLM Service - GPT-5 via GitHub Models API
Falls back to template-based responses if API unavailable
"""

import logging
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """GPT-5 powered plant response generator via GitHub Models API"""

    def __init__(self):
        self.client = None
        self.model = settings.GITHUB_MODELS_MODEL
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client for GitHub Models API"""
        if settings.GITHUB_TOKEN:
            try:
                self.client = AsyncOpenAI(
                    base_url=settings.GITHUB_MODELS_BASE_URL,
                    api_key=settings.GITHUB_TOKEN,
                )
                logger.info(
                    f"✅ GPT-5 via GitHub Models initialized (model: {self.model})"
                )
            except Exception as e:
                logger.error(f"❌ Failed to initialize GitHub Models client: {e}")
                self.client = None
        else:
            logger.warning("⚠️ GITHUB_TOKEN not set - using template-based responses")

    async def generate_response(
        self, prompt: str, context: Optional[str] = None
    ) -> str:
        """Generate response using GPT-5 or fallback to template"""
        if self.client:
            try:
                return await self._generate_gpt5_response(prompt, context)
            except Exception as e:
                logger.error(f"❌ GPT-5 API error: {e}")
                return self._generate_template_response(prompt, context)
        else:
            return self._generate_template_response(prompt, context)

    async def _generate_gpt5_response(
        self, prompt: str, context: Optional[str] = None
    ) -> str:
        """Generate response using GPT-5 via GitHub Models API"""
        system_prompt = """Sen bir botanik uzmanısın. Kullanıcılara bitki tanımlama ve bilgi sağlama konusunda yardımcı oluyorsun.
Yanıtlarını her zaman Türkçe olarak ver. Bilimsel ve yararlı bilgiler sun.
Emojiler kullanarak yanıtlarını daha okunabilir yap."""

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if context:
            messages.append(
                {
                    "role": "user",
                    "content": f"Bitki bilgileri:\n{context}\n\nKullanıcı sorusu: {prompt}",
                }
            )
        else:
            messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        return response.choices[0].message.content

    def _generate_template_response(
        self, prompt: str, context: Optional[str] = None
    ) -> str:
        """Fallback: Generate formatted plant response from context"""
        if not context:
            return "Bitki analizi yapıldı ancak eşleşen sonuç bulunamadı. Lütfen daha net bir görsel ile tekrar deneyin."

        # Parse context to extract plant info
        response_parts = ["🌿 **Görsel Analizi Tamamlandı!**\n"]

        # Add context directly - it's already formatted
        response_parts.append("**Bulunan Bitkiler:**")
        response_parts.append(context)
        response_parts.append("")

        # Add helpful info based on query type
        query_lower = prompt.lower()

        if any(word in query_lower for word in ["bakım", "sulama", "yetiştir", "care"]):
            response_parts.append("**💡 Bakım Önerileri:**")
            response_parts.append("- Bitkinin türüne göre sulama ihtiyacı değişir")
            response_parts.append("- Dolaylı güneş ışığı çoğu bitki için idealdir")
            response_parts.append("- Toprağın üst kısmı kuruduğunda sulayın")

        elif any(
            word in query_lower for word in ["zehir", "tehlike", "toxic", "poison"]
        ):
            response_parts.append("**⚠️ Uyarı:**")
            response_parts.append(
                "- Bazı bitkiler evcil hayvanlar için zararlı olabilir"
            )
            response_parts.append("- Detaylı bilgi için uzman görüşü alın")

        else:
            response_parts.append("**📝 Not:**")
            response_parts.append(
                "- Yukarıdaki bilgiler Kaggle PlantCLEF, PlantNet ve USDA veritabanlarından alınmıştır"
            )
            response_parts.append("- Kesin tanımlama için uzman görüşü önerilir")

        return "\n".join(response_parts)

    async def generate_rag_response(
        self, query: str, context: str, plants: list = None
    ) -> str:
        """RAG response with plant context"""
        return await self.generate_response(query, context)


# Global instance
grok_service = LLMService()
