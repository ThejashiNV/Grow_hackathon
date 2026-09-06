"""Rule-based headline classifier with expanded taxonomy.

Maps headline text to an event type and baseline impact score (0-100).
Covers company-specific, macro, sector, commodity, geopolitical, and
global market events. Rules are ordered most-specific-first.
"""

import re

from app.schemas.events import EventType

_RULES: list[tuple[EventType, float, list[str]]] = [
    # ── Company-specific (highest specificity) ──
    (EventType.EXECUTIVE_RESIGNATION, 90, [
        r"\bceo\b.*(resign|quit|step(s|ped)? down|ousted)",
        r"\bcfo\b.*(resign|quit|step(s|ped)? down)",
        r"(resign|quit|step(s|ped)? down).*\b(ceo|cfo|md|managing director)\b",
    ]),
    (EventType.MERGER_ACQUISITION, 85, [
        r"\bmerger\b", r"\bacquisition\b", r"\bacquire[sd]?\b",
        r"\btakeover\b", r"\bstake sale\b", r"\bbuy(s|ing)?\b.*\bcompany\b",
        r"\bdemerger\b", r"\bspin[\s-]?off\b",
    ]),
    (EventType.REGULATORY_ACTION, 80, [
        r"\bsebi\b", r"\brbi\b.*(action|penalty|ban|fine|order)",
        r"\bregulatory\b.*(action|probe|notice|order)",
        r"\bban(ned)?\b.*\b(trading|entity)\b",
    ]),
    (EventType.LEGAL_ISSUE, 78, [
        r"\blawsuit\b", r"\blitigation\b", r"\bfraud\b",
        r"\bprobe\b", r"\bcbi\b", r"\braid\b",
        r"\bed\b.*(probe|raid|attach|summon)",
        r"\benforcement directorate\b",
    ]),
    (EventType.EARNINGS_SURPRISE, 75, [
        r"\bbeats?\b.*(estimate|expectation|street)",
        r"\bmisses?\b.*(estimate|expectation|street)",
        r"\bearnings surprise\b",
    ]),
    (EventType.CREDIT_RATING_CHANGE, 70, [
        r"\brating\b.*(upgrade|downgrade|cut|revis)",
        r"\bmoody'?s\b", r"\bcrisil\b", r"\bicra\b",
        r"\bs&p\b.*(upgrade|downgrade)", r"\bfitch\b.*(upgrade|downgrade)",
    ]),
    (EventType.PROMOTER_ACTIVITY, 68, [
        r"\bpromoter\b.*(pledge|sell|buy|stake|holding)",
    ]),
    (EventType.INSIDER_ACTIVITY, 65, [
        r"\binsider\b.*(trading|buy|sell)",
        r"\bbulk deal\b", r"\bblock deal\b",
    ]),
    (EventType.MANAGEMENT_CHANGE, 60, [
        r"\bappoint(s|ed)?\b.*(ceo|cfo|md|director|chairman)",
        r"\bnew\b.*(ceo|cfo|chairman)",
    ]),
    (EventType.FUNDRAISING, 58, [
        r"\bqip\b", r"\brights issue\b", r"\bfund(s|ing)? rais\w*\b",
        r"\bipo\b", r"\bfpo\b", r"\bofs\b",
    ]),
    (EventType.ANALYST_ACTION, 55, [
        r"\bupgrade[sd]?\b.*(target|rating|stock)",
        r"\bdowngrade[sd]?\b.*(target|rating|stock)",
        r"\btarget price\b", r"\binitiat(e|es|ed)\b.*coverage",
    ]),
    (EventType.EARNINGS, 50, [
        r"\bq[1-4]\b.*(result|earnings|profit|revenue)",
        r"\bearnings\b", r"\bresults? announc",
    ]),
    (EventType.PROFIT_CHANGE, 48, [
        r"\bnet profit\b",
        r"\bprofit (rises?|falls?|jumps?|drops?|surges?|declines?)",
        r"\bpat\b.*(rise|fall|jump|drop|surge|decline)",
    ]),
    (EventType.REVENUE_CHANGE, 46, [
        r"\brevenue (rises?|falls?|jumps?|drops?|grows?|surges?|declines?)",
        r"\btopline\b.*(rise|fall|jump|grow)",
    ]),
    (EventType.MAJOR_CONTRACT, 50, [
        r"\bcontract\b.*(win|bags?|secures?|worth|award)",
        r"\border\b.*(win|bags?|worth|award)",
    ]),
    (EventType.DIVIDEND, 40, [r"\bdividend\b"]),
    (EventType.BUYBACK, 42, [r"\bbuyback\b", r"\bshare repurchase\b"]),
    (EventType.PRODUCT_LAUNCH, 35, [
        r"\blaunch(es|ed)?\b.*\b(product|service|platform|app)\b",
        r"\bunveil(s|ed)?\b",
    ]),

    # ── Macro / Central Bank ──
    (EventType.MACRO_RATE_CHANGE, 82, [
        r"\brepo rate\b", r"\brate (cut|hike|hold|pause|change)\b",
        r"\brbi\b.*(rate|policy|mpc|monetary)",
        r"\bmpc\b.*(decision|meet|vote|rate)",
        r"\bfed\b.*(rate|hike|cut|pause|hold)",
        r"\binterest rate\b.*(cut|hike|change|rise|fall)",
    ]),
    (EventType.MACRO_INFLATION, 72, [
        r"\bcpi\b.*(data|rise|fall|inflation)",
        r"\bwpi\b.*(data|rise|fall|inflation)",
        r"\binflation\b.*(rise|fall|ease|surge|data|hit|high|low|target|above|below)",
        r"\bcore inflation\b",
    ]),
    (EventType.MACRO_GDP, 70, [
        r"\bgdp\b.*(growth|data|slow|fall|rise|expand|contract|forecast|estimate)",
        r"\beconomic growth\b",
    ]),
    (EventType.MACRO_FISCAL, 68, [
        r"\bbudget\b.*(union|interim|fiscal|allocat|spend|tax)",
        r"\bfiscal deficit\b",
        r"\bgst\b.*(collection|revenue|rate|change|council)",
        r"\btax (reform|cut|hike|change)\b",
    ]),

    # ── Sector-wide ──
    (EventType.SECTOR_REGULATION, 65, [
        r"\b(auto|pharma|banking|telecom|it|fmcg|metal|energy)\b.*(regulation|policy|rule|reform|mandate)",
        r"\bnew (norm|rule|regulation)\b.*\b(sector|industry)\b",
    ]),
    (EventType.SECTOR_TREND, 55, [
        r"\bsector\b.*(rally|fall|rotation|outperform|underperform|sell[\s-]?off)",
        r"\b(it|banking|pharma|auto|fmcg|metal|energy|realty)\b.*(stocks?|sector)\b.*(rally|fall|surge|drop|gain|lose)",
    ]),

    # ── Commodity ──
    (EventType.COMMODITY_PRICE, 60, [
        r"\b(crude|brent|wti)\b.*(oil)?\b.*(price|rise|fall|surge|drop|jump|crash|rally)",
        r"\bgold\b.*(price|rise|fall|high|record|surge)",
        r"\bcopper\b.*(price|rise|fall|surge|drop)",
        r"\bsteel\b.*(price|rise|fall|surge|drop)",
        r"\b(iron ore|coking coal)\b.*(price|rise|fall)",
        r"\bcommodity\b.*(price|rally|crash|surge|slump)",
        r"\bnatural gas\b.*(price|rise|fall|surge)",
    ]),

    # ── Geopolitical ──
    (EventType.GEOPOLITICAL, 75, [
        r"\btrade war\b", r"\btariff\b.*(impose|hike|retaliat|war)",
        r"\bsanction(s|ed)?\b", r"\bgeopolit\w+\b",
        r"\bwar\b.*(escalat|tension|conflict)",
        r"\bmilitary\b.*(strike|action|tension)",
        r"\bchina[\s-](us|india)\b.*(tension|conflict|dispute)",
        r"\bopec\b.*(cut|output|decision|agree)",
    ]),

    # ── Global markets ──
    (EventType.GLOBAL_MARKET, 55, [
        r"\bwall street\b.*(rally|fall|crash|surge|plunge)",
        r"\bnasdaq\b.*(rally|fall|high|crash|surge|record)",
        r"\bs&?p[\s]?500\b.*(rally|fall|high|crash)",
        r"\bglobal market\b.*(rally|fall|sell|rout|crash|surge)",
        r"\bfii\b.*(buy|sell|inflow|outflow)",
        r"\bdii\b.*(buy|sell|inflow|outflow)",
        r"\b(us|europe|asia)\b.*(market|stocks?)\b.*(rally|fall|crash|surge|plunge)",
    ]),

    # ── Legacy catch-all for sector/macro that didn't match specific ──
    (EventType.MACRO_SECTOR_EVENT, 45, [
        r"\brbi policy\b", r"\binflation\b", r"\bgdp\b",
    ]),
]


