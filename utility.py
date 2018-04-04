import sqlite3 as sql
import scipy.stats as st
from matplotlib import pyplot as pp


def filia(parlamentar):
	conn = sql.connect('py_politica.db')
	cursor = conn.cursor()
	res = set()

	filia = cursor.execute('''SELECT  data, sigla, uf
		FROM votacao NATURAL JOIN voto
		WHERE id_candidato = '{}' ORDER BY data'''.format(parlamentar)).fetchall()

	res.add(filia[0])

	for i, info in enumerate(filia [1:],1):
		if info[1] != filia[i-1][1]:
			res.add(filia[i+1])

	conn.close()
	return res


def N_filia(parlamentar):
	conn = sql.connect('py_politica.db')
	cursor = conn.cursor()
	count = 1


	filia = cursor.execute('''SELECT  data, sigla, uf
		FROM votacao NATURAL JOIN voto
		WHERE id_candidato = '{}' ORDER BY data, hora'''.format(parlamentar)).fetchall()


	for i, info in enumerate(filia [1:],1):
		if info[1] != filia[i-1][1]:
			count += 1

	conn.close()
	return count

def N_filia_partido(partido):
	conn = sql.connect('py_politica.db')
	cursor = conn.cursor()
	filia_parlamentar = 0

	parlamentares = cursor.execute('''SELECT DISTINCT id_candidato
		FROM voto NATURAL JOIN votacao
		WHERE sigla = '{}' '''.format(partido)).fetchall()


	for parlamentar in parlamentares:
		filia_parlamentar += N_filia(parlamentar[0])

	return filia_parlamentar

# Retorna o numero de parlamentares que foram filiados a cada partido em uma das casas durante um determinado perido de tempo
def get_bancadas(dataInicio, dataFim, casa):
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()

	bancada = dict()

	dataInicio = dataInicio.split('-')
	dataFim = dataFim.split('-')

	lista_bancada = cursor.execute('''SELECT sigla, count(distinct voto.id_candidato) FROM voto
									join votacao join parlamentar
									WHERE votacao.ano_mes_dia > "{}-{}-{}"
									and votacao.ano_mes_dia < "{}-{}-{}"
									and votacao.id_votacao=voto.id_votacao
									and voto.id_candidato=parlamentar.id_candidato
									and parlamentar.casa="{}"
									group by sigla'''.format(dataInicio[0], dataInicio[1], dataInicio[2], dataFim[0], dataFim[1], dataFim[2], casa)).fetchall()

	for i in lista_bancada:
		bancada[i[0]] = i[1]

	return bancada

def bar_graph(eixo_x, eixo_y):
	pp.bar(eixo_x, eixo_y)
	pp.show()


def sherlock_holmes(votacoes):
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	ementas = list()

	ementas = [(cursor.execute('''SELECT ementa
		FROM proposicao
		WHERE id_proposicao IN
		(SELECT id_proposicao FROM votacao WHERE id_votacao = {});'''.format(votacao)).fetchone(), votacao) for votacao in votacoes]

	return ementas

def caca_palavras(ementas, palavras):
	polemica = list()
	for palavra in palavras:
		for ementa in ementas:
			if palavra in str(ementa[0]):
				polemica.append(ementa)

	return polemica


#Funções Estatisticas
DATA_INICIAL = '2010-02-24'
DATA_FIM = '2050-12-31'

