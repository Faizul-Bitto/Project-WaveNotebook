import requests

from app.core.config import settings
from app.core.logger import logger

SMS_ENDPOINT = "https://api.sms.net.bd/sendsms"
BALANCE_ENDPOINT = "https://api.sms.net.bd/user/balance/"


def verify_sms_connection():
    """
    Verify SMS.BD API connectivity by checking account balance.
    """

    try:
        response = requests.get(
            BALANCE_ENDPOINT,
            params={
                "api_key": settings.SMS_BD_API_KEY,
            },
            timeout=10,
        )

        response.raise_for_status()

        response_data = response.json()

        if response_data.get("error") != 0:
            raise Exception(response_data.get("msg"))

        logger.info(
            f"✅ SMS.BD Connected Successfully | "
            f"Balance={response_data['data']['balance']}"
        )

        return response_data

    except Exception as error:
        logger.exception(f"❌ SMS.BD Connection Failed | {error}")
        raise


def send_sms(
    phone_number: str,
    message: str,
):
    """
    Send SMS using SMS.BD API.
    """

    payload = {
        "api_key": settings.SMS_BD_API_KEY,
        "msg": message,
        "to": phone_number,
    }

    try:
        logger.info(f"📤 Sending SMS | Phone={phone_number}")

        response = requests.post(
            SMS_ENDPOINT,
            data=payload,
            timeout=10,
        )

        response.raise_for_status()

        response_data = response.json()

        if response_data.get("error") != 0:

            logger.error(
                f"❌ SMS Sending Failed | "
                f"Phone={phone_number} | "
                f"Response={response_data}"
            )

            raise Exception(response_data.get("msg"))

        logger.info(
            f"✅ SMS Sent Successfully | "
            f"Phone={phone_number} | "
            f"Request ID={response_data['data']['request_id']}"
        )

        return response_data

    except requests.RequestException as error:

        logger.exception(
            f"❌ SMS Service Connection Failed | "
            f"Phone={phone_number} | "
            f"Error={error}"
        )

        raise

    except Exception as error:

        logger.exception(
            f"❌ SMS Sending Failed | " f"Phone={phone_number} | " f"Error={error}"
        )

        raise
