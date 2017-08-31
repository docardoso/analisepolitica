from bs4 import BeautifulSoup
import pprint as pp
import requests
import sqlite3

def get_proposicoes_camara ():

    ano = 2017
    ListaProps = requests.get("http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoesVotadasEmPlenario?ano={}&tipo=".format(ano))
    xml = ListaProps.text # XML aonde estão as informações

    soupProp = BeautifulSoup(xml, "html.parser")
    dados_propostas = [] 
    propsLista = soupProp.find_all("proposicoes")

    i = 0
    for info in propsLista:
        props = info.find_all("proposicao")
        for prop in props:
            nomes = prop.find_all("nomeproposicao")
            for nome in nomes:
                if "=>" in nome.text: # Verifica se houve uma mudança na proposta (Ex: PL que virou PEC) e pega o nome mais recente
                    dados = nome.text.split(">")
                    dados = dados[1].split()
 
                else:
                    dados = nome.text.split()
 
                tipo = dados[0]
                numero, ano = dados[1].split("/")
                proposta = [numero, tipo, ano]
                if proposta in dados_propostas:
                    continue
                else:
                    dados_propostas.append([numero, tipo, ano]) 
               

    return dados_propostas
    
def get_votacoes_camara(propostas): 
           
    deputados = set()
    partidos = set()

    for proposta in propostas:

        votacoesLista = requests.get("http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ObterVotacaoProposicao?tipo={}&numero={}&ano={}".format(proposta[1], proposta[0], proposta[2]))
        soupVot = BeautifulSoup(votacoesLista.text, "html.parser")
        votacoes = soupVot.find_all("votacao")

        for votacao in votacoes: 
            if votacao["data"].split("/")[2] == "2017":
                votos = votacao.find_all("deputado")

                for voto in votos:
                    deputados.add((voto["idecadastro"], voto["nome"], "CF"))

                    if voto["partido"].strip() == "Solidaried":
                        partidos.add("SD")
                    else:
                        partidos.add(voto["partido"].strip())

        return deputados, partidos

def get_agenda_senado():
    datas = []

    for i in range(1,13):
        senado = requests.get('http://legis.senado.leg.br/dadosabertos/plenario/agenda/mes/2017{:02d}01'.format(i))
        xml_agenda = senado.text
        xml_agenda = BeautifulSoup(xml_agenda, "html.parser")

        for data in xml_agenda.find_all("data"):
            data = data.text
            if 'd' in data:
                continue

            datas.append(data)

    return datas

def get_votacoes_senado(data):
    sen = set()
    part = set()
    data = "".join(data.split("-"))
    xml_votacao = requests.get('http://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/{}'.format(data))
    xml_votacao = xml_votacao.text
    xml_votacao = BeautifulSoup(xml_votacao, "html.parser")

    
    for votacao in xml_votacao.find_all("votacao"):
        if votacao.find("secreta").text.strip() == 'S':
            continue

        for votos in votacao.find_all("votoparlamentar"):
            senador = votos.find("codigoparlamentar").text.strip()

            partido = votos.find('siglapartido').text.strip()
            nome = votos.find('nomeparlamentar').text.strip()

            id_senador = (senador, nome, "SF")
    
            sen.add(id_senador)
            part.add(partido)

    return sen, part


def main():
    parlamentares = set()
    partidos = set()

    agenda = get_agenda_senado()
    proposicoes = get_proposicoes_camara()

    d, p = get_votacoes_camara(proposicoes)
    parlamentares = parlamentares.union(d)
    partidos = partidos.union(p)

    for data in sorted(agenda):
        s, p = get_votacoes_senado(data)
        parlamentares = parlamentares.union(s)
        partidos = partidos.union(p)

    conn = sqlite3.connect("py_politica.db")
    cursor = conn.cursor()

    for i in parlamentares:
        if len(i) > 3:
            print(i)
    cursor.executemany("INSERT INTO parlamentar(id_API, nome, casa) VALUES (?, ?, ?)", parlamentares)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()