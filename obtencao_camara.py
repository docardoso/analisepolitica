from bs4 import BeautifulSoup
import requests as res
import pprint as pp
import sqlite3
import pickle
import json
 
# ---
# Pega a lista de proposições votadas em algum ano e coloca em um dicionario o numero, tipo e ano das proposições
# ---

def get_proposicoes ():

    ano = 2017
    ListaProps = res.get("http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoesVotadasEmPlenario?ano={}&tipo=".format(ano))
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



def get_deputados_partidos(): 

    r = res.get ("http://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterDeputados")
    xml = BeautifulSoup(r.text,"html.parser")
    ideCadastro =[d.text for d in set(xml.find_all("idecadastro"))]
    partidos = [p.text for p in set(xml.find_all("partido"))]
 
    return ideCadastro, partidos
    
def get_votacoes(proposta): 
           
    votacoesLista = res.get("http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ObterVotacaoProposicao?tipo={}&numero={}&ano={}".format(proposta[1], proposta[0], proposta[2]))
    soupVot = BeautifulSoup(votacoesLista.text, "html.parser")
    votacoes = soupVot.find_all("votacao")
              
    return votacoes

def main (): 
 
    deputados, partidos = get_deputados_partidos()
    propostas = get_proposicoes()

    detalhes = [[] for _ in range(len(deputados))]
    index = [0] * len(deputados)

    for proposta in propostas:   
        votacoes = get_votacoes(proposta)

        for votacao in votacoes: 
            if votacao["data"].split("/")[2] == "2017":
                votos = votacao.find_all("deputado")

                for voto in votos:
                    try: 
                        indice_dep = deputados.index(voto["idecadastro"].strip())
        
                    except ValueError: 
                        deputados.append(voto["idecadastro"].strip())
                        detalhes.append([])
                        index.append(0)
                        indice_dep = deputados.index(voto["idecadastro"].strip())

                    if len(detalhes[indice_dep]) < 3:
                        index[indice_dep] = voto["idecadastro"]
                        detalhes[indice_dep].append(voto["nome"])
                        detalhes[indice_dep].append(voto["uf"])
                        if voto["partido"].strip() == "Solidaried":
                            detalhes[indice_dep].append("SD")
                        else:
                            detalhes[indice_dep].append(voto["partido"].strip())

                    try: 
                        indice_part = partidos.index(voto["partido"].strip())

                    except ValueError: 
                        if voto["partido"].strip() == "Solidaried":
                            indice_part = partidos.index("SD")

                        else:
                            partidos.append(voto["partido"].strip())          
                            indice_part = partidos.index(voto["partido"].strip())

    nomes = []

    for item in detalhes:
        try:
            nomes.append(item[0])
        except Exception as ex:
            print(ex)

    parlamentares = []
    for x, y in zip(deputados, nomes):
        parlamentares.append((int(x), y, "CF"))

    conn = sqlite3.connect("py_politica.db")
    cursor = conn.cursor()

    cursor.executemany("INSERT INTO Parlamentar VALUES (?, ?, ?)", parlamentares)

    conn.commit()
    conn.close()
    
                
main()