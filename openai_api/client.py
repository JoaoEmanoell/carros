from openai import OpenAI

def get_car_ai_bio(model, brand, year):
    client = OpenAI()

    prompt = f"""
    Me mostre uma descrição de venda para o carro
    {brand} {model}, ano {year}, em no máximo
    250 caracteres. Não invente características.
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        max_output_tokens=150,
    )

    return response.output_text.strip()[:250]