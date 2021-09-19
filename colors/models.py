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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'body',
                    'brandname',
                    'glossiness',
                    'lightfastness',
                    'medium',
                    'name',
                    'series',
                    'tinting',
                    'transparency',
                ],
                name='unique_color',
            )
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

    _recipe_gloss = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    _recipe_matte = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    _recipe_medium = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    _recipe_oil = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    _recipe_thinner = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    _recipe_water = models.IntegerField(validators=[MinValueValidator(0)], default=0)

    _recipe_colors = models.ManyToManyField(
        'self',
        through='AnalogRecipe',
        related_name='used_in',
    )

    def __repr__(self):
        return f"<AnalogColor '{self.name}' ({self.medium})>"

    def __str__(self):
        return f"{self.name} ({self.medium})"

    @property
    def details(self):
        print(f'''
            {self.name}
            -----------
            image_url: {self.image_url}
            medium: {self.medium.upper()}
            body: {self.body.upper()}
            
            brandname: {self.brandname}
            series: {self.series}
            glossiness: {self.glossiness}
            lightfastness: {self.lightfastness}
            tinting: {self.tinting}
            transparency: {self.transparency}

            recipe:
                colors: {self.recipe['colors']}
                gloss: {self._recipe_gloss}
                matte: {self._recipe_matte}
                medium: {self._recipe_medium}
                oil: {self._recipe_oil}
                thinner: {self._recipe_thinner}
                water: {self._recipe_water}
            ''')

    @property
    def recipe(self):
        full_recipe = {
            'colors': [],
        }

        color_ingredients = [
            f'{color} x{quantity}' for color, quantity in zip(self._recipe_colors.all(), [ingredient.quantity for ingredient in AnalogRecipe.objects.filter(origin_color_id=self.id)])
        ]

        if len(color_ingredients) == 0:
            color_ingredients = [f'{self} x1']

        full_recipe['colors'] += color_ingredients

        additional_ingredients = {
            key_end.group(0): value for key, value in self.__dict__.items() if (key_end := re.search(r'(?<=_recipe_)(.*)', key)) is not None and key_end != 'colors' and value > 0
        }

        full_recipe |= additional_ingredients

        return full_recipe

    @recipe.setter
    def recipe(self, kwargs):
        """
            kwargs MUST include:
                colors: [(AnalogColor:color, integer:quantity)],
            kwargs MAY include:
                gloss: integer(0...100),
                matte: integer(0...100),
                medium: integer(0...100),
                oil: integer(0...100),
                thinner: integer(0...100),
                water: integer(0...100),
        """

        for color, quantity in kwargs.pop('colors'):
            r = AnalogRecipe(origin_color=self, ingredient=color, quantity=quantity)
            r.save()

        for key, value in kwargs.items():
            exec(f'self._recipe_{key} = {value}')

        self.save()

        return self.recipe


class AnalogRecipe(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['origin_color', 'ingredient'], name='unique_ingredients_for_each_color')
        ]

    origin_color = models.ForeignKey(AnalogColor, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(AnalogColor, on_delete=models.CASCADE, related_name='ingredient')
    quantity = models.IntegerField(validators=[MinValueValidator(1)], default=1)

    def __repr__(self):
        return f'{AnalogColor.objects.get(pk=self.origin_color_id).name} x {AnalogColor.objects.get(pk=self.ingredient_id).name}'

    def __str__(self):
        return f'{AnalogColor.objects.get(pk=self.origin_color_id).name}: {AnalogColor.objects.get(pk=self.ingredient_id).name} x{self.quantity}'
