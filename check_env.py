import os
from dotenv import load_dotenv

# Tenta carregar o arquivo .env do diretório atual
load_dotenv()

# Pega o valor da variável de ambiente
token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

print("--- INICIANDO TESTE DE AMBIENTE ---")
if token:
    print(f"Sucesso! O token encontrado foi: {token}")
else:
    print("Falha! Não foi possível encontrar a variável MERCADOPAGO_ACCESS_TOKEN.")
    print("Por favor, verifique se o arquivo .env existe, está no lugar certo e com o nome correto.")
print("--- FIM DO TESTE ---")