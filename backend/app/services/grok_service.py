"""
LLM Service - Multi-Provider with Automatic Fallback Chain
Priority: GPT-5 (GitHub) → Google AI Studio (Gemini) → OpenRouter → Template
"""

import logging
from typing import Optional, List, Tuple
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Multi-provider LLM service with automatic fallback chain"""

    def __init__(self):
        self.providers: List[Tuple[str, Optional[AsyncOpenAI], str]] = []
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all available LLM providers in priority order"""
        self.providers = []

        # 1. GPT-5 via GitHub Models (Primary)
        if settings.GITHUB_TOKEN:
            try:
                client = AsyncOpenAI(
                    base_url=settings.GITHUB_MODELS_BASE_URL,
                    api_key=settings.GITHUB_TOKEN,
                )
                self.providers.append(
                    ("GPT-5 (GitHub)", client, settings.GITHUB_MODELS_MODEL)
                )
                logger.info(
                    f"✅ Provider 1: GPT-5 via GitHub Models ({settings.GITHUB_MODELS_MODEL})"
                )
            except Exception as e:
                logger.warning(f"⚠️ GPT-5 init failed: {e}")

        # 2. Google AI Studio (Gemini) - First Fallback
        if settings.GOOGLE_AI_STUDIO_API_KEY:
            try:
                client = AsyncOpenAI(
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    api_key=settings.GOOGLE_AI_STUDIO_API_KEY,
                )
                self.providers.append(
                    ("Google AI (Gemini)", client, settings.GOOGLE_AI_STUDIO_MODEL)
                )
                logger.info(
                    f"✅ Provider 2: Google AI Studio ({settings.GOOGLE_AI_STUDIO_MODEL})"
                )
            except Exception as e:
                logger.warning(f"⚠️ Google AI init failed: {e}")

        # 3. OpenRouter - Second Fallback
        if settings.OPENROUTER_API_KEY:
            try:
                client = AsyncOpenAI(
                    base_url=settings.OPENROUTER_BASE_URL,
                    api_key=settings.OPENROUTER_API_KEY,
                )
                self.providers.append(("OpenRouter", client, settings.OPENROUTER_MODEL))
                logger.info(f"✅ Provider 3: OpenRouter ({settings.OPENROUTER_MODEL})")
            except Exception as e:
                logger.warning(f"⚠️ OpenRouter init failed: {e}")

        if not self.providers:
            logger.warning(
                "⚠️ No LLM providers configured - using template-based responses only"
            )
        else:
            logger.info(
                f"🔗 LLM Fallback chain: {' → '.join([p[0] for p in self.providers])} → Template"
            )

    async def generate_response(
        self, prompt: str, context: Optional[str] = None
    ) -> str:
        """Generate response with automatic fallback through provider chain"""

        # Try each provider in order
        for provider_name, client, model in self.providers:
            try:
                logger.info(f"🔄 Trying {provider_name}...")
                response = await self._call_provider(client, model, prompt, context)
                logger.info(f"✅ {provider_name} succeeded")
                return response
            except Exception as e:
                logger.warning(f"⚠️ {provider_name} failed: {e}")
                continue

        # All providers failed - use template
        logger.info("📝 All LLM providers failed - using template response")
        return self._generate_template_response(prompt, context)

    async def _call_provider(
        self,
        client: AsyncOpenAI,
        model: str,
        prompt: str,
        context: Optional[str] = None,
    ) -> str:
        """Call a specific LLM provider"""
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

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            timeout=settings.LLM_API_TIMEOUT,
        )

        return response.choices[0].message.content

    def _generate_template_response(
        self, prompt: str, context: Optional[str] = None
    ) -> str:
        """Last resort: Generate formatted plant response from context"""
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
