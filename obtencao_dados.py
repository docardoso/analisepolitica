import sqlite3
import aiohttp as aio
from bs4 import BeautifulSoup
import asyncio as asy

def consulta(tabela, padrao, info):
	conn = sqlite3.connect("py_politica.db")
	cursor = conn.cursor()
	try:
		columns = '?, '*(len(info) - 1)
		
		try:
			cursor.execute('''INSERT INTO {}{} VALUES ({}?);'''.format(tabela,padrao,columns), info)
			conn.commit()
			conn.close()
			print('foi')

		except sqlite3.IntegrityError:
			conn.close()
			print("não foi")

	except TypeError:
		pass 

async def get_materia(id_materia, session):
	URL1 = 'http://legis.senado.leg.br/dadosabertos/materia/{}'
	URL2 = 'http://legis.senado.leg.br/dadosabertos/materia/movimentacoes/{}?v=5'
	async with session.get(URL1.format(id_materia)) as materia:
		try:
			materia = BeautifulSoup(await materia.text(), 'lxml')
			tipo = materia.find('siglasubtipomateria').text
			autor = materia.find('nomeautor').text
			numero = materia.find('numeromateria').text
			data = materia.find('dataapresentacao').text
			ementa = materia.find('ementamateria').text
			temas = materia.find('indexacaomateria').text
		except AttributeError:
			return None

		async with session.get(URL2.format(id_materia)) as tramitacao:
			tramitacao = BeautifulSoup(await tramitacao.text(), 'lxml')
			status = tramitacao.find('descricaosituacao').text
			return (id_materia, tipo, autor, numero, data, ementa, temas, status)

async def get_dados(data, session):
	padrao_materia = '(id_materia, tipo, autor, numero, data_apresentacao, ementa, temas, status)'
	padrao_votacao = '(id_materia, id_votacao, dataHorainicio)'
	padrao_votacao_s = '(id_votacao, placarSim, placarNao, placarAbs)'
	padrao_parlamentar = '(id_candidato, nome, casa)'
	padrao_voto = '(id_candidato, id_votacao, sigla, uf, descricao)'	
	URL = 'http://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/{}'
	async with session.get(URL.format(data)) as votacoes:
		votacoes = BeautifulSoup(await votacoes.text(), 'lxml')

		for votacao in votacoes.find_all('votacao'):
			try:
				id_materia = votacao.find('codigomateria').text
				id_votacao = votacao.find('codigosessaovotacao').text
				data_hora_ini = votacao.find('datasessao').text + ' ' + votacao.find("horainicio").text + ":00"
			except AttributeError:
				continue
		
			consulta('materia',padrao_materia, await get_materia(id_materia,session))
			consulta('votacao', padrao_votacao, (id_materia, id_votacao, data_hora_ini))

			if votacao.find('secreta').text == 'S':
				try:
					placar_sim = votacao.find('totalvotossim').text
					placar_nao = votacao.find('totalvotosnao').text
					placar_abs = votacao.find('totalvotosabstencao').text
					consulta('votacao_secreta' ,padrao_votacao_s, (id_votacao, placar_sim, placar_nao, placar_abs))
					continue
				except AttributeError:
					continue
			
			if votacao.find('votos') == None:
				continue
			
			for voto in votacao.find_all('votoparlamentar'):
				id_candidato = voto.find('codigoparlamentar').text
				nome = voto.find('nomeparlamentar').text
				sigla = voto.find('siglapartido').text
				uf = voto.find('siglauf').text
				descricao = voto.find('voto').text
				consulta('voto', padrao_voto, (id_candidato,id_votacao,sigla,uf,descricao))
				consulta('parlamentar', padrao_parlamentar, (id_candidato,nome,'SF'))


async def get_agenda(ano, mes, session):
	URL = 'http://legis.senado.leg.br/dadosabertos/plenario/agenda/mes/{}{:02d}01'
	async with session.get(URL.format(ano,mes)) as data:
		data = BeautifulSoup(await data.text(), 'lxml')
		return data.find_all('data')


async def main():
	params = list()
	async with aio.ClientSession(trust_env = True) as session:
		agenda = await asy.gather(*[get_agenda(ano, mes, session) for ano in range(2010, 2050) for mes in range(1,13)])
		for datas in agenda:
			for data in datas:
				try:
					if 'd' not in data.text:
						params.append(data.text.replace('-',''))		

				except TypeError:
					continue

		await asy.gather(*[get_dados(dado, session) for dado in params])


loop = asy.get_event_loop()
loop.run_until_complete(main())
loop.close()