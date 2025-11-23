# xbrl_processing/fact_extractor.py
from __future__ import annotations

from types import SimpleNamespace
from typing import Iterator, Optional

from lxml import etree


def _iter_facts(model_xbrl) -> Iterator:
    """
    Yield fact-like objects even if Arelle failed to load taxonomy definitions.
    Falls back to scanning raw XML elements with a contextRef attribute.
    """
    facts = getattr(model_xbrl, "facts", None)
    if facts:
        for fact in facts:
            yield fact
        return

    # Fallback path: parse raw XML for elements that look like facts
    root = getattr(getattr(model_xbrl, "modelDocument", None), "xmlRootElement", None)
    if root is None:
        return

    contexts = getattr(model_xbrl, "contexts", {})

    ix_namespace = "http://www.xbrl.org/2013/inlineXBRL"

    for elem in root.iter():
        tag = elem.tag
        if not isinstance(tag, str):
            continue

        context_ref = elem.get("contextRef")
        if not context_ref:
            continue

        qname = etree.QName(tag)
        local_name: Optional[str] = None

        if qname.namespace == ix_namespace and qname.localname in {"nonNumeric", "nonFraction"}:
            name_attr = elem.get("name")
            if not name_attr:
                continue
            local_name = name_attr.split(":")[-1]
        else:
            local_name = qname.localname

        if not local_name:
            continue

        text = "".join(elem.itertext()).strip()
        if not text:
            continue

        fake_fact = SimpleNamespace()
        fake_fact.qname = SimpleNamespace(localName=local_name)
        fake_fact.value = text
        fake_fact.context = contexts.get(context_ref)

        yield fake_fact


def get_fact(model_xbrl, local_name: str) -> Optional[str]:
    """
    Extract the first fact with a given localname.
    Returns text or None.
    """
    for fact in _iter_facts(model_xbrl):
        if fact.qname.localName == local_name and fact.value not in ("", None):
            return str(fact.value).strip()
    return None


def get_all_text_facts(model_xbrl) -> list[str]:
    """
    Extract all non-empty fact values as plain strings.
    Useful for fallback text search if needed.
    """
    facts: list[str] = []
    for fact in _iter_facts(model_xbrl):
        if fact.value and isinstance(fact.value, str) and len(fact.value.strip()) > 5:
            facts.append(fact.value.strip())
    return facts
