
from bs4 import BeautifulSoup
import requests
import sqlite3

def get_proposicoes_camara(ano):
    proposicoes = set()
    lista_props = requests.get('http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoesVotadasEmPlenario?ano={}&tipo='.format(ano))
    lista_props = BeautifulSoup(lista_props.text, 'lxml')

    for info in lista_props.find_all('proposicoes'):
        for proposicao in info.find_all('proposicao'):
            for nome_proposicao in proposicao.find_all('nomeproposicao'):
                nome_proposicao = nome_proposicao.text
                if '=>' in nome_proposicao: # Verifica se houve uma mudança na proposicao (Ex: PL que virou PEC) e pega o nome mais recente
                    nome_proposicao = nome_proposicao.split(' => ')[1]

                nome_proposicao = nome_proposicao.split()
                tipo = nome_proposicao[0]
                numero, ano = nome_proposicao[1].split('/')
                proposicao = (numero, tipo, ano)
                proposicoes.add(proposicao)

        return proposicoes

def get_votacoes_camara(proposicoes):
    deputados = set()
    partidos = set()
    votos = set()
    votacao_camara = set()

    for proposicao in proposicoes:
        votacoesLista = requests.get('http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ObterVotacaoProposicao?tipo={}&numero={}&ano={}'.format(proposicao[1], proposicao[0], proposicao[2]))
        votacoesLista = BeautifulSoup(votacoesLista.text, 'html.parser')
        cod = 1
        print('cheguei')

        for votacao in votacoesLista.find_all('votacao'):
            hora = votacao['hora']+':00'
            data = str(votacao['data']).split('/')
            if len(data[1]) == 1:
                if len(data[0])==1:
                    data = data[2]+'-'+'0'+data[1]+'-'+'0'+data[0]
                else:
                    data = data[2]+'-'+'0'+data[1]+'-'+data[0]

            else:
                if len(data[0]) == 1:
                    data = data[2]+'-'+data[1]+'-'+'0'+data[0]

                else:
                    data = data[2]+'-'+data[1]+'-'+data[0]

            data_hora = data + ' ' + hora

            votacao_camara.add((votacao['codsessao']+str(-cod), proposicao[1], data_hora))
            for voto in votacao.find_all('deputado'):
                partido = voto['partido'].strip()
                if voto['idecadastro'] == '':
                    continue

                if voto['partido'].strip() == 'Podemos':
                    partidos.add(('PODE', voto['uf']))
                    partido = 'PODE'

                elif voto['partido'].strip() == 'Solidaried':
                    partidos.add(('SD', voto['uf']))
                    partido = 'SD'

                elif voto['partido'].strip() == 'S/Partido':
                    partidos.add(('Outros', voto['uf']))
                    partido = 'Outros'

                else:
                    partidos.add((voto['partido'], voto['uf']))

                if voto['voto'] == 'Sim':
                    votos.add((voto['idecadastro'], votacao['codsessao']+str(-cod), 1, partido, voto['uf']))

                elif voto['voto'] == 'Não':
                    votos.add((voto['idecadastro'], votacao['codsessao']+str(-cod), -1, partido, voto['uf']))

                else:
                    votos.add((voto['idecadastro'], votacao['codsessao']+str(-cod), 0, partido, voto['uf']))

                deputados.add((voto['idecadastro'], voto['nome'], 'CF'))


            cod += 1
    print('sai')

    return deputados, partidos, votos, votacao_camara


'''def get_agenda_senado():
    datas = []

    for i in range(1,13):
        senado = requests.get('http://legis.senado.leg.br/dadosabertos/plenario/agenda/mes/2017{:02d}01'.format(i))
        senado = senado.text
        senado = BeautifulSoup(senado, 'html.parser')

        for data in senado.find_all('data'):
            data = data.text
            if 'd' in data:
                continue

            datas.append(data)

    return datas


def get_votacoes_senado(data):
    senadores = set()
    partidos = set()
    votos_senado = set()
    votacao_senado = set()
    data = data.replace('-','')
    xml_votacao = requests.get('http://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/{}'.format(data))
    xml_votacao = xml_votacao.text
    xml_votacao = BeautifulSoup(xml_votacao, 'html.parser')


    for votacao in xml_votacao.find_all('votacao'):
        if votacao.find('secreta').text.strip() == 'S':
            continue

        cod_sessao = votacao.find('codigosessaovotacao').text
        data_sessao = votacao.find('datasessao').text
        hora_sessao = votacao.find('horainicio').text + ':00'
        tipo = votacao.find('siglamateria').text
        votacao_senado.add((cod_sessao, tipo, data_sessao, hora_sessao))

        for votos in votacao.find_all('votoparlamentar'):
            senador = votos.find('codigoparlamentar').text.strip()
            nome = votos.find('nomeparlamentar').text.strip()
            partido = votos.find('siglapartido').text.strip()
            UF = votos.find('siglauf').text.strip()
            senadores.add((senador, nome, 'SF'))

            if partido == 'S/Partido':
                partidos.add(('Outros', UF))

            elif partido == 'Podemos   ':
                partidos.add(('PODE', UF))

            elif partido == 'Solidaried':
                partidos.add(('SD', UF))

            else:
                partidos.add((partido,UF))

            if votos.find('voto').text.strip() == 'Sim':
                votos_senado.add((senador, cod_sessao, 1, partido, UF))

            elif votos.find('voto').text.strip() == 'Não':
                votos_senado.add((senador, cod_sessao, -1, partido, UF))

            else:
                votos_senado.add((senador, cod_sessao, 0, partido, UF))


    return senadores, partidos, votos_senado, votacao_senado'''


def main():
    conn = sqlite3.connect('py_politica.db')
    cursor = conn.cursor()
    proposicoes = list()
    parlamentares = set()
    partidos = set()
    votos = set()
    votacao = set()

    #agenda = get_agenda_senado()
    for ano in range(2000,2018):
        prop_ano = get_proposicoes_camara(ano)
        for Proposicoes in prop_ano:
            proposicoes.append(Proposicoes)


    deputados, partidos_camara, votos_camara, votacao_camara = get_votacoes_camara(proposicoes)
    parlamentares = parlamentares.union(deputados)
    partidos = partidos.union(partidos_camara)
    votos = votos.union(votos_camara)
    votacao = votacao.union(votacao_camara)

    '''for data in sorted(agenda):
        senadores, partidos_senado, votos_senado, votacao_senado = get_votacoes_senado(data)
        parlamentares = parlamentares.union(senadores)
        partidos = partidos.union(partidos_senado)
        votos = votos.union(votos_senado)
        votacao = votacao.union(votacao_senado)'''


    cursor.executemany('INSERT INTO parlamentar(id_candidato, id_API, nome, casa) VALUES (null, ?, ?, ?)', parlamentares)
    cursor.executemany('INSERT INTO votacao(id_votacao, id_API, tipo, data_hora) VALUES (null, ?, ?, ?)', votacao)
    conn.commit()



    for voto in votos:
        id_parlamentar = cursor.execute('SELECT id_candidato FROM parlamentar WHERE id_API = {}'.format(voto[0])).fetchone()
        id_votacao = cursor.execute('SELECT id_votacao FROM votacao WHERE id_API = "{}"'.format(str(voto[1]))).fetchone()
        cursor.execute('INSERT INTO voto(id_candidato, id_votacao, sigla, uf, descricao) VALUES ("{}", "{}", "{}", "{}", "{}")'.format(int(id_parlamentar[0]), id_votacao[0],voto[3], voto[4], voto[2]))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()

