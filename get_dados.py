from bs4 import BeautifulSoup
import requests
import sqlite3

'''def get_dados_camara(ano):
	cont = 0
	problema = list()
	conn = sqlite3.connect("py_politica.db")
	cursor = conn.cursor()
	ListaProps = BeautifulSoup(requests.get('http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoesVotadasEmPlenario?ano={}&tipo='.format (ano)).text, "html.parser")

	for proposicao in ListaProps.find_all("proposicao"):
		id_proposicao = proposicao.find("codproposicao").text
		dados = BeautifulSoup(requests.get('https://dadosabertos.camara.leg.br/api/v2/proposicoes/{}'.format(id_proposicao), headers={'accept': 'application/xml'}).text, "html.parser")
		tipo = dados.find("siglatipo").text
		numero = dados.find("numero").text
		ementa = dados.find("ementa").text

		try:			
			cursor.execute("INSERT INTO proposicao(id_proposicao, tipo, numero, ano, ementa) VALUES (?, ?, ?, ?, ?)", (id_proposicao, tipo, numero, ano, ementa))
			conn.commit()

		except sqlite3.IntegrityError:
			continue

		dados = BeautifulSoup(requests.get('https://dadosabertos.camara.leg.br/api/v2/proposicoes/{}/votacoes'.format(id_proposicao), headers={'accept': 'application/xml'}).text, "html.parser")
		for votacao in dados.find_all("votacao_"):
			id_votacao = votacao.find("id").text
			dados = BeautifulSoup(requests.get('https://dadosabertos.camara.leg.br/api/v2/votacoes/{}'.format(id_votacao), headers={'accept': 'application/xml'}).text, "html.parser")

			try:	
				data_hora_ini = dados.find("datahorainicio").text
				data_hora_fim = dados.find("datahorafim").text

			except AttributeError:
				if dados.find('status').text == '404':
					cont+=1

				print(dados.find('status').text)
				continue
			try:		
				cursor.execute("INSERT INTO votacao(id_votacao, id_proposicao, dataHoraInicio, dataHoraFim) VALUES (?, ?, ?, ?)", (id_votacao, id_proposicao, data_hora_ini, data_hora_fim))
				conn.commit()

			except sqlite3.IntegrityError:
				print(id_votacao)
				continue

			try:
				if 'Secreta' in votacao.find("tipovotacao").text:
					placar_sim = int(votacao.find("placarsim").text)
					placar_nao = int(votacao.find("placarnao").text)
					placar_abs = int(votacao.find("placarabstencao").text)

					cursor.execute("INSERT INTO votacao_secreta(id_votacao, placarSim, placarNao, placarAbs) VALUES (?, ?, ?, ?)", (id_votacao, placar_sim, placar_nao, placar_abs))
					conn.commit()
					print(votacao.find("tipovotacao").text)
					continue

			except AttributeError:
				problema.append(id_votacao)
				print(id_votacao)
				print('erro')
				continue
						
			dados = BeautifulSoup(requests.get('https://dadosabertos.camara.leg.br/api/v2/votacoes/{}/votos'.format(id_votacao), headers={'accept': 'application/xml'}).text, "html.parser")
			for voto in dados.find_all("votos"):
				id_candidato = voto.find("id").text
				nome = voto.find("nome").text

				try:
					cursor.execute("INSERT INTO parlamentar(id_candidato, nome, casa) VALUES (?, ?, ?)", (id_candidato, nome, "CF"))
					conn.commit()
				except sqlite3.IntegrityError:
					pass

				sigla = voto.find("siglapartido").text
				uf = voto.find("siglauf").text
				descricao = voto.find("voto").text

				cursor.execute("INSERT INTO voto(id_candidato, id_votacao, sigla, uf, descricao) VALUES (?, ?, ?, ?, ?)", (id_candidato, id_votacao, sigla, uf, descricao))
				conn.commit()

	conn.close()
	print('{} ocorrencias'.format(cont))
	print(problema)
'''

