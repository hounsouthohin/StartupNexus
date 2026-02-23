import logging
import os

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def create_chat_llm(
    *,
    temperature: float = 0.2,
    prefer_openai: bool = False,
    provider_override: str | None = None,
):
    """
    Fabrique un Chat LLM avec fallback provider.
    Priorite en mode auto: Groq -> Gemini -> OpenAI.
    """
    provider = (provider_override or os.getenv("LLM_PROVIDER", "auto") or "auto").strip().lower()

    if provider == "auto" and prefer_openai:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            logger.info(f"[llm_factory] provider=openai model={model}")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=openai_key,
            )

    if provider in ("auto", "groq"):
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
            logger.info(f"[llm_factory] provider=groq model={model}")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
            )
        if provider == "groq":
            raise RuntimeError("LLM_PROVIDER=groq mais GROQ_API_KEY est manquante")

    if provider in ("auto", "gemini"):
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except Exception as e:
                if provider == "gemini":
                    raise RuntimeError(f"Provider Gemini indisponible: {e}") from e
            else:
                model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
                logger.info(f"[llm_factory] provider=gemini model={model}")
                return ChatGoogleGenerativeAI(
                    model=model,
                    temperature=temperature,
                    google_api_key=gemini_key,
                )
        if provider == "gemini":
            raise RuntimeError("LLM_PROVIDER=gemini mais GEMINI_API_KEY est manquante")

    if provider in ("auto", "openai"):
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            logger.info(f"[llm_factory] provider=openai model={model}")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=openai_key,
            )
        raise RuntimeError("OPENAI_API_KEY manquante pour initialiser ChatOpenAI")

    raise RuntimeError(f"LLM_PROVIDER non supporte: {provider}")
