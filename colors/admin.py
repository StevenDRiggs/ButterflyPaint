from django.contrib import admin

from .models import AnalogColor
from .models import AnalogRecipe


class AnalogColorAdmin(admin.ModelAdmin):
    fields = [
       'name',
       'image_url',
       'medium',
       'body',
       'brandname',
       'glossiness',
       'lightfastness',
       'series',
       'tinting',
       'transparency',
       'recipe_gloss',
       'recipe_matte',
       'recipe_medium',
       'recipe_oil',
       'recipe_thinner',
       'recipe_water',
    ]


admin.site.register(AnalogColor, AnalogColorAdmin)
admin.site.register(AnalogRecipe)
