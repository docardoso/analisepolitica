import sqlite3 as SQL 

def filia(parlamentar):
	conn = SQL.connect('py_politica.db')
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
	conn = SQL.connect('py_politica.db')
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
	conn = SQL.connect('py_politica.db')
	cursor = conn.cursor()
	filia_parlamentar = 0

	parlamentares = cursor.execute('''SELECT DISTINCT id_candidato 
		FROM voto NATURAL JOIN votacao 
		WHERE sigla = '{}' '''.format(partido)).fetchall()


	for parlamentar in parlamentares:
		filia_parlamentar += N_filia(parlamentar[0])

	return filia_parlamentar

