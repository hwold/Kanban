from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
from os.path import basename
from typing import List, Dict
import smtplib
import time
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


SEND_TO = [
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


def get_data_from_view():
  url = f'https://sgd.paas.santanderbr.corp/api-integration-rpa/view?env=vw_valida_Cmdb_sccm_linux'

  response = requests.get(url, verify=False)
  response_json = response.json()['data']
  return response_json

def main():
    data = get_data_from_view()
    df = pd.json_normalize(data)

    windows_total = df[df['SCCM_HOST'] != 'null'].__len__()

    windows_atualizado= df[df['Windows atualizado'] == 'Windows Atualizado'].__len__()
    windows_desatualizado = df[df['Windows atualizado'] == 'Windows desatualizado'].__len__()
    
    linux_total = df[df['LINUX_HOST'] != 'null'].__len__()
    linux_atualizado= df[df['Linux atualizado'] == 'Linux Atualizado'].__len__()
    linux_desatualizado = df[df['Linux atualizado'] == 'Linux desatualizado'].__len__()
    
    total_geral = len(df)
    satellite = df[df['status'] == 'Apenas Satellite'].__len__()
    CMDB = df[df['status'] == 'Apenas CMDB'].__len__()
    SCCM = df[df['status'] == 'Apenas SCCM'].__len__()
    validacao_ok = df[df['status'] == 'Validação OK'].__len__()

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
            max-width: 756px;
            text-align: center;
        }

        table, th, td {
            border: 1px solid;
            border-collapse: collapse;
        }
    </style>
    """
    
    body = f'''
        {style}
        <p>Quantidade total de servidores no SCCM: {windows_total}.<br>
        Deste total, {windows_atualizado} estão atualizados e {windows_desatualizado} estão desatualizados.
        </p>
        <table>
        <tr>
            <th>Total</th>
            <th>Atualizado</th>
            <th>Desatualizado</th>
        </tr>

        <tr>
            <td>{windows_total}</td>
            <td>{windows_atualizado}</td>
            <td>{windows_desatualizado}</td>
        </tr>
        </table>
        <br>
        
        <p>Quantidade total de servidores no Satellite: {linux_total}.<br>
        Deste total, {linux_atualizado} estão atualizados e {linux_desatualizado} estão desatualizados.
        </p>
        <table>
        <tr>
            <th>Total</th>
            <th>Atualizado</th>
            <th>Desatualizado</th>
        </tr>

        <tr>
            <td>{linux_total}</td>
            <td>{linux_atualizado}</td>
            <td>{linux_desatualizado}</td>
        </tr>
        </table>
        <br>
        
        <p>Quantidade total de servidores no CMDB, SCCM e Satellite: {total_geral}.<br>
        Deste total, {satellite} estão apenas no Satellite, {CMDB} estão apenas no CMDB, {SCCM} estão apenas no SCCM e {validacao_ok} estão validados.
        </p>
        <table>
        <tr>
            <th>Total</th>
            <th>Satellite</th>
            <th>CMDB</th>
            <th>SCCM</th>
            <th>Validação OK</th>
        </tr>

        <tr>
            <td>{total_geral}</td>
            <td>{satellite}</td>
            <td>{CMDB}</td>
            <td>{SCCM}</td>
            <td>{validacao_ok}</td>
        </tr>
        </table><br>Obs: Para mais detalhes, acesse o arquivo em anexo, utilize a coluna 'Windows atualizado', para analisar o SCCM,
        utilize a coluna 'Linux atualizado' para analisar o Satellite e a coluna 'status' para analisar o CMDB X SCCM e Satellite.<br>
        <br>
        '''


    with open('nome_arquivo.html', 'w+') as file:
        file.writelines(body)

    df.to_excel('Discovery X SCCM e Satellite.xlsx')
   
    send_email(
        subject='Discovery X SCCM e Satellite',
        body=body,
        receiver=SEND_TO,
        copy=[],
        files=['Discovery X SCCM e Satellite.xlsx'],
        hidden_copy=[],
    )

if __name__ == '__main__':
  main()