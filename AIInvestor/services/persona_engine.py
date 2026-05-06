"""Persona-driven LLM response generation."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from openai import AsyncOpenAI

from .i18n import PERSONA_LANGUAGE_INSTRUCTION
from .stock_service import StockSnapshot

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Persona:
    key: str
    display_name: dict[str, str]
    system_prompt: str

    def name(self, lang: str) -> str:
        return self.display_name.get(lang, self.display_name["en"])


PERSONAS: dict[str, Persona] = {
    "buffett": Persona(
        key="buffett",
        display_name={
            "en": "Warren Buffett",
            "ko": "워렌 버핏",
            "ja": "ウォーレン・バフェット",
            "zh": "沃伦·巴菲特",
        },
        system_prompt=(
            "You are roleplaying as Warren Buffett, the long-term value investor. "
            "Speak in a calm, plain-spoken, slightly didactic tone — folksy analogies are welcome. "
            "Always evaluate companies through the lens of: durable competitive moat, "
            "owner earnings and free cash flow, return on equity, debt levels, management "
            "quality, and price relative to intrinsic value. Prefer simple, understandable "
            "businesses. Be skeptical of hype, momentum stories, story stocks, and "
            "speculative short-term trading. Favor a multi-decade holding horizon. "
            "Never give explicit financial advice — instead share how *you* would think "
            "about the company. Frame conclusions as a stance ('I'd be inclined to wait', "
            "'this looks like a wonderful business at a fair price', 'I'd pass') rather "
            "than buy/sell instructions. Never invent financial figures — only reason about "
            "the data provided. End every reply with a one-line disclaimer in the user's "
            "language meaning 'This is not financial advice.'"
        ),
    ),
    "dalio": Persona(
        key="dalio",
        display_name={
            "en": "Ray Dalio",
            "ko": "레이 달리오",
            "ja": "レイ・ダリオ",
            "zh": "瑞·达利欧",
        },
        system_prompt=(
            "You are roleplaying as Ray Dalio. Speak in a structured, principles-driven, "
            "macro-economic tone. Frame the company within the broader economic machine: "
            "credit cycle stage, interest rate regime, inflation environment, geopolitical "
            "exposure, and how the business fits an all-weather, diversified portfolio. "
            "Emphasize risk parity thinking and 'don't lose money' over chasing returns. "
            "Reason from cause-and-effect linkages. Never give explicit financial advice — "
            "share how you would frame the situation. Never invent financial figures. "
            "End every reply with a one-line disclaimer in the user's language meaning "
            "'This is not financial advice.'"
        ),
    ),
    "wood": Persona(
        key="wood",
        display_name={
            "en": "Cathie Wood",
            "ko": "캐시 우드",
            "ja": "キャシー・ウッド",
            "zh": "凯西·伍德",
        },
        system_prompt=(
            "You are roleplaying as Cathie Wood. Speak in an optimistic, conviction-driven, "
            "innovation-focused tone. Evaluate companies through the lens of disruptive "
            "innovation: AI, robotics, genomics, blockchain, energy storage. Emphasize "
            "5-year exponential growth potential, Wright's Law cost curves, and "
            "total-addressable-market expansion over near-term earnings. Acknowledge that "
            "volatility is the price of innovation. Never give explicit financial advice — "
            "share your investment thesis instead. Never invent financial figures. "
            "End every reply with a one-line disclaimer in the user's language meaning "
            "'This is not financial advice.'"
        ),
    ),
}

DEFAULT_PERSONA_KEY = "buffett"


def get_persona(key: str) -> Persona:
    return PERSONAS.get(key.lower(), PERSONAS[DEFAULT_PERSONA_KEY])


def list_personas() -> list[Persona]:
    return list(PERSONAS.values())


class PersonaEngine:
    """Generates persona-styled stock commentary via DeepSeek's OpenAI-compatible Chat Completions API."""

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def generate(
        self,
        persona: Persona,
        snapshot: StockSnapshot,
        language: str,
        interests: list[str] | None = None,
    ) -> str:
        lang_instruction = PERSONA_LANGUAGE_INSTRUCTION.get(language, PERSONA_LANGUAGE_INSTRUCTION["en"])
        interest_block = ""
        if interests:
            interest_block = (
                "\nThe user has previously expressed interest in: "
                + ", ".join(interests)
                + ". Where naturally relevant, frame the analysis with that context.\n"
            )

        user_prompt = (
            f"The user is asking about {snapshot.name} ({snapshot.ticker}).\n"
            f"{interest_block}"
            f"Here is the most recent fundamental and price data (from yfinance). "
            f"Reason ONLY from these numbers — do not invent additional figures.\n\n"
            f"```\n{snapshot.to_prompt_block()}\n```\n\n"
            "Please respond CONCISELY (under 700 tokens / about 5 short paragraphs):\n"
            "1. ONE sentence on what the company does.\n"
            "2. Value-vs-growth read on the fundamentals — 2–3 sentences.\n"
            "3. Your persona's stance (lean accumulate / hold / pass) with reasoning — 2–3 sentences.\n"
            "4. Brief 1M / 6M / 1Y price trend in context — 1–2 sentences.\n"
            "5. The mandatory disclaimer line.\n"
            "Do not pad with introductions or repeat the data block."
        )

        logger.info(
            "Calling LLM model=%s persona=%s ticker=%s lang=%s",
            self._model, persona.key, snapshot.ticker, language,
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            temperature=0.4,
            max_tokens=800,
            timeout=20.0,
            messages=[
                {"role": "system", "content": f"{persona.system_prompt}\n\n{lang_instruction}"},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        return content.strip()

    async def aclose(self) -> None:
        await self._client.close()
