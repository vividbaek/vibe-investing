"""Stock → 오행(五行) classifier.

Heuristics that map a ticker's sector / industry / business keywords / brand
color onto one of the 5 elements: wood / fire / earth / metal / water.

Rules of thumb:
- 금 (Metal):  precision · cutting · structure → semis, finance, defense, machinery, gold
- 목 (Wood):   growth · life · organic → biotech, pharma, agri, paper, education
- 수 (Water):  flow · information · fluid → internet, telecom, media, beverage, shipping, pipelines
- 화 (Fire):   energy · transformation → oil, utilities (electric), AI/SaaS, EV, gaming, ads
- 토 (Earth):  stability · physical foundation → REIT, retail, food/staples, construction, materials

Brand color (when known) provides a secondary signal:
- red/orange → fire, yellow/brown → earth, white/silver/gray → metal,
- black/blue → water, green → wood
"""

from __future__ import annotations

from dataclasses import dataclass

Element = str  # "wood" | "fire" | "earth" | "metal" | "water"


# ─────────────────────────────────────────────────────────────────────────────
# GICS sector → primary element (coarse default)
# ─────────────────────────────────────────────────────────────────────────────
SECTOR_TO_ELEMENT: dict[str, Element] = {
    "Information Technology": "fire",
    "Technology": "fire",
    "Communication Services": "water",
    "Communications": "water",
    "Consumer Discretionary": "fire",
    "Consumer Staples": "earth",
    "Consumer Cyclical": "fire",
    "Consumer Defensive": "earth",
    "Energy": "fire",
    "Financial Services": "metal",
    "Financials": "metal",
    "Health Care": "wood",
    "Healthcare": "wood",
    "Industrials": "metal",
    "Materials": "earth",
    "Basic Materials": "earth",
    "Real Estate": "earth",
    "Utilities": "fire",
}

