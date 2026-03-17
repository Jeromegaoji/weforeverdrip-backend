from django.contrib import admin

# Dashboard app is API-only — no models to register.
# All admin functionality is exposed via REST endpoints in dashboard/urls.py
# Endpoints are protected with IsStaffOrAdmin permission and serve dashboard analytics and management features.
