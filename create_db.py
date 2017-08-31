import sqlite3 as sql

con = sql.connect('py_politica.db')
cursor = con.cursor()

cursor.execute('''
CREATE TABLE parlamentar( 
		id integer primary key AUTOINCREMENT,
		id_API integer not null,
		nome varchar(50) not null,
		casa char(2) not null);''')

cursor.execute('''
CREATE TABLE partido( 
		sigla varchar(5) not null,
		uf char(2) not null,
		primary key(sigla, uf));''')

cursor.execute('''
CREATE TABLE votacao( 
		id integer primary key AUTOINCREMENT,
		id_API integer not null,
		tipo varchar(10) not null,
		data date not null);''')

cursor.execute('''
CREATE TABLE filia( 
		id integer not null,
		sigla varchar(5) not null,
		uf char(2) not null,
		data_in date not null,
		data_out date null default null,
		primary key (id, sigla, uf, data_in),
		foreign key(id) references parlamentar(id),
		foreign key(sigla) references partido(sigla),
		foreign key(uf) references partido(uf));''')

cursor.execute('''
CREATE TABLE voto( 
		id_candidato integer not null,
		id_votacao integer not null,
		descricao integer not null,
		primary key(id_candidato, id_votacao),
		foreign key (id_votacao) references votacao(id),
		foreign key (id_candidato) references parlamentar(id));''')

con.commit()
con.close()