# ─────────────────────────────────────────────────────────────────────────────
# Industry keyword overrides (more specific than sector)
# ─────────────────────────────────────────────────────────────────────────────
# Order matters — first match wins. Lowercased substring search on industry/desc.
_KEYWORD_RULES: list[tuple[str, Element]] = [
    # ── Metal (sharp, structured) ──
    ("semiconductor", "metal"),
    ("chips", "metal"),
    ("foundry", "metal"),
    ("aerospace", "metal"),
    ("defense", "metal"),
    ("weapon", "metal"),
    ("bank", "metal"),
    ("insurance", "metal"),
    ("asset management", "metal"),
    ("capital markets", "metal"),
    ("brokerage", "metal"),
    ("payment", "metal"),
    ("credit service", "metal"),
    ("machinery", "metal"),
    ("mining", "metal"),
    ("precious metal", "metal"),
    ("gold", "metal"),
    ("silver", "metal"),
    # ── Water (flow, info) ──
    ("internet", "water"),
    ("interactive media", "water"),
    ("social media", "water"),
    ("telecom", "water"),
    ("wireless", "water"),
    ("broadcast", "water"),
    ("streaming", "water"),
    ("entertainment", "water"),
    ("media", "water"),
    ("beverage", "water"),
    ("shipping", "water"),
    ("logistics", "water"),
    ("airlines", "water"),
    ("airline", "water"),
    ("midstream", "water"),
    ("pipeline", "water"),
    # ── Fire (energy, transformation) ──
    ("software", "fire"),
    ("application software", "fire"),
    ("infrastructure software", "fire"),
    ("cloud", "fire"),
    ("artificial intelligence", "fire"),
    ("ai ", "fire"),
    ("data analytics", "fire"),
    ("oil & gas", "fire"),  # default oil/gas (after midstream override)
    ("integrated oil", "fire"),
    ("oil refining", "fire"),
    ("oil exploration", "fire"),
    ("electric utilit", "fire"),
    ("renewable energy", "fire"),
    ("solar", "fire"),
    ("auto manufactur", "fire"),
    ("auto parts", "fire"),
    ("electric vehicle", "fire"),
    ("video games", "fire"),
    ("gaming", "fire"),
    ("advertising", "fire"),
    # ── Wood (growth, organic) ──
    ("biotech", "wood"),
    ("pharmaceutical", "wood"),
    ("drug manufactur", "wood"),
    ("medical device", "wood"),
    ("medical instrument", "wood"),
    ("healthcare plan", "wood"),
    ("hospital", "wood"),
    ("agricultur", "wood"),
    ("farm product", "wood"),
    ("packaged food", "wood"),
    ("paper", "wood"),
    ("forestry", "wood"),
    ("lumber", "wood"),
    ("education", "wood"),
    # ── Earth (stable, physical) ──
    ("reit", "earth"),
    ("real estate", "earth"),
    ("residential", "earth"),
    ("retail", "earth"),
    ("discount stor", "earth"),
    ("grocery", "earth"),
    ("restaurant", "earth"),
    ("tobacco", "earth"),
    ("household", "earth"),
    ("personal product", "earth"),
    ("building material", "earth"),
    ("construction", "earth"),
    ("homebuild", "earth"),
    ("cement", "earth"),
    ("steel", "earth"),
    ("chemical", "earth"),
    ("waste management", "earth"),
    ("specialty chemical", "earth"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Color → element (hex hue → element bucket)
# ─────────────────────────────────────────────────────────────────────────────
def color_to_element(hex_color: str | None) -> Element | None:
    """Map a #rrggbb brand color to its closest 오행. Returns None if unparseable."""
    if not hex_color:
        return None
    s = hex_color.strip().lstrip("#")
    if len(s) != 6:
        return None
    try:
        r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except ValueError:
        return None

    # Greyscale → metal (white/silver/gray)
    if abs(r - g) < 18 and abs(g - b) < 18 and abs(r - b) < 18:
        return "metal"

    mx = max(r, g, b)
    if mx < 50:
        return "water"  # near-black → water

    # Dominant hue
    if r > g and r > b:
        # Red dominant → fire (or earth if browny)
        if g > 60 and b < 80 and g < r:
            # brownish/orange-yellow
            if r - g < 60:
                return "earth"
        return "fire"
    if g > r and g > b:
        return "wood"
    if b > r and b > g:
        # Blue dominant → water (deep blue/black) or could be navy
        return "water"
    # Equal mix — yellow (r≈g, low b) → earth
    if r > 150 and g > 150 and b < 120:
        return "earth"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Classify
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class ElementClassification:
    primary: Element
    secondary: Element | None
    source: str  # "keyword" | "sector" | "color" | "manual"


def classify(
    *,
    sector: str | None = None,
    industry: str | None = None,
    business_summary: str | None = None,
    brand_color: str | None = None,
) -> ElementClassification:
    """Classify a ticker into primary + optional secondary 오행.

    Lookup order:
      1) industry keyword match (most specific)
      2) summary keyword match
      3) sector mapping
      4) brand color fallback
    """
    # 1+2: keyword match across industry + summary
    haystack = " ".join(
        s.lower() for s in (industry, business_summary) if s
    )
    primary: Element | None = None
    primary_src = "sector"

    if haystack:
        for kw, elem in _KEYWORD_RULES:
            if kw in haystack:
                primary = elem
                primary_src = "keyword"
                break

    # 3: sector fallback
    if primary is None and sector:
        primary = SECTOR_TO_ELEMENT.get(sector)
        primary_src = "sector"

    # 4: color fallback
    color_elem = color_to_element(brand_color)
    if primary is None:
        if color_elem:
            primary = color_elem
            primary_src = "color"
        else:
            primary = "earth"  # safe default — stable
            primary_src = "default"

    # Secondary: brand color if it differs from primary
    secondary: Element | None = None
    if color_elem and color_elem != primary:
        secondary = color_elem

    return ElementClassification(
        primary=primary, secondary=secondary, source=primary_src,
    )
