import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests

CACHE_FILE = Path(__file__).resolve().parent / 'rates_cache.json'
CACHE_TTL = timedelta(hours=1)

LANG_CURRENCY = {
    'en': ('USD', '$'),
    'ne': ('NPR', 'रु'),
    'hi': ('INR', '₹'),
    'ko': ('KRW', '₩'),
}

BASE_CURRENCY = 'USD'


def _load_cache():
    if not CACHE_FILE.exists():
        return None, None
    try:
        data = json.loads(CACHE_FILE.read_text())
        cached_at = datetime.fromisoformat(data['cached_at'])
        if datetime.utcnow() - cached_at < CACHE_TTL:
            return data['rates'], cached_at
    except (json.JSONDecodeError, KeyError, ValueError):
        pass
    return None, None


def _save_cache(rates):
    CACHE_FILE.write_text(json.dumps({
        'rates': rates,
        'cached_at': datetime.utcnow().isoformat(),
    }))


def fetch_rates():
    rates, _ = _load_cache()
    if rates:
        return rates
    try:
        resp = requests.get('https://open.er-api.com/v6/latest/USD', timeout=10)
        data = resp.json()
        if data.get('result') == 'success':
            rates = data['rates']
            _save_cache(rates)
            return rates
    except Exception:
        pass
    return {}


def get_rate(target_code):
    if target_code == BASE_CURRENCY:
        return 1.0
    rates = fetch_rates()
    return rates.get(target_code, 1.0)


def convert_price(amount_usd, lang_code):
    code, symbol = LANG_CURRENCY.get(lang_code, ('USD', '$'))
    rate = get_rate(code)
    converted = float(amount_usd) * rate
    return round(converted, 2), code, symbol
