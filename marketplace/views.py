import json
import os
import urllib.request
import urllib.parse
import urllib.error

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Product, User
from .forms import RegisterForm, LoginForm, ProductForm


# ---------------------------------------------------------------------------
# Gemini API helpers
# ---------------------------------------------------------------------------

GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))
GEMINI_MODEL   = 'gemini-1.5-flash'


def _get_gemini_url():
    """Build Gemini URL at call-time so a late-set env var is picked up."""
    key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))
    return (
        f'https://generativelanguage.googleapis.com/v1beta/models/'
        f'{GEMINI_MODEL}:generateContent?key={key}'
    ), key


def get_gemini_analysis(prompt: str) -> str:
    url, key = _get_gemini_url()

    if not key or key in ('', 'PASTE_YOUR_GEMINI_API_KEY_HERE'):
        return (
            'AI analysis unavailable — API key not configured. '
            'Set GEMINI_API_KEY in your environment or settings.py.'
        )

    try:
        payload = json.dumps({
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature':     0.65,
                'maxOutputTokens': 220,
                'topP':            0.9,
            },
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )

        with urllib.request.urlopen(req, timeout=12) as response:
            data = json.loads(response.read().decode('utf-8'))
            # Guard against unexpected response shapes
            return (
                data.get('candidates', [{}])[0]
                    .get('content', {})
                    .get('parts', [{}])[0]
                    .get('text', 'No analysis returned.')
                    .strip()
            )

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        if 'API_KEY_INVALID' in error_body or e.code == 400:
            return 'AI analysis unavailable — API key is invalid.'
        if e.code == 429:
            return 'AI quota exceeded. Please try again later.'
        return f'Gemini API error ({e.code}). Please try again in a few minutes.'

    except urllib.error.URLError:
        return 'Could not reach the AI service. Check your internet connection.'

    except (KeyError, IndexError, json.JSONDecodeError):
        return 'Received an unexpected response from the AI. Please try again.'

    except Exception:
        return 'Market analysis is temporarily unavailable. Please try again.'


def get_kisan_mitra_response(user_message: str, farmer_name: str, farmer_village: str) -> str:
    system_context = (
        f'You are Kisan Mitra, a friendly and knowledgeable agricultural assistant '
        f'for Indian farmers. The farmer you are helping is named {farmer_name} '
        f'from {farmer_village or "India"}. '
        'Respond in simple Hindi-English (Hinglish) or whichever language the farmer uses. '
        'Keep answers short, practical, and jargon-free. '
        'Topics you help with: crop prices, storage tips, government schemes '
        '(PM-KISAN, eNAM, PMFBY, Kisan Credit Card), pest control, weather advice, '
        'and how to use KisanBazaar to sell crops.'
    )
    full_prompt = f'{system_context}\n\nFarmer says: {user_message}'
    return get_gemini_analysis(full_prompt)


# ---------------------------------------------------------------------------
# AI views
# ---------------------------------------------------------------------------

@login_required
@require_GET
def roi_predictor(request, pk):
    product = get_object_or_404(Product, pk=pk, farmer=request.user)

    prompt = (
        'You are an expert Indian agricultural commodity market analyst. '
        f'A farmer in {product.location} has {product.quantity} kg of '
        f'{product.crop_name} listed at ₹{product.price} per kg. '
        f'It was harvested on {product.harvest_date} and expires around {product.expiry_date}. '
        'In exactly 2 short sentences, give a realistic market ROI forecast '
        'and one actionable selling tip suited for a small Indian farmer. '
        'Write in plain, simple language. No bullet points.'
    )

    analysis = get_gemini_analysis(prompt)

    return JsonResponse({
        'success':    True,
        'crop':       product.crop_name,
        'product_id': product.id,
        'analysis':   analysis,
    })


