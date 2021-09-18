import re

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class AnalogColor(models.Model):
    lightfastness_choices = [
        (1, 'I'),
        (2, 'II'),
        (3, 'III'),
    ]
    medium_choices = [
        ('acrylic', 'ACRYLIC'),
        ('oil', 'OIL'),
        ('watercolor', 'WATERCOLOR'),
        ('gouache', 'GOUACHE'),
        ('mixed', 'MIXED'),
        ('dye', 'DYE'),
        ('pastel', 'PASTEL'),
        ('colored_pencil', 'COLORED PENCIL'),
        ('graphite', 'GRAPHITE'),
        ('charcoal', 'CHARCOAL'),
        ('liquid_graphite', 'LIQUID GRAPHITE'),
    ]

    body = models.CharField(max_length=50, choices=[('heavy', 'HEAVY'), ('medium', 'MEDIUM'), ('light', 'LIGHT')])
    brandname = models.CharField(max_length=200)
    glossiness = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=100)
    image_url = models.URLField(max_length=1000)
    lightfastness = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)], choices=lightfastness_choices)
    medium = models.CharField(max_length=50, choices=medium_choices)
    name = models.CharField(max_length=200)
    series = models.CharField(max_length=200)
    tinting = models.IntegerField('tinting / pigmentation level', validators=[MinValueValidator(0), MaxValueValidator(100)])
    transparency = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)

    recipe_gloss = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    recipe_matte = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    recipe_medium = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    recipe_oil = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    recipe_thinner = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    recipe_water = models.IntegerField(validators=[MinValueValidator(0)], default=0)

    recipe_colors = models.ManyToManyField(
        'self',
        through='AnalogRecipe',
        related_name='used_in',
    )

    def __repr__(self):
        return f"<AnalogColor '{self.name}' ({self.medium})>"

    @property
    def recipe(self):
        full_recipe = {
            'colors': self.recipe_colors,
        }

        recipe_ingredients = {
            key_end.group(0): value for key, value in self.__dict__.items() if (key_end := re.search(r'(?<=recipe_)(.*)', key)) is not None and key_end != 'colors' and value > 0
        }

        full_recipe |= recipe_ingredients

        return full_recipe



class AnalogRecipe(models.Model):
    origin_color = models.ForeignKey(AnalogColor, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(AnalogColor, on_delete=models.CASCADE, related_name='ingredient')
    quantity = models.IntegerField(validators=[MinValueValidator(1)], default=1)
