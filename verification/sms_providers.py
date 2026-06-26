"""SMS provider abstraction layer — supports multiple backends for sending OTPs."""

import logging
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger(__name__)


# ==============================================================================
# SECTION: Abstract Base Provider
# ==============================================================================

class SMSProvider(ABC):
    @abstractmethod
    def send_otp(self, phone: str, otp: str) -> dict:
        ...

    @abstractmethod
    def verify_otp(self, phone: str, otp: str) -> bool:
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        ...


class TwilioSMSProvider(SMSProvider):
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
        self.messaging_service_sid = settings.TWILIO_MESSAGING_SERVICE_SID
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from twilio.rest import Client
            self._client = Client(self.account_sid, self.auth_token)
        return self._client

    def send_otp(self, phone: str, otp: str) -> dict:
        try:
            message = self.client.messages.create(
                body=f'Your verification code is: {otp}. Valid for 15 minutes.',
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone,
                messaging_service_sid=self.messaging_service_sid or None,
            )
            logger.info(f'SMS sent to {phone}, SID: {message.sid}')
            return {'success': True, 'sid': message.sid}
        except Exception as e:
            logger.error(f'Twilio SMS failed for {phone}: {e}')
            return {'success': False, 'error': str(e)}

    def verify_otp(self, phone: str, otp: str) -> bool:
        try:
            verification_check = self.client.verify \
                .v2 \
                .services(self.verify_service_sid) \
                .verification_checks \
                .create(to=phone, code=otp)
            return verification_check.status == 'approved'
        except Exception as e:
            logger.error(f'Twilio verification check failed for {phone}: {e}')
            return False

    def get_provider_name(self) -> str:
        return 'twilio'


# ==============================================================================
# SECTION: Console Provider (Dev)
# ==============================================================================

class ConsoleSMSProvider(SMSProvider):
    """Development-only provider that logs SMS to console."""

    def send_otp(self, phone: str, otp: str) -> dict:
        print(f'\n=== SMS VERIFICATION ===')
        print(f'  To: {phone}')
        print(f'  OTP: {otp}')
        print(f'  Valid for: 15 minutes')
        print(f'=======================\n')
        logger.info(f'[DEV SMS] Sent OTP {otp} to {phone}')
        return {'success': True, 'sid': 'dev-mode'}

    def verify_otp(self, phone: str, otp: str) -> bool:
        logger.info(f'[DEV SMS] Verifying {otp} for {phone}')
        return True

    def get_provider_name(self) -> str:
        return 'console'


# ==============================================================================
# SECTION: Provider Factory
# ==============================================================================

def get_sms_provider() -> SMSProvider:
    provider_name = getattr(settings, 'SMS_PROVIDER', 'console').lower()
    if provider_name == 'twilio':
        if not getattr(settings, 'TWILIO_ACCOUNT_SID', None):
            logger.warning('Twilio selected but TWILIO_ACCOUNT_SID not set, falling back to console')
            return ConsoleSMSProvider()
        return TwilioSMSProvider()
    return ConsoleSMSProvider()
