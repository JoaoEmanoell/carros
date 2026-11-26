
from django import forms
from cars.models import Car


class CarModelForm(forms.ModelForm):

    class Meta:
        model = Car
        fields = '__all__'

        labels = {
            'model': 'Modelo',
            'brand': 'Marca',
            'factory_year': 'Ano de fabricação',
            'model_year': 'Ano do modelo',
            'plate': 'Placa',
            'value': 'Preço (R$)',
            'photo': 'Fotografia do veículo',
            'bio': 'Descrição do veículo',
        }

        widgets = {
            'model': forms.TextInput(attrs={
                'placeholder': 'Ex.: Golf GTI',
            }),

            'factory_year': forms.NumberInput(attrs={
                'placeholder': 'Ex.: 2026',
            }),

            'model_year': forms.NumberInput(attrs={
                'placeholder': 'Ex.: 2026',
            }),

            'plate': forms.TextInput(attrs={
                'placeholder': 'Ex.: ABC1D23',
            }),

            'value': forms.NumberInput(attrs={
                'placeholder': 'Ex.: 150000',
                'step': '0.01',
            }),

            'photo': forms.ClearableFileInput(attrs={
                'accept': 'image/*',
            }),

            'bio': forms.Textarea(attrs={
                'placeholder': 'Descreva as características do veículo...',
                'rows': 5,
            }),
        }

        help_texts = {
            'photo': 'Selecione uma fotografia do veículo.',
            'bio': 'Informe os detalhes e características do veículo.',
            'value': 'Informe o valor do veículo em reais.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['brand'].empty_label = 'Selecione uma marca'

    def clean_value(self):
        value = self.cleaned_data.get('value')

        if value is not None and value < 20000:
            raise forms.ValidationError(
                'O valor mínimo do veículo deve ser de R$ 20.000,00.'
            )

        return value

    def clean_factory_year(self):
        factory_year = self.cleaned_data.get('factory_year')

        if factory_year is not None and factory_year < 1890:
            raise forms.ValidationError(
                'O ano de fabricação mínimo deve ser 1890.'
            )

        return factory_year

    def clean_plate(self):
        plate = self.cleaned_data.get('plate')

        if plate:
            return plate.strip().upper()

        return plate
