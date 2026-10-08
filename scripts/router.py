import json
import re
import sys
import time

from answer import answer_question
from search_kb import openai_client

CHAT_MODEL = "gpt-4.1-mini"

SAFETY_PATTERN = re.compile(
    r"\b(power|electric|electrical|utility)?\s*(line|lines|wire|wires|cable|cables)\b.{0,30}\b(down|fell|fallen|hanging|on the ground|snapped|broke|broken|sparking|sparks)\b"
    r"|\b(downed line|downed power line|sparks|sparking|on fire|smoke|electrocut\w*)\b"
    r"|\b(cable|cables) (ca[ií]do|ca[ií]dos)\b|\bchispas\b",
    re.IGNORECASE,
)

SAFETY_MESSAGE = (
    "Stay at least 35 feet away from any downed or damaged power line and treat it as live. "
    "Call 512-322-9100 to report it right away, and call 9-1-1 if anyone is hurt or there is fire or smoke."
)

TEMPLATES = {
    "report_outage": (
        "You can report an outage online on the Outage Map, by texting OUT to 287846, or by calling 512-322-9100. "
        "Check your breakers first if it is safe to do so.", ["P01"]),
    "check_outage_status": (
        "Check the Austin Energy Outage Map for the status of your outage and the estimated restoration time. "
        "Estimates can change once crews see the damage. You can also call 512-322-9100.", ["P02", "P36"]),
    "start_stop_transfer": (
        "To start, stop, or transfer service, call Customer Care at 512-494-9400, use Online Customer Care at coautilities.com, "
        "or visit a walk in Utility Customer Service Center. Starting service has a $20 fee and a $200 deposit, which can be waived in some cases.",
        ["P26", "P27"]),
    "bill_dispute": (
        "To dispute a bill, request an administrative review within 90 days by calling Customer Care at 512-494-9400 "
        "or visiting a Utility Customer Service Center. Would you like me to connect you with a representative?", ["P11"]),
}

DECLINES = {
    "account_specific": "I can't see account details. Log in to your account at coautilities.com or call Customer Care at 512-494-9400.",
    "other_city_service": "That isn't handled by Austin Energy. Please call 3-1-1 or visit austintexas.gov/311 for other City of Austin services.",
    "commercial": "I can only help with residential questions. For business accounts, please call Customer Care at 512-494-9400.",
    "unrelated": "I can only help with Austin Energy residential questions, like outages, bills, rebates, and safety.",
}

HUMAN_OFFER = " If you'd like, I can connect you with a Customer Care representative at 512-494-9400."

CLASSIFIER_PROMPT = """You route messages for an Austin Energy residential customer help assistant.
Classify the customer message into exactly one route:

- safety: a downed, hanging, or damaged power line, sparks, fire, smoke, or someone in electrical danger.
- report_outage: the customer wants to report that their power is out.
- check_outage_status: the customer wants to know when power will be restored or see outage status.
- start_stop_transfer: the customer wants to start, stop, or move utility service (including moving homes).
- bill_dispute: the customer wants to formally dispute or contest a bill.
- out_of_scope: anything Austin Energy residential help cannot answer. Also give "scope_reason":
  account_specific (balances, due dates, account changes), other_city_service (water, trash, roads, permits, 3-1-1 issues),
  commercial (business accounts, contractors), unrelated (anything else).
- ambiguous: the message could reasonably mean two or more different things and a wrong guess would mislead.
  Also write one short "clarifying_question" in the customer's language.
- informational: a question about Austin Energy or City of Austin Utilities residential programs, bills, rates,
  payments, assistance, rebates, solar, EV, GreenChoice, outages, trees, safety tips, or scams.

Also return "language" (two letter code of the customer's language) and "summary" (one short sentence describing what the customer needs, for a human agent).

Return JSON only:
{"route": "...", "scope_reason": "", "clarifying_question": "", "language": "en", "summary": "..."}"""


def classify(message):
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": CLASSIFIER_PROMPT}, {"role": "user", "content": message}],
    )
    try:
        result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        result = {"route": "informational", "language": "en", "summary": message}
    return result, response.usage.prompt_tokens, response.usage.completion_tokens


def translate(text, language):
    if language in ("", "en", None):
        return text, 0, 0
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": f"Translate the text into the language with code '{language}'. "
                                          "Keep phone numbers, codes, amounts, and website addresses exactly as written. Return only the translation."},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content.strip(), response.usage.prompt_tokens, response.usage.completion_tokens


def respond(message):
    start = time.perf_counter()
    tokens_in = tokens_out = 0
    result = {"route": "", "action": "", "answer": "", "cited_pages": [], "offer_human": False, "handoff_summary": ""}

    if SAFETY_PATTERN.search(message):
        result.update(route="safety", action="safety", answer=SAFETY_MESSAGE, cited_pages=["P04", "P35"])
        language = "en"
        classification = {}
    else:
        classification, t_in, t_out = classify(message)
        tokens_in += t_in
        tokens_out += t_out
        route = classification.get("route", "informational")
        language = classification.get("language", "en")
        result["route"] = route

        if route == "safety":
            result.update(action="safety", answer=SAFETY_MESSAGE, cited_pages=["P04", "P35"])
        elif route in TEMPLATES:
            text, pages = TEMPLATES[route]
            result.update(action="route", answer=text, cited_pages=pages, offer_human=route == "bill_dispute")
        elif route == "out_of_scope":
            reason = classification.get("scope_reason") or "unrelated"
            result.update(action="decline", answer=DECLINES.get(reason, DECLINES["unrelated"]))
        elif route == "ambiguous" and classification.get("clarifying_question"):
            result.update(action="clarify", answer=classification["clarifying_question"])
            language = "en"
        else:
            rag = answer_question(message)
            tokens_in += rag["input_tokens"]
            tokens_out += rag["output_tokens"]
            if rag["answerable"]:
                result.update(action="answer", answer=rag["answer"], cited_pages=rag["cited_pages"])
                language = "en"
            else:
                result.update(action="handoff", answer=rag["answer"], offer_human=True,
                              handoff_summary=classification.get("summary", message))

    if result["action"] in ("safety", "route", "decline", "handoff") and language != "en":
        translated, t_in, t_out = translate(result["answer"], language)
        result["answer"] = translated
        tokens_in += t_in
        tokens_out += t_out

    if any(word in message.lower() for word in ("disconnect", "shut off", "cut off", "desconex")) and result["action"] == "answer":
        result["answer"] += HUMAN_OFFER
        result["offer_human"] = True

    result["latency_s"] = round(time.perf_counter() - start, 2)
    result["input_tokens"] = tokens_in
    result["output_tokens"] = tokens_out
    return result


if __name__ == "__main__":
    reply = respond(" ".join(sys.argv[1:]))
    print(f"[{reply['route']} -> {reply['action']}]")
    print(reply["answer"])
    if reply["cited_pages"]:
        print("Sources: " + ", ".join(reply["cited_pages"]))
    if reply["handoff_summary"]:
        print("Handoff note for agent: " + reply["handoff_summary"])
    print(f"latency: {reply['latency_s']}s  tokens: {reply['input_tokens']} in / {reply['output_tokens']} out")
