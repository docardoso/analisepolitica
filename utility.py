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
			res.add(info)

	return res