def get_dados_senado(ano):
	conn = sqlite3.connect("py_politica.db")
	cursor = conn.cursor()

	for i in range(1,13):
		senado = BeautifulSoup(
			requests.get('http://legis.senado.leg.br/dadosabertos/plenario/agenda/mes/{}{:02d}01'.format(ano,i)).text, 
			"html.parser")

		for data in senado.find_all("data"):
			data = data.text
			if 'd' in data:
				continue

			data = data.replace("-","")
			senado = BeautifulSoup(
				requests.get('http://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/{}'.format(data)).text,
				"html.parser")

			for votacao in senado.find_all('votacao'):
				if votacao.find("secreta").text == 'S':
					try:
						id_materia = votacao.find('codigomateria').text
						tipo = votacao.find('siglamateria').text
						ano_materia = votacao.find('anomateria').text
						numero = votacao.find('numeromateria').text
						ementa = BeautifulSoup(
							requests.get('http://legis.senado.leg.br/dadosabertos/materia/{}'.format(id_materia)).text,
							"html.parser")
						ementa = ementa.find('ementamateria').text

						id_votacao = votacao.find('codigosessaovotacao').text
						data_hora_ini = votacao.find('datasessao').text + ' ' + votacao.find("horainicio").text + ":00"

						placar_sim = votacao.find('totalvotossim').text
						placar_nao = votacao.find('totalvotosnao').text
						placar_abs = votacao.find('totalvotosabstencao').text
						

					except AttributeError:
						continue

					try:
						cursor.execute('''INSERT INTO proposicao(id_proposicao, tipo, numero, ano, ementa) 
							VALUES (?, ?, ?, ?, ?)''', 
							(id_materia, tipo, numero, ano_materia, ementa))
						conn.commit()

					except sqlite3.IntegrityError:
						pass

					try:
						cursor.execute("INSERT INTO votacao(id_votacao, id_proposicao, dataHoraInicio) VALUES (?, ?, ?)", (id_votacao, id_materia, data_hora_ini))
						conn.commit()
						cursor.execute("INSERT INTO votacao_secreta(id_votacao, placarSim, placarNao, placarAbs) VALUES (?, ?, ?, ?)", (id_votacao, placar_sim, placar_nao, placar_abs))
						conn.commit()

					except sqlite3.IntegrityError:
						continue
					
		
				else:
					if votacao.find('votos') == None:
						continue
						
					try:

						id_materia = votacao.find('codigomateria').text
						tipo = votacao.find('siglamateria').text
						ano_materia = votacao.find('anomateria').text
						numero = votacao.find('numeromateria').text
						ementa = BeautifulSoup(requests.get('http://legis.senado.leg.br/dadosabertos/materia/{}'.format(id_materia)).text, "html.parser")
						ementa = ementa.find('ementamateria').text

						id_votacao = votacao.find('codigosessaovotacao').text
						data_hora_ini = votacao.find('datasessao').text + ' ' + votacao.find("horainicio").text + ":00"

					except AttributeError:
						continue					
							
					try:
						cursor.execute("INSERT INTO proposicao(id_proposicao, tipo, numero, ano, ementa) VALUES (?, ?, ?, ?, ?)", (id_materia, tipo, numero, ano_materia, ementa))
						conn.commit()

					except sqlite3.IntegrityError:
						pass
						
					try:
						cursor.execute("INSERT INTO votacao(id_votacao, id_proposicao, dataHoraInicio) VALUES (?, ?, ?)", (id_votacao, id_materia, data_hora_ini))
						conn.commit()

					except sqlite3.IntegrityError:
						continue
							
					for voto in votacao.find_all('votoparlamentar'):
						id_candidato = voto.find('codigoparlamentar').text
						nome = voto.find('nomeparlamentar').text
						sigla = voto.find('siglapartido').text
						uf = voto.find('siglauf').text
						descricao = voto.find('voto').text

						try:
							cursor.execute("INSERT INTO parlamentar(id_candidato, nome, casa) VALUES (?, ?, ?)", (id_candidato, nome, "SF"))
							conn.commit()

						except sqlite3.IntegrityError:
							pass
								
						cursor.execute("INSERT INTO voto(id_candidato, id_votacao, sigla, uf, descricao) VALUES (?, ?, ?, ?, ?)", (id_candidato, id_votacao, sigla, uf, descricao))
						conn.commit()

	
	conn.close()


for ano in range(2010,2018):
	print(ano)
	get_dados_senado(ano)

