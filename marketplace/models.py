from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    FARMER     = 'farmer'
    BUYER      = 'buyer'
    WAREHOUSE  = 'warehouse'
    WHOLESALER = 'wholesaler'

    ROLE_CHOICES = [
        (FARMER,     'Farmer'),
        (BUYER,      'Buyer'),
        (WAREHOUSE,  'Warehouse Operator'),
        (WHOLESALER, 'Wholesaler'),
    ]

    role    = models.CharField(max_length=12, choices=ROLE_CHOICES, default=BUYER, db_index=True)
    phone   = models.CharField(max_length=15, blank=True, default='')
    village = models.CharField(max_length=100, blank=True, default='')

    def is_farmer(self):     return self.role == self.FARMER
    def is_buyer(self):      return self.role == self.BUYER
    def is_warehouse(self):  return self.role == self.WAREHOUSE
    def is_wholesaler(self): return self.role == self.WHOLESALER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name        = 'User'
        verbose_name_plural = 'Users'


class Product(models.Model):
    DEFAULT_SHELF_DAYS = 7

    SHELF_LIFE_DAYS_MAP = {
        'corn':        3,
        'mushroom':    3,
        'lettuce':     3,
        'spinach':     3,
        'tomato':      5,
        'chilli':      5,
        'brinjal':     5,
        'cauliflower': 5,
        'mango':       5,
        'papaya':      6,
        'banana':      7,
        'peas':        7,
        'grapes':      7,
        'apple':       14,
        'carrot':      14,
        'orange':      14,
        'potato':      14,
        'sugarcane':   10,
        'onion':       30,
        'garlic':      60,
        'cotton':      180,
        'wheat':       180,
        'soybean':     180,
        'mustard':     180,
        'rice':        365,
    }

    CROP_EMOJI_MAP = {
        'tomato':      '🍅', 'potato':      '🥔', 'onion':       '🧅',
        'wheat':       '🌾', 'rice':        '🍚', 'corn':        '🌽',
        'carrot':      '🥕', 'mango':       '🥭', 'banana':      '🍌',
        'apple':       '🍎', 'garlic':      '🧄', 'spinach':     '🥬',
        'chilli':      '🌶️', 'cauliflower': '🥦', 'brinjal':     '🍆',
        'peas':        '🫛', 'sugarcane':   '🎋', 'cotton':      '🌿',
        'grapes':      '🍇', 'papaya':      '🧡', 'orange':      '🍊',
        'mushroom':    '🍄', 'lettuce':     '🥬', 'soybean':     '🌱',
        'mustard':     '🌻',
    }

    farmer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='products',
        limit_choices_to={'role': 'farmer'},
    )
    crop_name    = models.CharField(max_length=100, db_index=True)
    quantity     = models.DecimalField(max_digits=10, decimal_places=2, help_text='Quantity in KG')
    price        = models.DecimalField(max_digits=10, decimal_places=2, help_text='Price per KG in INR')
    location     = models.CharField(max_length=200, db_index=True)
    harvest_date = models.DateField()
    expiry_date  = models.DateField(
        null=True, blank=True,
        help_text='Auto-calculated on save from crop type + harvest date',
    )
    image        = models.ImageField(upload_to='products/', blank=True, null=True)
    is_available = models.BooleanField(default=True, db_index=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Auto-calculate expiry_date from harvest_date + crop shelf life."""
        today = timezone.now().date()
        try:
            base_date  = self.harvest_date if self.harvest_date else today
            crop_key   = (self.crop_name or '').lower().strip()
            shelf_days = self.SHELF_LIFE_DAYS_MAP.get(crop_key, self.DEFAULT_SHELF_DAYS)
            self.expiry_date = base_date + timedelta(days=shelf_days)
        except Exception:
            self.expiry_date = today + timedelta(days=self.DEFAULT_SHELF_DAYS)
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def days_until_spoilage(self) -> int:
        try:
            ref = self.expiry_date or (
                self.harvest_date + timedelta(days=self.DEFAULT_SHELF_DAYS)
                if self.harvest_date else None
            )
            return (ref - timezone.now().date()).days if ref else 0
        except Exception:
            return 0

    @property
    def urgency_level(self) -> str:
        days = self.days_until_spoilage
        if days <= 0:  return 'expired'
        if days <= 2:  return 'critical'
        if days <= 4:  return 'warning'
        return 'fresh'

    @property
    def crop_emoji(self) -> str:
        key = (self.crop_name or '').lower().strip()
        return self.CROP_EMOJI_MAP.get(key, '🌿')

    def __str__(self):
        return f"{self.crop_name} — {self.quantity} kg @ ₹{self.price}/kg ({self.farmer.username})"

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Product'
        verbose_name_plural = 'Products'
        indexes = [
            models.Index(fields=['crop_name', 'location']),
            models.Index(fields=['harvest_date']),
            models.Index(fields=['expiry_date']),
        ]