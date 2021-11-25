from django.test import TestCase

from .models import AnalogColor, AnalogRecipe, DigitalColor


class AnalogColorTestCase(TestCase):
    def setUp(self):
        AnalogColor.objects.create(brandname='Golden', image_url='https://picsum.photos/200/300', medium='oil', name='Test Analog Color 0', series='1')


    def test_recipe_is_auto_created(self):
        ac = AnalogColor.objects.first()
        self.assertEqual(ac.recipe, '')
