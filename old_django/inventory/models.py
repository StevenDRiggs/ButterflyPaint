from django.core.validators import MinValueValidator
from django.db import models

from colors.models import AnalogColor


class Inventory(models.Model):
    size_choices = [
        ('small_bottle', 'SMALL BOTTLE'),
        ('medium_bottle', 'MEDIUM BOTTLE'),
        ('large_bottle', 'LARGE BOTTLE'),
        ('extra_large_bottle', 'EXTRA LARGE BOTTLE'),
        ('small_jar', 'SMALL JAR'),
        ('medium_jar', 'MEDIUM JAR'),
        ('large_jar', 'LARGE JAR'),
        ('extra_large_jar', 'EXTRA LARGE JAR'),
        ('small_tube', 'SMALL TUBE'),
        ('medium_tube', 'MEDIUM TUBE'),
        ('large_tube', 'LARGE TUBE'),
        ('extra_large_tube', 'EXTRA LARGE TUBE'),
        ('pencil', 'PENCIL'),
        ('stick', 'STICK'),
        ('pen', 'PEN'),
        ('marker', 'MARKER'),
    ]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'color',
                    'size',
                ],
                name='unique_inventory_type',
            )
        ]

    color = models.ForeignKey(AnalogColor, on_delete=models.PROTECT)
    size = models.CharField(max_length=50, choices=size_choices)
    quantity_full = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    quantity_three_fourths = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    quantity_half = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    quantity_one_fourth = models.IntegerField(validators=[MinValueValidator(0)], default=0)

    @property
    def total(self):
        return sum([self.quantity_full, self.quantity_three_fourths, self.quantity_half, self.quantity_one_fourth])

    def __repr__(self):
        return f'<Inventory {self.color.name}-{self.color.medium} ({self.total} {self.size})>'

    def __str__(self):
        return f'{self.color.name}({self.color.medium}) ({self.size}): {self.total}'