def assertividade_votacao(data_in = DATA_INICIAL, data_fim = DATA_FIM):
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	ranking = list()

	sql_command = '''
		SELECT id_votacao
		FROM votacao
		WHERE id_votacao not in (SELECT id_votacao FROM votacao_secreta) AND
		date(dataHorainicio) >= '{}' AND
		date(dataHorainicio) <= '{}';
	'''
	votos = cursor.execute(sql_command.format(data_in, data_fim)).fetchall()
	sql_command1 = '''
		SELECT max(qtd)
		FROM (
			SELECT count(*) AS qtd
			FROM voto
			WHERE id_votacao = {}
			GROUP BY descricao)R;
	'''

	sql_command2 = '''
		SELECT COUNT (*)
		FROM voto
		WHERE id_votacao = {}
		GROUP BY id_votacao;
	'''

	for votacao in votos:
		placar_max = cursor.execute(sql_command1.format(votacao[0])).fetchone()
		total = cursor.execute(sql_command2.format(votacao[0])).fetchone()
		ranking.append((votacao[0], (placar_max[0]/total[0])*100))

	sql_command = '''
		SELECT id_votacao, placarSim, placarNao, placarAbs
		FROM votacao NATURAL JOIN votacao_secreta
		WHERE date(dataHorainicio) >= '{}' AND
			date(dataHorainicio) <= '{}';
	'''
	votacoes_secretas = cursor.execute(sql_command.format(data_in, data_fim)).fetchall()

	for v_secreta in votacoes_secretas:
		placar_max = max([v_secreta[1], v_secreta[2], v_secreta[3]])
		total = sum([v_secreta[1], v_secreta[2], v_secreta[3]])
		ranking.append((v_secreta[0],(placar_max/total)*100))

	ranking = sorted(ranking, key= lambda ranking: ranking[1], reverse = True)
	return ranking


def mais_votos(tipo, data_in = DATA_INICIAL, data_fim = DATA_FIM):
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	ranking = list()

	if tipo.lower() == 's': tipo = 'Sim'
	elif tipo.lower() == 'n': tipo = 'Não'
	elif tipo.lower() ==  'a': tipo = 'Abstenção'
	elif tipo not in ('Sim', 'Não', 'Abstenção'):
		raise ValueError("Tipo Inválido")

	sql_command = '''
		SELECT id_votacao
		FROM votacao
		WHERE id_votacao not in (SELECT id_votacao FROM votacao_secreta) AND
		date(dataHorainicio) >= '{}' AND
		date(dataHorainicio) <= '{}';
	'''

	votacoes = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()

	sql_command ='''
		SELECT id_votacao, COUNT(*)
		FROM voto
		WHERE
			id_votacao = {} AND
			descricao = '{}'
		GROUP BY id_votacao;
		'''
	for votacao in votacoes:
		total = cursor.execute(sql_command.format(votacao[0],tipo)).fetchone()
		if total == None:
			total = (votacao[0], 0)

		ranking.append(total)

	if tipo == 'Sim': tipo = 'placarSim'
	if tipo == 'Não': tipo = 'placarNao'
	if tipo == 'Abstenção': tipo = 'placarAbs'

	sql_command = '''
		SELECT id_votacao, {}
		FROM votacao NATURAL JOIN votacao_secreta
		WHERE id_votacao in (SELECT id_votacao FROM votacao_secreta) AND
		date(dataHorainicio) >= '{}' AND
		date(dataHorainicio) <= '{}';
	'''
	votacao_secreta = cursor.execute(sql_command.format(tipo, data_in, data_fim)).fetchall()
	ranking.extend(votacao_secreta)
	ranking = sorted(ranking, key= lambda ranking: ranking[1], reverse = True)
	return ranking


