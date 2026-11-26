import math

from cars.models import Car, Brand
from cars.forms import CarModelForm
from django.db.models import Q, F
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView,
)


class CarsListView(ListView):
    model = Car
    template_name = 'cars.html'
    context_object_name = 'cars'
    paginate_by = 9

    def get_queryset(self):
        cars = super().get_queryset().select_related('brand')

        search = self.request.GET.get('search', '').strip()
        brand = self.request.GET.get('brand', '')
        min_price = self.request.GET.get('min_price', '')
        max_price = self.request.GET.get('max_price', '')
        order = self.request.GET.get('order', '')

        # Busca por modelo ou marca
        if search:
            cars = cars.filter(
                Q(model__icontains=search) |
                Q(brand__name__icontains=search)
            )

        # Filtro por marca
        if brand.isascii() and brand.isdigit() and len(brand) <= 10:
            cars = cars.filter(brand_id=int(brand))

        # Filtro por preço mínimo
        if min_price:
            try:
                minimum = float(min_price.replace(',', '.'))

                if math.isfinite(minimum) and minimum >= 0:
                    cars = cars.filter(value__gte=minimum)

            except ValueError:
                pass

        # Filtro por preço máximo
        if max_price:
            try:
                maximum = float(max_price.replace(',', '.'))

                if math.isfinite(maximum) and maximum >= 0:
                    cars = cars.filter(value__lte=maximum)

            except ValueError:
                pass

        # Opções de ordenação
        ordering = {
            'price_asc': F('value').asc(nulls_last=True),
            'price_desc': F('value').desc(nulls_last=True),
            'year_desc': F('factory_year').desc(nulls_last=True),
            'year_asc': F('factory_year').asc(nulls_last=True),
            'model_asc': 'model',
            'model_desc': '-model',
        }

        cars = cars.order_by(
            ordering.get(order, 'model'),
            'pk'
        )

        return cars

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['brands'] = Brand.objects.order_by('name')

        context['selected_brand'] = self.request.GET.get(
            'brand', ''
        )

        context['selected_order'] = self.request.GET.get(
            'order', ''
        )

        return context


@method_decorator(login_required(login_url='/login/'), name='dispatch')
@method_decorator(permission_required('cars.add_car', raise_exception=True), name='dispatch')
class NewCarteView(CreateView):
    model = Car
    form_class = CarModelForm
    template_name = 'new_car.html'
    success_url = '/cars/'


class CarDetailView(DetailView):
    model = Car
    template_name = 'car_detail.html'


@method_decorator(login_required(login_url='/login/'), name='dispatch')
@method_decorator(permission_required('cars.change_car', raise_exception=True), name='dispatch')
class CarUpdateView(UpdateView):
    model = Car
    form_class = CarModelForm
    template_name = 'car_update.html'

    def get_success_url(self):
        return reverse_lazy('car_detail', kwargs={'pk': self.object.pk})

@method_decorator(login_required(login_url='/login/'), name='dispatch')
@method_decorator(permission_required('cars.delete_car', raise_exception=True), name='dispatch')
class CarDeleteView(DeleteView):
    model = Car
    template_name = 'car_delete.html'
    success_url = '/cars/'