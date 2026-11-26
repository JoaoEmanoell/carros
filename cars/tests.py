from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from cars.models import Car, Brand, CarInventory
from cars.forms import CarModelForm
from unittest.mock import patch
from openai import OpenAIError
from openai_api.client import get_car_ai_bio


class CarTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.porsche = Brand.objects.create(name='Porsche')
        cls.nissan = Brand.objects.create(name='Nissan')

        cls.car1 = Car.objects.create(
            model='911',
            brand=cls.porsche,
            factory_year=2017,
            model_year=2017,
            value=937945,
            bio='Porsche 911 de teste.'
        )

        cls.car2 = Car.objects.create(
            model='Skyline GT-R',
            brand=cls.nissan,
            factory_year=1999,
            model_year=1999,
            value=800000,
            bio='Nissan Skyline de teste.'
        )

        cls.user = User.objects.create_user(
            username='cliente_teste',
            password='Teste@123456'
        )

        cls.manager = User.objects.create_user(
            username='gerente_teste',
            password='Teste@123456'
        )

        permissions = Permission.objects.filter(
            content_type__app_label='cars',
            codename__in=[
                'add_car',
                'change_car',
                'delete_car',
            ]
        )

        cls.manager.user_permissions.add(*permissions)

    # LISTAGEM

    def test_car_list(self):

        response = self.client.get('/cars/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cars.html')
        self.assertContains(response, '911')
        self.assertContains(response, 'Skyline GT-R')

    # PESQUISA POR MODELO

    def test_search_by_model(self):

        response = self.client.get(
            '/cars/',
            {'search': 'Skyline'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['cars']),
            [self.car2]
        )

    # PESQUISA POR MARCA

    def test_search_by_brand(self):

        response = self.client.get(
            '/cars/',
            {'search': 'Porsche'}
        )

        self.assertEqual(
            list(response.context['cars']),
            [self.car1]
        )

    # FILTRO POR MARCA

    def test_brand_filter(self):

        response = self.client.get(
            '/cars/',
            {'brand': self.nissan.pk}
        )

        self.assertEqual(
            list(response.context['cars']),
            [self.car2]
        )

    # PREÇO MÍNIMO

    def test_min_price_filter(self):

        response = self.client.get(
            '/cars/',
            {'min_price': '900000'}
        )

        self.assertEqual(
            list(response.context['cars']),
            [self.car1]
        )

    # PREÇO MÁXIMO

    def test_max_price_filter(self):

        response = self.client.get(
            '/cars/',
            {'max_price': '850000'}
        )

        self.assertEqual(
            list(response.context['cars']),
            [self.car2]
        )

    # ORDENAÇÃO POR PREÇO

    def test_price_ordering(self):

        response = self.client.get(
            '/cars/',
            {'order': 'price_asc'}
        )

        self.assertEqual(
            list(response.context['cars']),
            [self.car2, self.car1]
        )

    # DETALHES DO VEÍCULO

    def test_car_detail(self):

        response = self.client.get(
            reverse('car_detail', args=[self.car1.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'car_detail.html')
        self.assertContains(response, '911')

    # VEÍCULO INEXISTENTE

    def test_car_not_found(self):

        response = self.client.get(
            reverse('car_detail', args=[999999])
        )

        self.assertEqual(response.status_code, 404)

    # USUÁRIO NÃO AUTENTICADO

    def test_anonymous_user_cannot_create(self):

        response = self.client.get('/new_car/')

        self.assertEqual(response.status_code, 302)

    # CLIENTE NÃO PODE CADASTRAR

    def test_customer_cannot_create(self):

        self.client.force_login(self.user)

        response = self.client.get('/new_car/')

        self.assertEqual(response.status_code, 403)

    # CLIENTE NÃO PODE EDITAR

    def test_customer_cannot_update(self):

        self.client.force_login(self.user)

        response = self.client.get(
            f'/car/{self.car1.pk}/update/'
        )

        self.assertEqual(response.status_code, 403)

    # CLIENTE NÃO PODE EXCLUIR

    def test_customer_cannot_delete(self):

        self.client.force_login(self.user)

        response = self.client.post(
            f'/car/{self.car1.pk}/delete/'
        )

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Car.objects.filter(pk=self.car1.pk).exists()
        )

    # GERENTE PODE ACESSAR CADASTRO

    def test_manager_can_access_create(self):

        self.client.force_login(self.manager)

        response = self.client.get('/new_car/')

        self.assertEqual(response.status_code, 200)

    # GERENTE PODE ACESSAR EDIÇÃO

    def test_manager_can_access_update(self):

        self.client.force_login(self.manager)

        response = self.client.get(
            f'/car/{self.car1.pk}/update/'
        )

        self.assertEqual(response.status_code, 200)

    # GERENTE PODE EXCLUIR

    def test_manager_can_delete(self):

        self.client.force_login(self.manager)

        response = self.client.post(
            f'/car/{self.car1.pk}/delete/'
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Car.objects.filter(pk=self.car1.pk).exists()
        )

    # VALIDAÇÃO DE PREÇO

    def test_invalid_car_price(self):

        form = CarModelForm(data={
            'model': 'Carro Teste',
            'brand': self.porsche.pk,
            'factory_year': 2020,
            'model_year': 2020,
            'value': 10000,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('value', form.errors)

    # VALIDAÇÃO DO ANO

    def test_invalid_factory_year(self):

        form = CarModelForm(data={
            'model': 'Carro Teste',
            'brand': self.porsche.pk,
            'factory_year': 1800,
            'model_year': 2020,
            'value': 50000,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('factory_year', form.errors)

    # PÁGINA 404 PERSONALIZADA

    def test_custom_404(self):

        with self.settings(DEBUG=False):

            response = self.client.get(
                '/pagina-inexistente/'
            )

            self.assertEqual(response.status_code, 404)
            self.assertTemplateUsed(response, '404.html')
        # CADASTRO DE VEÍCULO

    def test_manager_can_create_car(self):
        self.client.force_login(self.manager)

        response = self.client.post('/new_car/', {
            'model': 'Civic',
            'brand': self.porsche.pk,
            'factory_year': 2024,
            'model_year': 2024,
            'plate': 'ABC1D23',
            'value': 150000,
            'bio': 'Veículo de teste.',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Car.objects.filter(model='Civic').exists()
        )

    # EDIÇÃO DE VEÍCULO

    def test_manager_can_update_car(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            f'/car/{self.car1.pk}/update/',
            {
                'model': '911 Turbo',
                'brand': self.porsche.pk,
                'factory_year': 2017,
                'model_year': 2017,
                'value': 950000,
                'bio': 'Descrição atualizada.',
            }
        )

        self.assertEqual(response.status_code, 302)

        self.car1.refresh_from_db()

        self.assertEqual(self.car1.model, '911 Turbo')
        self.assertEqual(self.car1.value, 950000)

    # ESTOQUE APÓS CADASTRO

    def test_inventory_after_create(self):
        Car.objects.create(
            model='GT-R',
            brand=self.nissan,
            value=500000,
            bio='Veículo de teste.'
        )

        inventory = CarInventory.objects.latest('pk')

        self.assertEqual(inventory.cars_count, 3)
        self.assertEqual(inventory.cars_value, 2237945)

    # ESTOQUE APÓS EDIÇÃO

    def test_inventory_after_update(self):
        self.car1.value = 1000000
        self.car1.save()

        inventory = CarInventory.objects.latest('pk')

        self.assertEqual(inventory.cars_count, 2)
        self.assertEqual(inventory.cars_value, 1800000)

    # ESTOQUE APÓS EXCLUSÃO

    def test_inventory_after_delete(self):
        self.car1.delete()

        inventory = CarInventory.objects.latest('pk')

        self.assertEqual(inventory.cars_count, 1)
        self.assertEqual(inventory.cars_value, 800000)

    # ESTOQUE VAZIO

    def test_empty_inventory(self):
        Car.objects.all().delete()

        inventory = CarInventory.objects.latest('pk')

        self.assertEqual(inventory.cars_count, 0)
        self.assertEqual(inventory.cars_value, 0)

    # PAGINAÇÃO

    def test_pagination(self):
        for number in range(10):
            Car.objects.create(
                model=f'Veículo {number}',
                brand=self.nissan,
                value=50000,
                bio='Veículo de teste.'
            )

        response = self.client.get('/cars/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['cars']), 9)
        self.assertEqual(
            response.context['paginator'].count, 12
        )

    # PESQUISA SEM RESULTADOS

    def test_search_without_results(self):
        response = self.client.get('/cars/', {
            'search': 'VeiculoInexistente'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cars']), 0)

    # FILTRO COM PREÇO INVÁLIDO

    def test_invalid_price_filter(self):
        response = self.client.get('/cars/', {
            'min_price': 'abc'
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cars']), 2)

    # PÁGINA 403 PERSONALIZADA

    def test_custom_403(self):
        self.client.force_login(self.user)

        response = self.client.get('/new_car/')

        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, '403.html')

class CarAITests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.brand = Brand.objects.create(name='Porsche')

    @patch('cars.signals.get_car_ai_bio')
    def test_ai_generates_car_bio(self, mock_ai):

        mock_ai.return_value = 'Descrição gerada pela IA.'

        car = Car.objects.create(
            model='911',
            brand=self.brand,
            factory_year=2024,
            value=900000,
        )

        car.refresh_from_db()

        self.assertEqual(
            car.bio,
            'Descrição gerada pela IA.'
        )

        mock_ai.assert_called_once_with(
            model='911',
            brand='Porsche',
            year=2024,
        )

    @patch('cars.signals.get_car_ai_bio')
    def test_manual_bio_is_preserved(self, mock_ai):

        car = Car.objects.create(
            model='911',
            brand=self.brand,
            bio='Descrição manual.',
        )

        self.assertEqual(car.bio, 'Descrição manual.')

        mock_ai.assert_not_called()

    @patch('cars.signals.get_car_ai_bio')
    def test_car_is_saved_when_ai_fails(self, mock_ai):

        mock_ai.return_value = None

        car = Car.objects.create(
            model='911',
            brand=self.brand,
        )

        self.assertTrue(
            Car.objects.filter(pk=car.pk).exists()
        )

        self.assertFalse(car.bio)

    @patch('cars.signals.get_car_ai_bio')
    def test_existing_bio_is_preserved(self, mock_ai):

        car = Car.objects.create(
            model='911',
            brand=self.brand,
            bio='Descrição original.',
        )

        car.value = 950000
        car.save()
        car.refresh_from_db()

        self.assertEqual(car.bio, 'Descrição original.')

        mock_ai.assert_not_called()

    @patch.dict('os.environ', {'OPENAI_API_KEY': ''})
    @patch('openai_api.client.OpenAI')
    def test_ai_without_api_key(self, mock_client):

        result = get_car_ai_bio(
            model='911',
            brand='Porsche',
            year=2024,
        )

        self.assertIsNone(result)

        mock_client.assert_not_called()

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai_api.client.OpenAI')
    def test_ai_description_character_limit(self, mock_client):

        mock_client.return_value.responses.create.return_value.output_text = (
            'A' * 300
        )

        result = get_car_ai_bio(
            model='911',
            brand='Porsche',
            year=2024,
        )

        self.assertEqual(len(result), 250)

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('openai_api.client.OpenAI')
    def test_ai_api_error(self, mock_client):

        mock_client.return_value.responses.create.side_effect = (
            OpenAIError('Erro simulado')
        )

        result = get_car_ai_bio(
            model='911',
            brand='Porsche',
            year=2024,
        )

        self.assertIsNone(result)
