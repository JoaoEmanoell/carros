
import os
import logging

from openai import OpenAI, OpenAIError


logger = logging.getLogger(__name__)


def get_car_ai_bio(model, brand, year):

    api_key = os.getenv('OPENAI_API_KEY', '').strip()

    if not api_key:
        return None

    year_text = f'ano {year}' if year else 'ano não informado'

    prompt = f"""
    Crie uma descrição comercial para o seguinte veículo:

    Marca: {brand}
    Modelo: {model}
    Ano: {year_text}

    Regras:
    - Escreva em português do Brasil.
    - Utilize no máximo 250 caracteres.
    - Use uma linguagem profissional e atrativa.
    - Não invente características do veículo.
    - Não invente informações sobre conservação,
      quilometragem ou equipamentos.
    - Retorne somente a descrição.
    """

    try:
        client = OpenAI(
            api_key=api_key,
            timeout=10.0,
            max_retries=0,
        )

        response = client.responses.create(
            model='gpt-4.1-mini',
            input=prompt,
            max_output_tokens=150,
        )

        description = (response.output_text or '').strip()

        return description[:250] or None

    except OpenAIError as error:
        logger.warning(
            'Falha ao gerar descrição com IA: %s',
            type(error).__name__,
        )

        return None
