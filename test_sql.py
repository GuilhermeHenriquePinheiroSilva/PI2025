# test_sql.py

print("Iniciando teste de geração de SQL...")

try:
    from sqlalchemy.schema import CreateTable
    from sqlalchemy.dialects import mysql
    # Importamos os modelos para que eles sejam carregados
    from app.models import user_orm 
    from app.models import giftcard_orm

    # Pegamos o objeto da tabela a partir da classe ORM
    giftcard_table = giftcard_orm.RegisterGiftCardORM.__table__

    # Compilamos o comando CREATE TABLE para o dialeto mysql
    sql_statement = CreateTable(giftcard_table).compile(dialect=mysql.dialect())

    print("\n--- INÍCIO DO SQL GERADO ---")
    print(str(sql_statement))
    print("--- FIM DO SQL GERADO ---\n")

    if "id UUID" in str(sql_statement):
        print(">>> PROBLEMA CONFIRMADO: O SQL gerado ainda contém 'id UUID'.")
    elif "id CHAR" in str(sql_statement) or "id VARCHAR" in str(sql_statement):
        print(">>> BOA NOTÍCIA: O SQL gerado parece estar CORRETO ('id CHAR/VARCHAR').")
    else:
        print(">>> Análise do SQL gerado é inconclusiva, verifique o resultado acima.")

except Exception as e:
    print(f"\nOcorreu um erro durante o teste: {e}")

print("Teste de geração de SQL finalizado.")