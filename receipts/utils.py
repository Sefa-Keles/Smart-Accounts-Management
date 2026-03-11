import json
import os
import re
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import Request, urlopen


OCR_SPACE_ENDPOINT = "https://api.ocr.space/parse/imageurl"


def _to_decimal(number_text):
    """Convert text like '12.50' or '12,50' to Decimal."""
    cleaned = number_text.replace(" ", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except Exception:
        return None


def _extract_amount(raw_text):
    """Try to find total amount from OCR text."""
    lines = raw_text.splitlines()
    amount_pattern = r"(\d+[.,]\d{2})"

    for line in lines:
        lower_line = line.lower()
        if "total" in lower_line or "amount" in lower_line:
            match = re.search(amount_pattern, line)
            if match:
                return _to_decimal(match.group(1))

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
    ]

    tokens = raw_text.replace("\n", " ").split()
    for token in tokens:
        candidate = token.strip(".,:;()[]{}")
        for pattern in patterns:
            try:
                return datetime.strptime(candidate, pattern).date()
            except ValueError:
                continue
    return None


def _extract_vendor(raw_text):
    """Take first meaningful text line as vendor name."""
    skip_words = ["receipt", "invoice", "date", "total", "amount", "tax", "vat"]

    for line in raw_text.splitlines():
        candidate = line.strip()
        if len(candidate) < 3:
            continue
        if not any(ch.isalpha() for ch in candidate):
            continue

        lower_candidate = candidate.lower()
        if any(word in lower_candidate for word in skip_words):
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
        with urlopen(request, timeout=25) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"success": False, "error": f"OCR request failed: {exc}"}

    if response_data.get("IsErroredOnProcessing"):
        error_list = response_data.get("ErrorMessage") or ["Unknown OCR error"]
        return {"success": False, "error": "; ".join(error_list)}

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