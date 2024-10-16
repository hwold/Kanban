# %%
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os.path import basename
from typing import List, Dict
import smtplib
import time
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from IPython.core.display import HTML
from IPython.display import display
import pandas as pd


SEND_TO = [
  'wlavieri@f1rst.com.br',
  'alex.falcao@f1rst.com.br',
  'felipe.chicralla@f1rst.com.br',
  'michael.silva@f1rst.com.br',
  'harald.neto@f1rst.com.br',
]


def send_email(receiver: List[str], copy: List[str], hidden_copy: List[str], subject: str, body: str, files: List[str]) -> None:
    msg = MIMEMultipart()

    sender = 'esmglobal@santander.com.br'

    msg['From'] = sender
    msg['Subject'] = subject

    msg['To'] = ", ".join(receiver)
    msg['Cc'] = ", ".join(copy)
    msg['Bcc'] = ", ".join(hidden_copy)

    receivers = receiver + copy + hidden_copy

    msg.attach(MIMEText(body, 'html'))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)

    try:
      print('Enviando e-mail...')
      server = smtplib.SMTP('srvsmtp2.santander.com.br')
      server.sendmail(sender, receivers, msg.as_string())

    except Exception as e:
      print(f'Falha ao enviar e-mail, aguardando 30s para tentar enviar novamente.\n{e}')
      time.sleep(30)
      server = smtplib.SMTP('srvsmtp2.santander.com.br')
      server.sendmail(sender, receivers, msg.as_string())


def get_data_from_view(view_name: str) -> List[Dict[str, any]]:
  url = f'https://sgd.paas.santanderbr.corp/api-integration-rpa/view?env={view_name}'

  response = requests.get(url, verify=False)
  response_json = response.json()['data']
  return response_json

# %%
def main():
  windows_view = 'vw_valida_CMDB_Vs_Infoblox'
  data = get_data_from_view(windows_view)
  df = pd.DataFrame(data)
  df.to_excel('Discovery_vs_Infoblox.xlsx',index=False)
  ########################################

  style = """
    <style>
        th {
            background-color: rgb(228, 228, 228);
        }

        th, td {
            width: 100px;
            text-align: center;
        }
        
        table {
            width: 100%;
            max-width: 540px;
            text-align: center;
        }

        table, th, td {
            border: 1px solid;
            border-collapse: collapse;
        }
    </style>
  """
    
  table_1 = f'''Quantidade de Vlan's no Infoblox e no Discovery: {len(df)-1}<br>
    Deste total, {df[df['divergência'] == 'ok'].__len__()} estão iguais(validado), {df[df['divergência'] == 'apenas no infoblox'].__len__()} estão apenas no Infoblox e {df[df['divergência'] == 'apenas no discovery'].__len__()} estão apenas no Discovery.<br>
    <br>
    {style}
    <table>
      <tr>
        <th>Total</th>
        <th>OK</th>
        <th>Infoblox</th>
        <th>Discovery</th>
      </tr>
      <tr>
        <td>{len(df)-1}</td>
        <td>{df[df['divergência'] == 'ok'].__len__()}</td>
        <td>{df[df['divergência'] == 'apenas no infoblox'].__len__()}</td>
        <td>{df[df['divergência'] == 'apenas no discovery'].__len__()}</td>
      </tr>
    </table> <br>Para mais detalhes, acesse o arquivo em anexo, utilize a coluna 'divergência' para identificar as diferenças.<br>
    Para saber o que está apenas no Infoblox, filtre a coluna 'divergência' por 'apenas no infoblox', para o que está apenas no Discovery, filtre por 'apenas no discovery'.<br>
    '''
  email_html = f'{table_1}'
  #display(HTML(email_html))
  send_email(
     subject='Validação entre Discovery e Inflobox',
     body=email_html,
     receiver=SEND_TO,
     copy=[],
     files=['Discovery_vs_Infoblox.xlsx'],
     hidden_copy=[],
  )
if __name__ == '__main__':
  main()