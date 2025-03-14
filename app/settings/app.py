BASE_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS=[
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist'
]


DEVELOPED_APPS=[
  'user',
  'products',
  'shop',
]

INSTALLED_APPS = BASE_APPS + THIRD_PARTY_APPS + DEVELOPED_APPS

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'EXCEPTION_HANDLER':'app.utils.exception.custom_exception_handler'
}