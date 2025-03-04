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
]

DEVELOPED_APPS=[
  'user',
]

INSTALLED_APPS = BASE_APPS + THIRD_PARTY_APPS + DEVELOPED_APPS