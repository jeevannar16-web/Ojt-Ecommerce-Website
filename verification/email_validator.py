"""Email validation service."""

import re
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)



def _check_mx(domain):
    try:
        import dns.resolver
        try:
            dns.resolver.resolve(domain, 'MX')
        except dns.resolver.NoAnswer:
            try:
                dns.resolver.resolve(domain, 'A')
            except Exception:
                return False, f"The domain <strong>{domain}</strong> does not appear to be a valid email domain."
        except dns.resolver.NXDOMAIN:
            return False, f"The domain <strong>{domain}</strong> does not exist."
        except dns.exception.Timeout:
            pass
        return True, None
    except ImportError:
        return True, None
    except Exception as e:
        logger.warning(f"MX check failed for {domain}: {e}")
        return True, None



SERVICES = []


def _register_service(name, check_fn):
    SERVICES.append((name, check_fn))


def _check_zerobounce(email):
    api_key = getattr(settings, 'ZEROBOUNCE_API_KEY', '')
    if not api_key:
        return None
    try:
        resp = requests.get(
            'https://api.zerobounce.net/v2/validate',
            params={'api_key': api_key, 'email': email},
            timeout=10,
        )
        data = resp.json()
        status = data.get('status', '')
        if status == 'invalid':
            return False, f"The email address <strong>{email}</strong> does not appear to exist."
        if status == 'abuse':
            return False, f"The email address <strong>{email}</strong> is from a known abuse/disposable domain."
        if status == 'spamtrap':
            return False, f"This email address cannot be used."
        if status in ('valid', 'catch-all', 'unknown'):
            return True, None
        return True, None
    except requests.RequestException as e:
        logger.warning(f"ZeroBounce API request failed for {email}: {e}")
        return None
    except Exception as e:
        logger.warning(f"ZeroBounce check failed for {email}: {e}")
        return None


def _check_neverbounce(email):
    api_key = getattr(settings, 'NEVERBOUNCE_API_KEY', '')
    if not api_key:
        return None
    try:
        resp = requests.post(
            'https://api.neverbounce.com/v4/single/check',
            json={'key': api_key, 'email': email},
            timeout=10,
        )
        data = resp.json()
        status = data.get('result', '')
        if status in ('invalid', 'disposable'):
            return False, f"The email address <strong>{email}</strong> does not appear to exist."
        if status in ('valid', 'catchall', 'unknown'):
            return True, None
        return True, None
    except requests.RequestException as e:
        logger.warning(f"NeverBounce API request failed for {email}: {e}")
        return None
    except Exception as e:
        logger.warning(f"NeverBounce check failed for {email}: {e}")
        return None


def _check_checkmail(email):
    api_key = getattr(settings, 'CHECKMAIL_API_KEY', '')
    if not api_key:
        return None
    try:
        resp = requests.get(
            'https://api.check-mail.org/v1/check',
            params={'email': email, 'api_key': api_key},
            timeout=10,
        )
        data = resp.json()
        if data.get('valid') is False:
            return False, f"The email address <strong>{email}</strong> does not appear to exist."
        return True, None
    except requests.RequestException as e:
        logger.warning(f"Check-Mail API request failed for {email}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Check-Mail check failed for {email}: {e}")
        return None


def _check_myemailverifier(email):
    api_key = getattr(settings, 'MYEMAILVERIFIER_API_KEY', '')
    if not api_key:
        return None
    try:
        resp = requests.get(
            f'https://client.myemailverifier.com/verifier/validate_single/{email}/{api_key}',
            timeout=10,
        )
        data = resp.json()
        status = data.get('Status', '')
        if status in ('Invalid', 'Unknown'):
            return False, f"The email address <strong>{email}</strong> does not appear to exist."
        if status == 'Valid':
            return True, None
        return True, None
    except requests.RequestException as e:
        logger.warning(f"MyEmailVerifier API request failed for {email}: {e}")
        return None
    except Exception as e:
        logger.warning(f"MyEmailVerifier check failed for {email}: {e}")
        return None


_register_service('ZeroBounce', _check_zerobounce)
_register_service('NeverBounce', _check_neverbounce)
_register_service('Check-Mail', _check_checkmail)
_register_service('MyEmailVerifier', _check_myemailverifier)



def validate_email_deliverability(email):
    if not email or '@' not in email:
        return False, "Please enter a valid email address."

    domain = email.split('@')[1].lower().strip()
    if not re.match(r'^[a-z0-9]([a-z0-9\-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]*[a-z0-9])?)*\.[a-z]{2,}$', domain):
        return False, f"<strong>{domain}</strong> is not a valid domain name."

    any_valid = False
    for name, check_fn in SERVICES:
        result = check_fn(email)
        if result is None:
            continue
        is_valid, _ = result
        if not is_valid:
            return result
        any_valid = True

    if any_valid:
        return True, None

    return _check_mx(domain)
