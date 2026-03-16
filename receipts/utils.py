import json
import os
import re
import ssl
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi


OCR_SPACE_ENDPOINT = "https://api.ocr.space/parse/image"


def _to_decimal(number_text):
    """Convert text like '12.50' or '12,50' to Decimal."""
    cleaned = number_text.replace(" ", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except Exception:
        return None


def _extract_amount(raw_text):
    """Try to find the final total amount from OCR text."""
    lines = raw_text.splitlines()
    amount_pattern = r"(\d+[.,]\d{2})"

    # Strategy 1: Look for "Total due" or "Total charge including VAT" context
    # These usually contain the final invoice amount
    target_keywords = ["total due", "total charge including vat", "total amount", "final total"]
    for i, line in enumerate(lines):
        lower_line = line.lower()
        # Check if this line has a target keyword
        if any(keyword in lower_line for keyword in target_keywords):
            # Money amount might be in same line or next line
            match = re.search(amount_pattern, line)
            if match:
                return _to_decimal(match.group(1))
            # Check next line
            if i + 1 < len(lines):
                match = re.search(amount_pattern, lines[i + 1])
                if match:
                    return _to_decimal(match.group(1))

    # Strategy 2: If no target keyword found, look in lines with "total" keyword
    for i, line in enumerate(lines):
        lower_line = line.lower()
        if "total" in lower_line:
            match = re.search(amount_pattern, line)
            if match:
                return _to_decimal(match.group(1))

    # Strategy 3: Fallback - find largest amount in entire document
    all_matches = re.findall(amount_pattern, raw_text)
    values = [value for value in (_to_decimal(item) for item in all_matches) if value is not None]
    return max(values) if values else None


def _extract_date(raw_text):
    """Try common date formats and return first valid date."""
    patterns = [
        "%d/%m/%Y",
        "%d/%m/%y",
        "%d-%m-%Y",
        "%d-%m-%y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d %b %y",      # 05 Nov 22
        "%d %b %Y",      # 05 Nov 2022
        "%d %B %y",      # 05 November 22
        "%d %B %Y",      # 05 November 2022
    ]

    # Try multi-token patterns first (e.g. "05 Nov 22")
    lines = raw_text.split('\n')
    for line in lines:
        line = line.strip()
        # Try patterns that can match multi-word sequences
        for pattern in patterns:
            try:
                return datetime.strptime(line, pattern).date()
            except ValueError:
                continue

    # Fallback to tokenized approach for numeric patterns


def _extract_vendor(raw_text):
    """Extract vendor name: prefer lines with Ltd/Inc/Company markers (strongly prefer 'Ltd')."""
    skip_words = ["receipt", "invoice", "date", "total", "amount", "tax", "vat", "thanks", "payment", "way", "direct", "debit", "road", "london", "account"]
    
    # Strategy 1: Find lines with "Ltd" (strongest indicator of company name)
    for line in raw_text.splitlines():
        candidate = line.strip()
        if len(candidate) < 5 or len(candidate) > 60:
            continue
        if not any(ch.isalpha() for ch in candidate):
            continue

        lower = candidate.lower()
        if any(word in lower for word in skip_words):
            continue

        # Strongly prefer "Ltd" - most reliable company indicator
        if "ltd" in lower:
            return candidate

    # Strategy 2: Find other company markers (Inc, Corp, Solutions, etc)
    vendor_markers = ["inc", "llc", "company", "corp", "solutions"]
    for line in raw_text.splitlines():
        candidate = line.strip()
        if len(candidate) < 5 or len(candidate) > 60:
            continue
        if not any(ch.isalpha() for ch in candidate):
            continue

        lower = candidate.lower()
        if any(word in lower for word in skip_words):
            continue

        if any(marker in lower for marker in vendor_markers):
            return candidate

    # Strategy 3: Fallback - get first reasonable line
    for line in raw_text.splitlines():
        candidate = line.strip()
        if len(candidate) < 5 or len(candidate) > 60:
            continue
        if not any(ch.isalpha() for ch in candidate):
            continue

        lower = candidate.lower()
        if any(word in lower for word in skip_words):
            continue

        return candidate

    return None


def process_receipt_with_ocr(file_url):
    """Call OCR.space and extract simple fields from the result text."""
    api_key = os.environ.get("OCR_SPACE_API_KEY")
    if not api_key:
        return {"success": False, "error": "OCR_SPACE_API_KEY is not configured."}

    payload = urlencode(
        {
            "apikey": api_key,
            "url": file_url,
            "language": "eng",
            "isOverlayRequired": "false",
        }
    ).encode("utf-8")

    request = Request(
        OCR_SPACE_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        # Timeout set to 60s for PDF processing via OCR.space
        # (OCR.space fetches and processes the file at that URL)
        with urlopen(request, timeout=60, context=ssl_context) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        # Provide more context for timeout errors
        exc_msg = str(exc)
        if "timed out" in exc_msg.lower() or isinstance(exc, TimeoutError):
            error_text = "OCR processing timed out. PDF may be large or network is slow. Please try again."
        else:
            error_text = f"OCR request failed: {exc_msg[:100]}"
        return {"success": False, "error": error_text}


    parsed_results = response_data.get("ParsedResults", [])
    raw_text = "\n".join(item.get("ParsedText", "") for item in parsed_results).strip()
    if not raw_text:
        return {"success": False, "error": "No text extracted."}

    return {
        "success": True,
        "raw_text": raw_text,
        "vendor": _extract_vendor(raw_text),
        "amount": _extract_amount(raw_text),
        "date": _extract_date(raw_text),
    }