"""Lightweight rule-based headline classifier.

Per the hackathon scope, this is deliberately not a trained model: a keyword
ruleset mapping headline text to an event type and a baseline impact score
(0-100, "how important is this kind of event generally"). Swappable later for
an LLM-assisted classifier without touching callers.
"""

import re

from app.schemas.events import EventType

# Ordered most-specific-first: the first matching rule wins.
_RULES: list[tuple[EventType, float, list[str]]] = [
    (EventType.EXECUTIVE_RESIGNATION, 90, [r"\bceo\b.*(resign|quit|step(s|ped)? down|ousted)", r"\bcfo\b.*(resign|quit|step(s|ped)? down)", r"(resign|quit|step(s|ped)? down).*\b(ceo|cfo|md|managing director)\b"]),
    (EventType.MERGER_ACQUISITION, 85, [r"\bmerger\b", r"\bacquisition\b", r"\bacquire[sd]?\b", r"\btakeover\b", r"\bstake sale\b"]),
    (EventType.REGULATORY_ACTION, 80, [r"\bsebi\b", r"\brbi\b.*(action|penalty|ban)", r"\bregulatory\b.*(action|probe|notice)", r"\bban(ned)?\b"]),
    (EventType.LEGAL_ISSUE, 78, [r"\blawsuit\b", r"\blitigation\b", r"\bfraud\b", r"\bprobe\b", r"\bcbi\b", r"\braid\b"]),
    (EventType.EARNINGS_SURPRISE, 75, [r"\bbeats?\b.*(estimate|expectation)", r"\bmisses?\b.*(estimate|expectation)", r"\bearnings surprise\b"]),
    (EventType.CREDIT_RATING_CHANGE, 70, [r"\brating\b.*(upgrade|downgrade|cut|revis)", r"\bmoody'?s\b", r"\bcrisil\b", r"\bicra\b"]),
    (EventType.PROMOTER_ACTIVITY, 68, [r"\bpromoter\b.*(pledge|sell|buy|stake)"]),
    (EventType.INSIDER_ACTIVITY, 65, [r"\binsider\b.*(trading|buy|sell)", r"\bbulk deal\b", r"\bblock deal\b"]),
    (EventType.MANAGEMENT_CHANGE, 60, [r"\bappoint(s|ed)?\b.*(ceo|cfo|md|director|chairman)", r"\bnew\b.*(ceo|cfo|chairman)"]),
    (EventType.FUNDRAISING, 58, [r"\bqip\b", r"\brights issue\b", r"\bfund(s|ing)? rais\w*\b", r"\bipo\b"]),
    (EventType.ANALYST_ACTION, 55, [r"\bupgrade[sd]?\b.*(target|rating|stock)", r"\bdowngrade[sd]?\b.*(target|rating|stock)", r"\btarget price\b"]),
    (EventType.EARNINGS, 50, [r"\bq[1-4]\b.*(result|earnings|profit|revenue)", r"\bearnings\b", r"\bresults? announc"]),
    (EventType.PROFIT_CHANGE, 48, [r"\bnet profit\b", r"\bprofit (rises?|falls?|jumps?|drops?|surges?)"]),
    (EventType.REVENUE_CHANGE, 46, [r"\brevenue (rises?|falls?|jumps?|drops?|grows?)"]),
    (EventType.MAJOR_CONTRACT, 50, [r"\bcontract\b.*(win|bags?|secures?|worth)", r"\border\b.*(win|bags?|worth)"]),
    (EventType.DIVIDEND, 40, [r"\bdividend\b"]),
    (EventType.BUYBACK, 42, [r"\bbuyback\b", r"\bshare repurchase\b"]),
    (EventType.PRODUCT_LAUNCH, 35, [r"\blaunch(es|ed)?\b"]),
    (EventType.MACRO_SECTOR_EVENT, 45, [r"\bsector\b", r"\brbi policy\b", r"\brepo rate\b", r"\binflation\b", r"\bgdp\b"]),
]


def classify_headline(title: str) -> tuple[EventType, float]:
    lowered = title.lower()
    for event_type, impact_score, patterns in _RULES:
        for pattern in patterns:
            if re.search(pattern, lowered):
                return event_type, impact_score
    return EventType.OTHER, 20.0
