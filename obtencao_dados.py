from bs4 import BeautifulSoup
import pprint as pp
import requests
import sqlite3

def get_proposicoes_camara ():
	ano = 2017
	dados_propostas = [] 
	ListaProps = requests.get("http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoesVotadasEmPlenario?ano={}&tipo=".format(ano))
	ListaProps = ListaProps.text # XML aonde estão as informações
	ListaProps = BeautifulSoup(ListaProps, "html.parser")

	for info in ListaProps.find_all("proposicoes"):
		for proposicao in info.find_all("proposicao"):
			for dados in proposicao.find_all("nomeproposicao"):
				if "=>" in dados.text: # Verifica se houve uma mudança na proposta (Ex: PL que virou PEC) e pega o nome mais recente
					dados = dados.text.split(">")
					dados = dados[1].split()

				else:
					dados = dados.text.split()
 
				tipo = dados[0]
				numero, ano = dados[1].split("/")
				proposta = [numero, tipo, ano]
				if proposta in dados_propostas:
					continue
				else:
					dados_propostas.append([numero, tipo, ano]) 
					
		return dados_propostas

def get_agenda_senado():
	datas = []

	for i in range(1,13):
		senado = requests.get('http://legis.senado.leg.br/dadosabertos/plenario/agenda/mes/2017{:02d}01'.format(i))
		senado = senado.text
		senado = BeautifulSoup(senado, "html.parser")

		for data in senado.find_all("data"):
			data = data.text
			if 'd' in data:
				continue

			datas.append(data)

	return datas
	
def get_votacoes_camara(propostas): 
	deputados = set()
	partidos = set()
	votos = set()
	votacao_camara = set()
	
	for proposta in propostas:
		votacoesLista = requests.get("http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ObterVotacaoProposicao?tipo={}&numero={}&ano={}".format(proposta[1], proposta[0], proposta[2]))
		votacoesLista = BeautifulSoup(votacoesLista.text, "html.parser")
		cod = 1

		for votacao in votacoesLista.find_all("votacao"): 
			if votacao["data"].split("/")[2] == "2017":
				data = str(votacao["data"]).split('/')
				data = data[2]+'-'+data[1]+'-'+data[0]
				votacao_camara.add((votacao['codsessao']+str(-cod), proposta[1], data))
				for voto in votacao.find_all("deputado"):
					if voto['idecadastro'] == '':
						continue

					if voto['partido'].strip() == 'Podemos':
						partidos.add(('PODE', voto['uf']))
						
					elif voto['partido'].strip() == 'Solidaried':
						partidos.add(('SD', voto['uf']))
						
					elif voto['partido'].strip() == 'S/Partido':
						partidos.add(('Outros', voto['uf']))

					else:
						partidos.add((voto['partido'], voto['uf']))

					if voto['voto'] == 'Sim':
						votos.add((voto["idecadastro"], votacao['codsessao']+str(-cod), 1))

					elif voto['voto'] == 'Não':
						votos.add((voto["idecadastro"], votacao['codsessao']+str(-cod), -1))

					else:
						votos.add((voto["idecadastro"], votacao['codsessao']+str(-cod), 0))
						
					deputados.add((voto["idecadastro"], voto["nome"], "CF"))


				cod += 1

	return deputados, partidos, votos, votacao_camara

def get_votacoes_senado(data):
	senadores = set()
	partidos = set()
	votos_senado = set()
	votacao_senado = set()
	data = data.replace("-","")
	xml_votacao = requests.get('http://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/{}'.format(data))
	xml_votacao = xml_votacao.text
	xml_votacao = BeautifulSoup(xml_votacao, "html.parser")

	
	for votacao in xml_votacao.find_all("votacao"):
		if votacao.find("secreta").text.strip() == 'S':
			continue

		cod_sessao = votacao.find('codigosessaovotacao').text
		data_sessao = votacao.find('datasessao').text
		tipo = votacao.find('siglamateria').text
		votacao_senado.add((cod_sessao, tipo, data_sessao))

		for votos in votacao.find_all("votoparlamentar"):
			senador = votos.find("codigoparlamentar").text.strip()
			nome = votos.find('nomeparlamentar').text.strip()
			partido = votos.find('siglapartido').text.strip()
			UF = votos.find('siglauf').text.strip()
			senadores.add((senador, nome, "SF"))

			if partido == 'S/Partido':
				partidos.add(('Outros', UF))

			elif partido == 'Podemos   ':
				partidos.add(('PODE', UF))

			elif partido == 'Solidaried':
				partidos.add(('SD', UF))

			else:
				partidos.add((partido,UF))

			if votos.find('voto').text.strip() == 'Sim':
				votos_senado.add((senador, cod_sessao, 1))

			elif votos.find('voto').text.strip() == 'Não':
				votos_senado.add((senador, cod_sessao, -1))

			else:
				votos_senado.add((senador, cod_sessao, 0))
			
	return senadores, partidos, votos_senado, votacao_senado


def main():
	conn = sqlite3.connect("py_politica.db")
	cursor = conn.cursor()
	parlamentares = set()
	partidos = set()
	votos = set()
	votacao = set()

	agenda = get_agenda_senado()
	proposicoes = get_proposicoes_camara()

	deputados, partidos_camara, votos_camara, votacao_camara = get_votacoes_camara(proposicoes)
	parlamentares = parlamentares.union(deputados)
	partidos = partidos.union(partidos_camara)
	votos = votos.union(votos_camara)
	votacao = votacao.union(votacao_camara)

	for data in sorted(agenda):
		senadores, partidos_senado, votos_senado, votacao_senado = get_votacoes_senado(data)
		parlamentares = parlamentares.union(senadores)
		partidos = partidos.union(partidos_senado)
		votos = votos.union(votos_senado)
		votacao = votacao.union(votacao_senado)


	cursor.executemany("INSERT INTO parlamentar(id, id_API, nome, casa) VALUES (null, ?, ?, ?)", parlamentares)
	cursor.executemany("INSERT INTO votacao(id, id_API, tipo, data) VALUES (null, ?, ?, ?)", votacao)
	conn.commit()
	
	for partido in partidos:
		try:
			cursor.execute("INSERT INTO partido (sigla, uf) Values (?,?)", partido)

		except sqlite3.IntegrityError:
				continue


	for voto in votos:
		id_parlamentar = cursor.execute('SELECT id FROM parlamentar WHERE id_API = {}'.format(voto[0])).fetchone()
		id_votacao = cursor.execute('SELECT id FROM votacao WHERE id_API = "{}"'.format(str(voto[1]))).fetchone()
		cursor.execute("INSERT INTO voto(id_candidato, id_votacao, descricao) VALUES ({}, {}, {})".format(int(id_parlamentar[0]), id_votacao[0], voto[2]))
			
	conn.commit()
	conn.close()

if __name__ == '__main__':
	main()