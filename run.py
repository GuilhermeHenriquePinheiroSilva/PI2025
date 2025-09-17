# run.py

import subprocess
import sys
import os

print("Iniciando a automação do projeto GoGift...")

def run_command(command, message):
    """
    Função para rodar um comando e checar por erros.
    """
    print(f"\n--- {message} ---")
    try:
        subprocess.run(command, check=True, shell=True)
        print("Sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o comando: {e}")
        return False
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        return False

# 1. Criar o ambiente virtual usando 'py'
if not run_command("py -m venv venv", "Criando/Checando ambiente virtual"):
    print("Não foi possível criar o ambiente virtual. Saindo.")
    sys.exit(1)

# Caminho para o executável do Python dentro do venv
venv_python = os.path.join("venv", "Scripts", "python") if sys.platform == "win32" else os.path.join("venv", "bin", "python")

# 2. Instalar as dependências
if not run_command(f"{venv_python} -m pip install -r requirements.txt", "Instalando dependências"):
    print("Não foi possível instalar as dependências. Saindo.")
    sys.exit(1)

# 3. Rodar o init_db.py. Ele irá falhar se o banco de dados não existir.
print("\n--- Inicializando o banco de dados (criando tabelas) ---")
try:
    subprocess.run(f"{venv_python} -m app.database.init_db", check=True, shell=True)
    print("Sucesso!")
except subprocess.CalledProcessError as e:
    print(f"Erro ao executar o comando: {e}")
    print("\nERRO: O banco de dados 'prjgogift' não foi encontrado.")
    print("Por favor, crie-o manualmente no XAMPP e tente novamente.")
    sys.exit(1)

# 4. Iniciar o servidor Uvicorn
print("\n--- Iniciando o servidor Uvicorn ---")
try:
    subprocess.run(f"{venv_python} -m uvicorn app.main:app --reload", check=True, shell=True)
except KeyboardInterrupt:
    print("\nServidor Uvicorn encerrado.")
except Exception as e:
    print(f"Ocorreu um erro ao iniciar o Uvicorn: {e}")

print("\nProcesso de automação finalizado.")