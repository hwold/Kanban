# %%
#    table = Table(
#        tabela_nome, metadata, *columns,
#        PrimaryKeyConstraint(*chave_primaria, name=f"pk_{tabela_nome}"),
#        extend_existing=True
#    )

# %%
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData, Column, String, DateTime, Integer
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
import os
from sqlalchemy.sql import text
import urllib.parse
# Configurações do banco de dados SQL Server
def get_database_engine():
  print('EXECUTANDO NO BANCO DE PROD!')
  username = 'svc_p_ito_01'
  password = urllib.parse.quote('_c4u_6_XHE4y1@Cg')
  server = 'SQLPRD0007AG'
  port = 8000
  database = 'dbsgdt1'
  print(f'DB: Usuário: "{username}", Password: "{password}", Server: "{server}", Porta: "{port}", Database: "{database}"')
  connection_string = f'mssql+pymssql://{username}:{password}@{server}:{port}/{database}?charset=utf8'
  engine = create_engine(connection_string)
  return engine
engine = get_database_engine()
metadata = MetaData()
def ler_arquivo(file_path, file_extension):
   # Ler o arquivo de acordo com a extensão informada
   if file_extension == 'csv':
       df = pd.read_csv(file_path)
       df.dropna(how='any', inplace=True)  # Remover linhas vazias
   elif file_extension in ['xls', 'xlsx']:
       df = pd.read_excel(file_path)
       df.dropna(how='any', inplace=True)  # Remover linhas vazias
   elif file_extension == 'json':
       df = pd.read_json(file_path)
       df.dropna(how='any', inplace=True)
   else:
       raise ValueError(f"Tipo de arquivo '{file_extension}' não suportado.")
   return df
def converter_tipos(df, tipos_colunas):
   # Converter colunas de string para datetime, se necessário
   for coluna, tipo in tipos_colunas.items():
       if tipo == DateTime:
           df[coluna] = pd.to_datetime(df[coluna], errors='coerce')  # Converte a coluna para datetime, com erro tratado
   return df
def criar_tabela(df, tabela_nome, tipos_colunas):
   # Criar a tabela com os tipos de dados especificados, sem definir chave primária
   columns = []
   for column_name in df.columns:
       if column_name in tipos_colunas:
           tipo = tipos_colunas[column_name]
       else:
           tipo = String  # Tipo padrão como String
       columns.append(Column(column_name, tipo))
   table = Table(tabela_nome, metadata, *columns, extend_existing=True)
   metadata.create_all(engine)  # Cria a tabela no banco de dados se não existir
   return table
def tabela_existe(tabela_nome):
   # Verificar se a tabela já existe no banco de dados
   insp = inspect(engine)
   return insp.has_table(tabela_nome)
def upsert_dados(df, tabela_nome, chave_unica):
   try:
       # Renomear colunas do DataFrame para remover espaços
       df.columns = df.columns.str.replace(' ', '')
       df = df.dropna(how='any')  # Remover linhas vazias
       conn = engine.connect()
       trans = conn.begin()  # Iniciar uma transação para melhorar a performance
       # Dividir os registros entre os que precisam ser atualizados e os que serão inseridos
       registros_para_inserir = []
       registros_para_atualizar = []
       if chave_unica:
           # Verificar quais registros já existem no banco e separar para insert ou update
           filtro_cols = [f"{chave}" for chave in chave_unica]
           where_clause = " AND ".join([f"{col} = :{col}" for col in filtro_cols])
           for index, row in df.iterrows():
               filtro = {chave.replace(' ', '_'): row[chave] for chave in chave_unica}
               query = text(f"SELECT COUNT(*) FROM {tabela_nome} WHERE {where_clause}")
               resultado = conn.execute(query, filtro).scalar()
               if resultado > 0:
                   registros_para_atualizar.append(row.to_dict())
               else:
                   registros_para_inserir.append(row.to_dict())
               # Adicionar feedback de progresso
               if index % 100 == 0:
                   print(f"Processados {index + 1} registros...")
               elif index > 14730:
                    break

       # Realizar inserção em lote dos registros que não existem
       if registros_para_inserir:
           print(f"Iniciando inserção de {len(registros_para_inserir)} registros...")
           insert_columns = ", ".join([f"{col}" for col in df.columns])
           insert_values = ", ".join([f":{col}" for col in df.columns])
           insert_query = text(f"INSERT INTO {tabela_nome} ({insert_columns}) VALUES ({insert_values})")
           conn.execute(insert_query, registros_para_inserir)
           conn.commit()  # Confirmar a transação após a inserção em lote
           print(f"Inserção de {len(registros_para_inserir)} registros concluída e confirmada.")

       # Iniciar uma nova transação para as atualizações
       # Realizar atualização dos registros que já existem
       if registros_para_atualizar:
           print(f"Iniciando atualização de {len(registros_para_atualizar)} registros...")
           for registro in registros_para_atualizar:
               dados_para_atualizar = {col: registro[col] for col in df.columns if col not in chave_unica}
               update_clause = ", ".join([f"{col} = :{col}" for col in dados_para_atualizar.keys()])
               where_clause = " AND ".join([f"{col} = :{col}" for col in chave_unica])
               update_query = text(f"UPDATE {tabela_nome} SET {update_clause} WHERE {where_clause}")
               conn.execute(update_query, registro)
           conn.commit()  # Confirmar a transação após as atualizações
           print(f"Atualização de {len(registros_para_atualizar)} registros concluída e confirmada.")
       print(f"Dados inseridos/atualizados na tabela '{tabela_nome}' com sucesso.")
   except SQLAlchemyError as e:
       trans.rollback()  # Reverter a transação em caso de erro
       print(f"Erro ao inserir/atualizar dados: {e}")
   finally:
       conn.close()
def processar_arquivo(file_path, file_extension, tabela_nome, tipos_colunas, chave_unica=None):
   # Ler o arquivo baixado
   df = ler_arquivo(file_path, file_extension)
   # Converter tipos de colunas conforme necessário
   df = converter_tipos(df, tipos_colunas)
   # Verificar se a tabela já existe, se não, cria a tabela
   if not tabela_existe(tabela_nome):
       criar_tabela(df, tabela_nome, tipos_colunas)
   # Inserir ou atualizar os dados lidos no banco de dados
   upsert_dados(df, tabela_nome, chave_unica)
# Exemplo de uso
if __name__ == "__main__":
   arquivo_caminho = r"C:\Users\t781646\Downloads\certificados_telecom.json"  # Caminho do arquivo
   extensao_arquivo = "json"  # Extensão do arquivo (csv, xls, xlsx)
   nome_tabela = "EXT_certificados_telecom"  # Nome da tabela no banco de dados
   tipos_colunas = {
    "vs_cert_url": String,
    "vs_expiration_string": String,
    "vs_expiration_days": String,
    "vs_cert": String,
    "vs_vsname": String,
    "vs_ip": String,
    "el_hostname": String,
    "el_ip": String,
    "el_fqdn": String,
    "vs_oper_status": String,
    "vs_adm_status": String,
    "vs_cert_alarm": String,
    "vs_update": DateTime,
    "TIPO": String,
   }  # Definir tipos de colunas específicos
   # Não definir chave primária, mas ainda podemos ter uma chave única para o upsert, se necessário
   chave_unica = ["vs_cert_url"]
   processar_arquivo(arquivo_caminho, extensao_arquivo, nome_tabela, tipos_colunas, chave_unica)