def competitividade_votacao(op = '/', data_in = DATA_INICIAL ,data_fim = DATA_FIM):
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	ranking = list()

	sql_command = '''
		SELECT id_votacao
		FROM votacao
		WHERE id_votacao not in (SELECT id_votacao FROM votacao_secreta) AND
		date(dataHorainicio) >= '{}' AND
		date(dataHorainicio) <= '{}';
	'''
	votacoes = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()

	sql_command = '''
		SELECT count(descricao) as qtd
		FROM voto
		WHERE id_votacao = {}
		GROUP BY descricao
		ORDER BY qtd desc
	'''

	for votacao in votacoes:
		primeiros = cursor.execute(sql_command.format(votacao[0])).fetchall()[:2]
		if op == '/': calculo = int(primeiros[0][0])/int(primeiros[1][0])
		elif op == '-': calculo = int(primeiros[0][0])-int(primeiros[1][0])
		else:
			raise ValueError("Operador inválido")

		ranking.append((votacao[0], calculo))

	sql_command = '''
		SELECT id_votacao
		FROM votacao NATURAL JOIN votacao_secreta
		WHERE id_votacao in (SELECT id_votacao FROM votacao_secreta) AND
		date(dataHorainicio) >= '{}' AND
		date(dataHorainicio) <= '{}';
	'''

	votacoes_secretas = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()

	sql_command = '''
		SELECT placarSim, placarNao, placarAbs
		FROM votacao_secreta
		WHERE id_votacao = {}
	'''

	for votacao_secreta in votacoes_secretas:
		primeiros = cursor.execute(sql_command.format(votacao_secreta[0])).fetchone()
		primeiros = sorted(primeiros)[-2:]
		if op == '/': calculo = int(primeiros[1])/int(primeiros[0])
		elif op == '-': calculo = int(primeiros[1])-int(primeiros[0])
		else:
			raise ValueError("Operador inválido")
		ranking.append((votacao_secreta[0], calculo))

	ranking = sorted(ranking, key= lambda ranking: ranking[1], reverse = True)
	return ranking


def entropia(data_in = DATA_INICIAL, data_fim = DATA_FIM):
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()
	ranking = list()

	sql_command = '''
		SELECT id_votacao
		FROM votacao
		WHERE id_votacao not in (SELECT id_votacao FROM votacao_secreta) AND
		date(dataHorainicio) >= '{}' AND
		date(dataHorainicio) <= '{}';
	'''
	votacoes = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()

	sql_command = '''
		SELECT count(descricao) as qtd
		FROM voto
		WHERE id_votacao = {}
		GROUP BY descricao
	'''

	for votacao in votacoes:
		n_votos = cursor.execute(sql_command.format(votacao[0])).fetchall()
		n_votos = [int(a[0]) for a in n_votos]
		ranking.append((votacao[0],st.entropy(n_votos)))

	sql_command = '''
		SELECT id_votacao
		FROM votacao NATURAL JOIN votacao_secreta
		WHERE id_votacao in (SELECT id_votacao FROM votacao_secreta) AND
		date(dataHorainicio) >= '{}' AND
		date(dataHorainicio) <= '{}';
	'''

	votacoes_secretas = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()

	sql_command = '''
		SELECT placarSim, placarNao, placarAbs
		FROM votacao_secreta
		WHERE id_votacao = {}
	'''
	for votacao_secreta in votacoes_secretas:
		n_votos = cursor.execute(sql_command.format(votacao_secreta[0])).fetchone()
		ranking.append((votacao_secreta[0], st.entropy(n_votos)))

	ranking = sorted(ranking, key= lambda ranking: ranking[1], reverse = True)
	return ranking


def votacoes_periodo(passo = 'dia', data_in = DATA_INICIAL, data_fim = DATA_FIM):
	conn = sql.connect("py_politica.db")
	cursor = conn.cursor()


	if passo == 'dia':

		sql_command = '''
		SELECT date(dataHorainicio),count(id_votacao)
		FROM votacao
		WHERE date(dataHorainicio) >= '{}' AND
			date(dataHorainicio) <= '{}'
		GROUP BY date(dataHorainicio);
	'''
		res = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()
		

	elif passo == 'mes':

		sql_command = '''
			SELECT strftime('%Y-%m', dataHoraInicio) as tmp, count(*) as cnt
			FROM votacao 
			WHERE date(dataHorainicio) >= '{}' AND
				date(dataHorainicio) <= '{}'
			GROUP BY tmp;
		'''	

		res = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()
		

	elif passo == 'ano':
		
		sql_command = '''
			SELECT strftime('%Y', dataHoraInicio) as tmp, count(*) as cnt 
			FROM votacao 
			WHERE date(dataHorainicio) >= '{}' AND
				date(dataHorainicio) <= '{}'
			GROUP BY tmp;
		'''	

		res = cursor.execute(sql_command.format(data_in,data_fim)).fetchall()
					

	return res