@login_required
@require_POST
def kisan_mitra_chat(request):
    try:
        body         = json.loads(request.body)
        user_message = body.get('message', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'error': 'Invalid request body.'}, status=400)

    if not user_message:
        return JsonResponse({'success': False, 'error': 'Message cannot be empty.'}, status=400)

    if len(user_message) > 1000:
        return JsonResponse({'success': False, 'error': 'Message too long (max 1000 chars).'}, status=400)

    reply = get_kisan_mitra_response(
        user_message,
        farmer_name=request.user.username,
        farmer_village=getattr(request.user, 'village', ''),
    )

    return JsonResponse({'success': True, 'reply': reply})


# ---------------------------------------------------------------------------
# Public / auth views
# ---------------------------------------------------------------------------

def home(request):
    if request.user.is_authenticated and request.user.is_farmer():
        return redirect('farmer_dashboard')

    query    = request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip()

    products = Product.objects.select_related('farmer').filter(is_available=True)

    if query:
        products = products.filter(crop_name__icontains=query)
    if location:
        products = products.filter(location__icontains=location)

    product_data = [
        {
            'product': p,
            'days':    p.days_until_spoilage,
            'urgency': p.urgency_level,
            'emoji':   p.crop_emoji,
        }
        for p in products
    ]

    locations = (
        Product.objects
        .filter(is_available=True)
        .values_list('location', flat=True)
        .distinct()
        .order_by('location')
    )

    total_farmers  = User.objects.filter(role=User.FARMER).count()
    total_listings = Product.objects.filter(is_available=True).count()
    total_buyers   = User.objects.filter(role=User.BUYER).count()

    return render(request, 'marketplace/home.html', {
        'product_data':   product_data,
        'query':          query,
        'location':       location,
        'locations':      locations,
        'total_farmers':  total_farmers,
        'total_listings': total_listings,
        'total_buyers':   total_buyers,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! 🎉')
            return redirect('farmer_dashboard' if user.is_farmer() else 'home')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'marketplace/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}! 👋')
                return redirect('farmer_dashboard' if user.is_farmer() else 'home')
            messages.error(request, 'Wrong username or password.')
    else:
        form = LoginForm()

    return render(request, 'marketplace/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


# ---------------------------------------------------------------------------
# Farmer-only views
# ---------------------------------------------------------------------------

@login_required
def farmer_dashboard(request):
    if not request.user.is_farmer():
        messages.error(request, 'Only farmers can access this page.')
        return redirect('home')

    my_products  = Product.objects.filter(farmer=request.user).select_related('farmer')
    product_data = [
        {
            'product': p,
            'days':    p.days_until_spoilage,
            'urgency': p.urgency_level,
            'emoji':   p.crop_emoji,
        }
        for p in my_products
    ]

    # Expose ai_enabled flag so templates can show correct status
    ai_enabled = bool(
        getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))
    )

    return render(request, 'marketplace/farmer_dashboard.html', {
        'product_data':   product_data,
        'total_products': my_products.count(),
        'ai_enabled':     ai_enabled,
    })


@login_required
def add_product(request):
    if not request.user.is_farmer():
        messages.error(request, 'Only farmers can add products.')
        return redirect('home')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product        = form.save(commit=False)
            product.farmer = request.user
            product.save()
            messages.success(request, f'✅ {product.crop_name} listed successfully!')
            return redirect('farmer_dashboard')
        messages.error(request, 'Please fill all fields correctly.')
    else:
        form = ProductForm()

    return render(request, 'marketplace/add_product.html', {'form': form})


@login_required
def delete_product(request, pk):
    # Accept GET or POST — guard with ownership check only
    try:
        product = Product.objects.get(pk=pk, farmer=request.user)
        name    = product.crop_name
        product.delete()
        messages.success(request, f'{name} removed from your listings.')
    except Product.DoesNotExist:
        messages.error(request, 'Product not found or permission denied.')
    return redirect('farmer_dashboard')


# ---------------------------------------------------------------------------
# Kisan Mitra page
# ---------------------------------------------------------------------------

@login_required
def kisan_mitra_view(request):
    if not request.user.is_farmer():
        messages.error(request, 'Kisan Mitra is available for farmers only.')
        return redirect('home')

    ai_enabled = bool(
        getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY', ''))
    )
    return render(request, 'marketplace/kisan_mitra.html', {'ai_enabled': ai_enabled})