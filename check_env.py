from dotenv import load_dotenv; load_dotenv()
import os
vars = ['OKX_API_KEY','OKX_SECRET_KEY','OKX_PASSPHRASE','OKX_FLAG','OKX_INSTRUMENT','GEMINI_API_KEY','TELEGRAM_TOKEN']
for v in vars:
    val = os.getenv(v)
    status = "OK" if val else "MISSING"
    if val and len(val) > 10:
        val = val[:6] + "..." + val[-4:]
    print(f"{v}: {status} ({val})")