def classify_headline(title: str) -> tuple[EventType, float]:
    lowered = title.lower()
    for event_type, impact_score, patterns in _RULES:
        for pattern in patterns:
            if re.search(pattern, lowered):
                return event_type, impact_score
    return EventType.OTHER, 20.0


EVENT_CATEGORY: dict[str, str] = {
    EventType.EARNINGS: "company",
    EventType.EARNINGS_SURPRISE: "company",
    EventType.REVENUE_CHANGE: "company",
    EventType.PROFIT_CHANGE: "company",
    EventType.MANAGEMENT_CHANGE: "company",
    EventType.EXECUTIVE_RESIGNATION: "company",
    EventType.MERGER_ACQUISITION: "company",
    EventType.REGULATORY_ACTION: "company",
    EventType.LEGAL_ISSUE: "company",
    EventType.PRODUCT_LAUNCH: "company",
    EventType.MAJOR_CONTRACT: "company",
    EventType.DIVIDEND: "company",
    EventType.BUYBACK: "company",
    EventType.FUNDRAISING: "company",
    EventType.CREDIT_RATING_CHANGE: "company",
    EventType.ANALYST_ACTION: "company",
    EventType.PROMOTER_ACTIVITY: "company",
    EventType.INSIDER_ACTIVITY: "company",
    EventType.MACRO_RATE_CHANGE: "macro",
    EventType.MACRO_INFLATION: "macro",
    EventType.MACRO_GDP: "macro",
    EventType.MACRO_FISCAL: "macro",
    EventType.SECTOR_TREND: "sector",
    EventType.SECTOR_REGULATION: "sector",
    EventType.COMMODITY_PRICE: "commodity",
    EventType.GEOPOLITICAL: "geopolitical",
    EventType.GLOBAL_MARKET: "global",
    EventType.MACRO_SECTOR_EVENT: "macro",
    EventType.OTHER: "other",
}
