# 🌾 KisanBazaar

**Direct from Farm to Your Table** — a Django marketplace that connects Indian farmers with buyers, with zero middlemen, AI-powered ROI forecasting, and a Hinglish chatbot (Kisan Mitra).

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [Running Tests](#running-tests)
- [URL Reference](#url-reference)
- [AI Features (Gemini)](#ai-features-gemini)
- [Bug Fixes Applied](#bug-fixes-applied)
- [Deployment Notes](#deployment-notes)

---

## Features

| Feature | Description |
|---|---|
| 🧑‍🌾 Farmer Dashboard | List, manage, and delete crop listings |
| 🛒 Buyer Marketplace | Search crops by name and location, contact farmers via WhatsApp |
| 📈 ROI Predictor | AI-powered market forecast per listing (Gemini API) |
| 🤖 Kisan Mitra | Hinglish AI chatbot for farming advice, schemes, and storage tips |
| 🌐 Google Translate | One-click translation into Hindi, Marathi, Punjabi, Tamil, Telugu and more |
| ⏰ Freshness Badges | Auto-calculated expiry dates with 🟢🟡🔴⚫ urgency badges |
| 📱 Mobile Friendly | Responsive design built with Tailwind CSS |
| 🔐 Role-based Auth | Farmer / Buyer / Warehouse / Wholesaler roles |

---

## Project Structure

```
kisanbazaar/                  ← Django project root
├── manage.py
├── kisanbazaar/
│   ├── settings.py
│   ├── urls.py               ← include('marketplace.urls')
│   └── wsgi.py
└── marketplace/              ← Main app
    ├── models.py             ← User, Product
    ├── views.py              ← All views + Gemini helpers
    ├── forms.py              ← RegisterForm, LoginForm, ProductForm
    ├── admin.py              ← Styled admin panels
    ├── apps.py
    ├── urls.py               ← App URL patterns
    ├── tests.py              ← Unit + integration tests
    ├── migrations/
    └── templates/
        └── marketplace/
            ├── base.html
            ├── home.html
            ├── login.html
            ├── register.html
            ├── farmer_dashboard.html
            ├── add_product.html
            ├── kisan_mitra.html
            └── whatsapp.html     ← SVG icon partial
    └── static/
        └── marketplace/
            ├── css/global.css
            └── js/
                ├── global.js
                ├── add_product.js
                └── farmer_dashboard.js
```

---

## Quick Start

### 1. Clone & set up a virtual environment

```bash
git clone https://github.com/yourname/kisanbazaar.git
cd kisanbazaar
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install django pillow python-dotenv
```

> **Pillow** is required for `ImageField` on the Product model.

### 3. Create `.env` file in the project root

```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key-here
```

### 4. Update `settings.py`

Add the following to your `kisanbazaar/settings.py`:

```python
import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

INSTALLED_APPS = [
    ...
    'marketplace',
]

# Custom user model
AUTH_USER_MODEL = 'marketplace.User'

# Gemini API key (read by views.py)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Media files (product images)
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 5. Include marketplace URLs

In `kisanbazaar/urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('marketplace.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 6. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## Configuration

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ Yes | Django secret key |
| `DEBUG` | No | `True` for dev, `False` for prod |
| `GEMINI_API_KEY` | For AI features | Get from [Google AI Studio](https://aistudio.google.com/) |
| `DATABASE_URL` | For production | Default is SQLite |

---

## Running Tests

```bash
python manage.py test marketplace
```

Tests cover:
- User role methods (`is_farmer`, `is_buyer`, etc.)
- Product expiry auto-calculation
- Urgency level logic
- Crop emoji mapping
- Home / login / register page loads
- Farmer dashboard access control
- Kisan Mitra chat endpoint validation

---

## URL Reference

| URL | View | Auth Required |
|---|---|---|
| `/` | Home / marketplace | No |
| `/register/` | Register | No |
| `/login/` | Login | No |
| `/logout/` | Logout | No |
| `/farmer/dashboard/` | Farmer dashboard | ✅ Farmer only |
| `/farmer/add/` | List a crop | ✅ Farmer only |
| `/farmer/delete/<pk>/` | Delete listing | ✅ Farmer only |
| `/farmer/roi/<pk>/` | ROI forecast (JSON) | ✅ Farmer only |
| `/kisan-mitra/` | Kisan Mitra chat page | ✅ Farmer only |
| `/kisan-mitra/chat/` | Chat AJAX endpoint (POST) | ✅ Farmer only |
| `/admin/` | Django admin | ✅ Staff only |

---

## AI Features (Gemini)

Both AI features use the **Gemini 1.5 Flash** model via the REST API (no SDK needed).

### ROI Predictor

Hit the endpoint from the farmer dashboard card:

```
GET /farmer/roi/<product_id>/
```

Returns JSON:
```json
{
  "success": true,
  "crop": "Tomato",
  "product_id": 7,
  "analysis": "Tomato prices in Jaipur are steady at ₹18–22/kg..."
}
```

### Kisan Mitra Chat

```
POST /kisan-mitra/chat/
Content-Type: application/json
X-CSRFToken: <token>

{ "message": "Tomato ka sahi bhav kya hai?" }
```

Returns:
```json
{
  "success": true,
  "reply": "Aaj Jaipur mandi mein tomato ka bhav ₹15–20/kg hai..."
}
```

If the API key is missing, both endpoints return a safe fallback message instead of crashing.

---

## Bug Fixes Applied

### `views.py`
- **Gemini URL was built at module load time** — if `GEMINI_API_KEY` was set after import, the URL had an empty key. Fixed by building the URL inside a helper `_get_gemini_url()` that reads the key at call time.
- **Missing 429 handling** — added quota-exceeded error case for Gemini API.
- **`kisan_mitra_chat` accepted any HTTP method** — it is decorated `@require_POST` but the page view `kisan_mitra_view` was entirely missing. Added the page view and wired it in `urls.py`.
- **`ai_enabled` context variable not passed to `farmer_dashboard`** — template referenced it, view didn't supply it. Fixed.
- **Input sanitisation** — added 1 000-character cap on chat messages.
- **`location` queryset in `home`** — now filtered to `is_available=True` and sorted alphabetically.

### `urls.py`
- Added the missing `kisan_mitra` page URL (`/kisan-mitra/`) that maps to `kisan_mitra_view`.

### `models.py`
- **Missing emoji entries** — added `mushroom`, `lettuce`, `soybean`, `mustard` to `CROP_EMOJI_MAP` (they existed in `SHELF_LIFE_DAYS_MAP` but not the emoji map).
- **`save()` used bare `self.crop_name.lower()`** — if `crop_name` was `None` this raised `AttributeError`. Fixed with `(self.crop_name or '').lower()`.

### `forms.py`
- **`village` field not included in `RegisterForm`** — `User` model has a `village` field that Kisan Mitra uses for personalisation; added it to the form and overrode `save()` to persist it.
- **`image` FileInput missing `accept`** — added `accept="image/*"` to restrict the browser file picker.
- **No server-side validation on quantity/price** — added `clean_quantity` and `clean_price` to reject zero or negative values.

### `apps.py`
- Added `default_auto_field = 'django.db.models.BigAutoField'` to suppress Django system-check warnings.

### `admin.py`
- `expiry_date` added to `readonly_fields` in `ProductAdmin` — it is auto-set on save; exposing it as editable could cause a mismatch.

### `kisan_mitra.html`
- **`split` filter used on a string literal** — Django templates do not have a `split` filter by default; replaced with explicit `<button>` tags to avoid `TemplateSyntaxError`.

---

## Deployment Notes

1. Set `DEBUG=False` and configure `ALLOWED_HOSTS` in production.
2. Use a proper database (PostgreSQL recommended): set `DATABASE_URL`.
3. Run `python manage.py collectstatic` and serve `/static/` via Nginx or a CDN.
4. Serve `/media/` separately (or use an object-storage bucket for product images).
5. Store `SECRET_KEY` and `GEMINI_API_KEY` in environment variables — never commit them.
6. Consider rate-limiting the `/kisan-mitra/chat/` endpoint (e.g. with `django-ratelimit`) to control Gemini API costs.

---

## License

MIT — free to use and adapt. Built with ❤️ for Indian farmers 🇮🇳
