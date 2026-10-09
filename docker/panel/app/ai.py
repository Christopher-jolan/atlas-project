import json

from .config import AI_API_KEY
from .gemini import gemini_text


async def generate_executive_insights(context: dict) -> str:
    if not AI_API_KEY:
        return "کلید AI_API_KEY تنظیم نشده است. برای بینش هوشمند، کلید Gemini را در env قرار دهید."

    prompt = f"""تو مشاور مدیریتی یک شرکت نرم‌افزار حسابداری ایرانی هستی.
بر اساس داده‌های واقعی تماس‌های ذخیره‌شده در PostgreSQL، یک گزارش مدیریتی فارسی بنویس.

ساختار:
1. خلاصه وضعیت (۳-۴ جمله)
2. نقاط قوت تیم
3. مشکلات فوری (مشتریان ناراضی، ریسک churn)
4. فرصت‌های فروش (سرنخ‌های داغ)
5. توصیه‌های عملی برای مدیر (۵ مورد مشخص)
6. اولویت‌های هفته آینده

داده‌ها:
{json.dumps(context, ensure_ascii=False, indent=2, default=str)}

فقط متن فارسی بنویس، بدون JSON."""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3},
    }
    try:
        return await gemini_text(payload, timeout=120)
    except Exception as exc:
        return f"خطا در دریافت بینش از Gemini: {exc}"
