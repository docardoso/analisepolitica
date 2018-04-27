import sqlite3
import aiohttp as aio
from bs4 import BeautifulSoup
import asyncio as asy
import logging
import time

PADRAO_MATERIA = '(id_materia, tipo, autor, numero, data_apresentacao, ementa, temas, apelido, status)'
PADRAO_VOTACAO = '(id_materia, id_votacao, dataHorainicio)'
PADRAO_VOTACAO_S = '(id_votacao, placarSim, placarNao, placarAbs)'
PADRAO_PARLAMENTAR = '(id_candidato, nome, casa)'
PADRAO_VOTO = '(id_candidato, id_votacao, sigla, uf, descricao)'	

t = time.time()
conn = sqlite3.connect("py_politica.db")
cursor = conn.cursor()
logging.getLogger('aiohttp.client').setLevel(logging.ERROR)


def insert(tabela, padrao, info):
	columns = ','.join('?'*len(info))
	try:
		cursor.execute('''INSERT INTO {}{} VALUES ({});'''.format(tabela,padrao,columns), info)
		conn.commit()
	except sqlite3.IntegrityError:
		pass

def get_text_alt(elem, tag, alt=None):
	try:
		return elem.find(tag).text
	except AttributeError:
		return alt

def get_parlamentar_partidos(mtx):
	votos = list()
	parlamentares = list()

	for linha in mtx:
		parlamentares.extend(linha[0])
		votos.extend(linha[1])

	for parlamentar, voto in zip(parlamentares, votos):
		insert('parlamentar', PADRAO_PARLAMENTAR, parlamentar)
		insert('voto', PADRAO_VOTO, voto)

async def get_materia(id_materia, session):
	URL1 = 'http://legis.senado.leg.br/dadosabertos/materia/{}'

	async with session.get(URL1.format(id_materia)) as materia:
		materia = BeautifulSoup(await materia.text(), 'lxml')
		tipo = materia.find('siglasubtipomateria').text
		autor = get_text_alt(materia, 'nomeautor', get_text_alt(materia, 'descricaotipoautor'))
		apelido = get_text_alt(materia, 'apelidomateria')
		numero = materia.find('numeromateria').text
		data = materia.find('dataapresentacao').text
		ementa = materia.find('ementamateria').text
		temas = get_text_alt(materia, 'indexacaomateria')
		status = materia.find('descricaosituacao').text
		return (id_materia, tipo, autor, numero, data, ementa, temas, apelido, status)

async def get_dados(data, session):
	votos = list()
	parlamentares = list()
	URL = 'http://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/{}'

	async with session.get(URL.format(data)) as votacoes:
		votacoes = BeautifulSoup(await votacoes.text(), 'lxml')
		for votacao in votacoes.find_all('votacao'):
			try:
				id_materia = votacao.find('codigomateria').text
			except AttributeError:
				id_materia = None
			else:
				insert('materia', PADRAO_MATERIA, await get_materia(id_materia, session))

			id_votacao = votacao.find('codigosessaovotacao').text
			data_hora_ini = votacao.find('datasessao').text + ' ' + votacao.find("horainicio").text + ":00"
			atr = (id_materia, id_votacao, data_hora_ini)
			insert('votacao', PADRAO_VOTACAO, atr)	

			if votacao.find('secreta').text == 'S':			
				placar_sim = get_text_alt(votacao, 'totalvotossim')
				placar_nao = get_text_alt(votacao, 'totalvotosnao')
				placar_abs = get_text_alt(votacao, 'totalvotosabstencao')
				atr = (id_votacao, placar_sim, placar_nao, placar_abs)
				insert('votacao_secreta', PADRAO_VOTACAO_S, atr)
			
			for voto in votacao.find_all('votoparlamentar'):
				id_candidato = voto.find('codigoparlamentar').text
				nome = voto.find('nomeparlamentar').text
				sigla = voto.find('siglapartido').text
				uf = voto.find('siglauf').text
				descricao = voto.find('voto').text
				parlamentares.append((id_candidato,nome,'SF'))
				votos.append((id_candidato,id_votacao,sigla,uf,descricao))		
		
		return parlamentares, votos
	
					
async def get_agenda(ano, mes, session):
	URL = 'http://legis.senado.leg.br/dadosabertos/plenario/agenda/mes/{}{:02d}01'

	async with session.get(URL.format(ano,mes)) as data:
		data = BeautifulSoup(await data.text(), 'lxml')
		return data.find_all('data')

async def main():
	params = list()

	async with aio.ClientSession(trust_env = True) as session:
		dummy = [get_agenda(ano, mes, session) for ano in range(2010, 2050) for mes in range(1,13)]
		agenda = await asy.gather(*dummy)
		for datas in agenda:
			for data in datas:
				try:
					if 'd' not in data.text:
						params.append(data.text.replace('-',''))		
				except TypeError:
					continue

		mtx = await asy.gather(*[get_dados(dado, session) for dado in params])
		return mtx

loop = asy.get_event_loop()
get_parlamentar_partidos(loop.run_until_complete(main()))
loop.close()
conn.close()
print(time.time() - t)