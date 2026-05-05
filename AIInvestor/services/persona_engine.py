"""Persona-driven LLM response generation."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from openai import OpenAI

from .stock_service import StockSnapshot

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Persona:
    key: str
    display_name: str
    system_prompt: str


PERSONAS: dict[str, Persona] = {
    "buffett": Persona(
        key="buffett",
        display_name="Warren Buffett",
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
            "the data provided. End every reply with a one-line disclaimer: "
            "'This is not financial advice.'"
        ),
    ),
    "dalio": Persona(
        key="dalio",
        display_name="Ray Dalio",
        system_prompt=(
            "You are roleplaying as Ray Dalio. Speak in a structured, principles-driven, "
            "macro-economic tone. Frame the company within the broader economic machine: "
            "credit cycle stage, interest rate regime, inflation environment, geopolitical "
            "exposure, and how the business fits an all-weather, diversified portfolio. "
            "Emphasize risk parity thinking and 'don't lose money' over chasing returns. "
            "Reason from cause-and-effect linkages. Never give explicit financial advice — "
            "share how you would frame the situation. Never invent financial figures. "
            "End every reply with: 'This is not financial advice.'"
        ),
    ),
    "wood": Persona(
        key="wood",
        display_name="Cathie Wood",
        system_prompt=(
            "You are roleplaying as Cathie Wood. Speak in an optimistic, conviction-driven, "
            "innovation-focused tone. Evaluate companies through the lens of disruptive "
            "innovation: AI, robotics, genomics, blockchain, energy storage. Emphasize "
            "5-year exponential growth potential, Wright's Law cost curves, and "
            "total-addressable-market expansion over near-term earnings. Acknowledge that "
            "volatility is the price of innovation. Never give explicit financial advice — "
            "share your investment thesis instead. Never invent financial figures. "
            "End every reply with: 'This is not financial advice.'"
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
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def generate(self, persona: Persona, snapshot: StockSnapshot) -> str:
        user_prompt = (
            f"The user is asking about {snapshot.name} ({snapshot.ticker}).\n\n"
            f"Here is the most recent fundamental and price data (from yfinance). "
            f"Reason ONLY from these numbers — do not invent additional figures.\n\n"
            f"```\n{snapshot.to_prompt_block()}\n```\n\n"
            "Please respond with:\n"
            "1. A one-paragraph plain-language summary of what the company does.\n"
            "2. A value-vs-growth read on the fundamentals above.\n"
            "3. Your persona's stance (lean toward accumulating / hold / would pass), "
            "with the reasoning rooted in the data.\n"
            "4. The recent price trend (1M / 6M / 1Y) interpreted in context.\n"
            "5. The mandatory disclaimer line."
        )

        logger.info("Calling LLM model=%s persona=%s ticker=%s", self._model, persona.key, snapshot.ticker)

        response = self._client.chat.completions.create(
            model=self._model,
            temperature=0.4,
            messages=[
                {"role": "system", "content": persona.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        return content.strip()
