import re

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class AnalogColor(models.Model):
    body_choices = [
        ('heavy', 'HEAVY'),
        ('medium', 'MEDIUM'),
        ('light', 'LIGHT'),
    ]
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
                    'opaqueness',
                    'series',
                    'tinting',
                    'thickness',
                ],
                name='unique_color',
            )
        ]

    body = models.CharField(max_length=50, choices=body_choices, default='heavy')
    brandname = models.CharField(max_length=200)
    glossiness = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=100)
    image_url = models.URLField(max_length=1000)
    lightfastness = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)], choices=lightfastness_choices, default=1)
    medium = models.CharField(max_length=50, choices=medium_choices)
    name = models.CharField(max_length=200)
    opaqueness = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=100)
    series = models.CharField(max_length=200)
    thickness = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=75)
    tinting = models.IntegerField('tinting / pigmentation level', validators=[MinValueValidator(0), MaxValueValidator(100)], default=100)

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


class DigitalColor(models.Model):
    name = models.CharField(max_length=200, blank=True)
    _integer_value = models.BigIntegerField(validators=[MinValueValidator(0), MaxValueValidator(int(0xffffffff))])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    '_integer_value'
                ],
                name='unique_digital_color',
            )
        ]

    def __repr__(self):
        return f"<DigitalColor {self.name or 'NO NAME SET'} {self.hex}"

    def __str__(self):
        return f"{self.name or 'NO NAME SET'} {self.rgba}"
    
    @property
    def rgba(self):
        i = self._integer_value

        r = i // 256 ** 3
        i %= 256 ** 3

        g = i // 256 ** 2
        i %= 256 ** 2

        b = i // 256
        i %= 256

        a = round(i / 256, 2)

        return (r, g, b, a)

    @rgba.setter
    def rgba(self, args: tuple):
        """
            args must be: (red: int, green: int, blue: int, alpha: float)
        """

        red, green, blue, alpha = args

        r = red * 256 ** 3
        g = green * 256 ** 2
        b = blue * 256
        a = int(alpha * 256) - 1

        self._integer_value = r + g + b + a
        self.save()

        return self.rgba

    @property
    def rgb(self):
        r, g, b, _ = self.rgba

        return (r, g, b)

    @rgb.setter
    def rgb(self, args: tuple):
        """
            args must be: (red: int, green: int, blue: int)
        """

        red, green, blue = args

        self.rgba = (red, green, blue, 1.0)

        return self.rgb

    @property
    def hsla(self):
        r, g, b, a = self.rgba

        r /= 255
        g /= 255
        b /= 255

        min_value = min(r, g, b)
        max_value = max(r, g, b)

        L = (min_value + max_value) / 2

        if min_value == max_value:
            s = 0
        else:
            if L <= 0.5:
                s = (max_value - min_value) / (max_value + min_value)
            else:
                s = (max_value - min_value) / (2.0 - max_value - min_value) 

        if r == max_value:
            h = (g - b) / (max_value - min_value)
        elif g == max_value:
            h = 2.0 + (b - r) / (max_value - min_value)
        else:
            h = 4.0 + (r - g) / (max_value - min_value)

        h *= 60
        if h < 0:
            h += 360

        return (int(h), f'{int(round(s, 2) * 100)}%', f'{int(round(L, 2) * 100)}%', a)

    @hsla.setter
    def hsla(self, args: tuple):
        """
            args must be: (hue(degrees): int, saturation: str(with or without '%') or int or float, luminance: str(with or without '%') or int or float, alpha: float)
        """

        h, s, L, a = args
        if type(s) is str:
            s = float(s.split('%')[0]) / 100
        else:
            s = float(s)
            if s > 1.0:
                s /= 100

        if type(L) is str:
            L = float(L.split('%')[0]) / 100
        else:
            L = float(L)
            if L > 1.0:
                L /= 100

        if s == 0:
            r = g = b = int(L * 255)
        else:
            if L < 0.5:
                L1 = L * (1.0 + s)
            else:
                L1 = L + s - L * s

            L2 = 2 * L - L1
            h /= 360
            r1 = h + 1/3
            if r1 > 1.0:
                r1 -= 1.0
            g1 = h
            b1 = h - 1/3
            if b1 < 0:
                b1 += 1.0

            #TODO check for accuracy when calculations are == to values
            ldict = {}

            for channel in ('r1', 'g1', 'b1'):
                if 6 * locals()[channel] < 1.0:
                    exec(f'{channel[0]} = {L2} + ({L1} - {L2}) * 6 * {locals()[channel]}', globals(), ldict)
                elif 2 * locals()[channel] < 1.0:
                    exec(f'{channel[0]} = {L1}', globals(), ldict)
                elif 3 * locals()[channel] < 2.0:
                    exec(f'{channel[0]} = {L2} + ({L1} - {L2}) * (2/3 - {locals()[channel]}) * 6', globals(), ldict)
                else:
                    exec(f'{channel[0]} = {L2}', globals(), ldict)

                r = ldict.get('r')
                g = ldict.get('g')
                b = ldict.get('b')

            r *= 255
            g *= 255
            b *= 255

        self.rgba = (int(r), int(g), int(b), a)
        self.save()

        return self.hsla

    @property
    def hsl(self):
        h, s, L, a = self.hsla

        return (h, s, L)

    @hsl.setter
    def hsl(self, args: tuple):
        """
            args must be: (hue(degrees): int, saturation: str(with or without '%') or int or float, luminance: str(with or without '%') or int or float)
        """

        h, s, L = args

        self.hsla = (h, s, L, 1.0)

        return self.hsl

    @property
    def cmyk(self):
        r, g, b = self.rgb

        r /= 255
        g /= 255
        b /= 255

        k = 1 - max(r, g, b)
        c = (1 - r - k) / (1 - k)
        m = (1 - g - k) / (1 - k)
        y = (1 - b - k) / (1 - k)

        k = int(k * 100)
        c = int(c * 100)
        m = int(m * 100)
        y = int(y * 100)

        return (f'{c}%', f'{m}%', f'{y}%', f'{k}%')

    @cmyk.setter
    def cmyk(self, args: tuple):
        """
            args must be (cyan, magenta, yellow, black) (all values: str(with or without '%') or int or float
        """

        c, m, y, k = args
        if type(c) is str:
            c = float(c.split('%')[0])
        else:
            c = float(c)

        if type(m) is str:
            m = float(m.split('%')[0])
        else:
            m = float(m)

        if type(y) is str:
            y = float(y.split('%')[0])
        else:
            y = float(y)

        if type(k) is str:
            k = float(k.split('%')[0])
        else:
            k = float(k)

        r = int(255 * (1 - c / 100) * (1 - k / 100))
        g = int(255 * (1 - m / 100) * (1 - k / 100))
        b = int(255 * (1 - y / 100) * (1 - k / 100))

        self.rgb = (r, g, b)
        self.save()

        return self.cmyk

    @property
    def hex(self):
        return hex(self._integer_value)

    @hex.setter
    def hex(self, hex_value: str):
        if hex_value.startswith('#'):
            hex_value = hex_value[1:]

        if hex_value.startswith('0x'):
            hex_value = hex_value[2:]
        hex_length = len(hex_value)

        if hex_length == 3 or hex_length == 4:
            hex_intermediary = []
            for i in range(hex_length):
                hex_intermediary.append(hex_value[i])
                hex_intermediary.append(hex_value[i])
            
            hex_value = ''.join(hex_intermediary)
            hex_length *= 2

        if hex_length == 6:
            self._integer_value = int(float.fromhex(f'{hex_value}ff'))
        elif hex_length == 8:
            self._integer_value = int(float.fromhex(hex_value))
        else:
            raise TypeError('hex value must be six or eight digits')

        self.save()

        return self.hex
