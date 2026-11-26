
from django.db.models.signals import pre_save, post_save, post_delete
from django.db.models import Sum
from django.dispatch import receiver

from .models import Car, CarInventory
from openai_api.client import get_car_ai_bio


def car_inventory_update():

    cars_count = Car.objects.count()

    cars_value = Car.objects.aggregate(
        total_value=Sum('value')
    )['total_value'] or 0

    CarInventory.objects.create(
        cars_count=cars_count,
        cars_value=cars_value
    )


@receiver(pre_save, sender=Car)
def car_pre_save(sender, instance, **kwargs):

    if kwargs.get('raw'):
        return

    update_fields = kwargs.get('update_fields')

    if update_fields is not None and 'bio' not in update_fields:
        return

    if not (instance.bio or '').strip():

        description = get_car_ai_bio(
            model=instance.model,
            brand=instance.brand.name,
            year=instance.factory_year,
        )

        if description:
            instance.bio = description


@receiver(post_save, sender=Car)
def car_post_save(sender, instance, **kwargs):

    if not kwargs.get('raw'):
        car_inventory_update()


@receiver(post_delete, sender=Car)
def car_post_delete(sender, instance, **kwargs):

    car_inventory_update()
