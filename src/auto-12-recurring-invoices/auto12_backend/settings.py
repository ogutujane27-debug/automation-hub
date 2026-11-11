# settings.py snippets

INSTALLED_APPS = [
    # ... default Django apps ...
    'rest_framework',
    'corsheaders',
    'recurring_invoices', # My custom app for AUTO-12
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # Must be placed high up
    # ... default middlewares ...
    'django.middleware.common.CommonMiddleware',
]

# Allow local frontend and ngrok / production origins
CORS_ALLOW_ALL_ORIGINS = True # Or specify domains for production security

# SAP HANA Database Connection for IAL01_DEV
DATABASES = {
    'default': {
        'ENGINE': 'hdbcli.django',
        'NAME': 'IAL01_DEV',
        'USER': '<YOUR_HANA_USER>',
        'PASSWORD': '<YOUR_HANA_PASSWORD>',
        'HOST': '<YOUR_HANA_HOST_IP_OR_SERVER>',
        'PORT': '30015',
    }
}