from django.contrib import admin
from . import models

# Register your models here.
admin.site.register([model for model in models.__dict__.values() if isinstance(model, type)])
