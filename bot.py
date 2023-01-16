import logging
import os
import re
import requests
from telegram import Update


from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
UAH_EXCHANGE_RATE = 40
DAVINCI_PRICE_PER_TOKEN = 0.02 / 1000

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Echo the user message."""

    text = update.message.text

    match = re.match(r".*tokens\D{0,5}(\d+).*", text)
    tokens = None
    # extract parameters from query. Use it before actual query in format
    # like "tokens=500, temperature=50"
    if match:

        text = re.sub(r"tokens\D{0,5}\d+", "", text)

        tokens = int(match.group(1))

    temperature = None
    match = re.match(r".*temp(?:erature)?\D*\b([1-9]?\d|100)\b.*", text)
    if match:

        text = re.sub(r"temp(?:erature)?\D*\b(?:[1-9]?\d|100)\b", "", text)

        temperature = int(match.group(1)) / 100

    text = re.sub(r"[\s\W]*$", "", text)
    text = re.sub(r"^[\s\W]*", "", text)

    data = {
        "model": "text-davinci-003",
        "prompt": text + "\n",
        "temperature": temperature or 0.2,
        "max_tokens": tokens or 500,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    res = requests.post(
        "https://api.openai.com/v1/completions", json=data, headers=headers
    )

    gpt_text = res.json().get("choices")[0]["text"]
    tokens_used = res.json().get("usage")

    answer = f"```\n---{gpt_text}\n---```"
    approx_price = (
        tokens_used["total_tokens"] * DAVINCI_PRICE_PER_TOKEN * UAH_EXCHANGE_RATE
    )
    response_text = (
        f"GPT3 answers: \n{answer}"
        f"\n\nApproximate price: UAH {approx_price:.2f}"
        f"\nParameters applied: `{data}`"
    )
    try:
        await update.message.reply_markdown(response_text)
    except Exception as e:
        await update.message.reply_markdown(
            f"```\nException during script execution: {e}```"
        )


def main() -> None:

    """Start the bot."""
    application = Application.builder().token(TG_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()


if __name__ == "__main__":

    main()
