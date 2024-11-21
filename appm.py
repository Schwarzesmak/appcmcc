from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuración para la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///edificio_universidad.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -------------------- MODELOS --------------------

# Representación de un Departamento
class Departamento(db.Model):
    __tablename__ = 'departamento'
    codigo = db.Column(db.String, primary_key=True)
    piso = db.Column(db.Integer, nullable=False)
    numero = db.Column(db.String, nullable=False)
    ocupado = db.Column(db.Boolean, default=False)
    rut_propietario = db.Column(db.String, nullable=True)
    estado_actual = db.Column(db.String, nullable=False)
    rut_arrendatario = db.Column(db.String, nullable=True)
    inicio_contrato = db.Column(db.Date, nullable=True)
    fin_contrato = db.Column(db.Date, nullable=True)
    comentarios = db.Column(db.String, nullable=True)
    habitaciones = db.Column(db.Integer, nullable=False)
    banos = db.Column(db.Integer, nullable=False)

# Representación de Cuotas de Gastos Comunes
class GastoComun(db.Model):
    __tablename__ = 'gasto_comun'
    id_gasto = db.Column(db.Integer, primary_key=True)
    mes = db.Column(db.String, nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    monto_pagado = db.Column(db.Float, default=0.0)
    fecha_pago = db.Column(db.Date, nullable=True)
    pendiente = db.Column(db.Boolean, default=True)
    codigo_depto = db.Column(db.String, db.ForeignKey('departamento.codigo'), nullable=False)
    rut_responsable = db.Column(db.String, nullable=False)
    nombre_responsable = db.Column(db.String, nullable=False)
    telefono_contacto = db.Column(db.String, nullable=False)

    departamento = db.relationship('Departamento', backref='gastos_comunes')

# Crear las tablas en la base de datos
with app.app_context():
    db.create_all()

# -------------------- RUTAS --------------------

# Listar todas las cuotas de gastos comunes
@app.route('/gastos', methods=['GET'])
def listar_gastos():
    gastos = GastoComun.query.all()
    return jsonify([{
        'id_gasto': gasto.id_gasto,
        'mes': gasto.mes,
        'anio': gasto.anio,
        'monto_pagado': gasto.monto_pagado,
        'fecha_pago': gasto.fecha_pago,
        'pendiente': gasto.pendiente,
        'codigo_depto': gasto.codigo_depto,
        'rut_responsable': gasto.rut_responsable,
        'nombre_responsable': gasto.nombre_responsable,
        'telefono_contacto': gasto.telefono_contacto
    } for gasto in gastos])

# Marcar un gasto como pagado
@app.route('/gastos/pago', methods=['POST'])
def registrar_pago():
    data = request.get_json()
    codigo_depto = data.get('codigo_depto')
    mes = data.get('mes')
    anio = data.get('anio')
    fecha_pago = data.get('fecha_pago')

    gasto = GastoComun.query.filter_by(codigo_depto=codigo_depto, mes=mes, anio=anio).first()
    if not gasto:
        return jsonify({'mensaje': 'Gasto no encontrado'}), 404

    gasto.monto_pagado = gasto.monto_pagado or 0.0  # Evitar errores si no tiene un valor inicial
    gasto.fecha_pago = datetime.strptime(fecha_pago, '%Y-%m-%d')
    gasto.pendiente = False

    db.session.commit()
    return jsonify({'mensaje': 'El gasto ha sido registrado como pagado con éxito'})

# Listar cuotas pendientes hasta un mes y año específicos
@app.route('/gastos/pendientes', methods=['GET'])
def listar_pendientes():
    mes = int(request.args.get('mes'))
    anio = int(request.args.get('anio'))

    pendientes = GastoComun.query.filter(
        (GastoComun.anio < anio) | ((GastoComun.anio == anio) & (GastoComun.mes <= mes)),
        GastoComun.pendiente == True
    ).all()

    return jsonify([{
        'departamento': gasto.codigo_depto,
        'periodo': f"{gasto.mes}-{gasto.anio}",
        'monto': gasto.monto_pagado or 0.0
    } for gasto in pendientes])

# Crear un nuevo gasto común
@app.route('/gastos', methods=['POST'])
def agregar_gasto():
    data = request.get_json()
    nuevo_gasto = GastoComun(
        mes=data['mes'],
        anio=data['anio'],
        monto_pagado=0.0,
        fecha_pago=None,
        pendiente=True,
        codigo_depto=data['codigo_depto'],
        rut_responsable=data['rut_responsable'],
        nombre_responsable=data['nombre_responsable'],
        telefono_contacto=data['telefono_contacto']
    )
    db.session.add(nuevo_gasto)
    db.session.commit()
    return jsonify({'mensaje': 'Gasto común registrado con éxito'}), 201

if __name__ == '__main__':
    app.run(debug=True)
