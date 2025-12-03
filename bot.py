import csv
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('es_AR')

tipos_lesion = [
    "Esguince de tobillo", "Fractura de muñeca", "Contusión muscular",
    "Luxación de hombro", "Desgarro muscular", "Corte superficial",
    "Golpe en la cabeza", "Lesión de rodilla", "Tendinitis", "Contractura"
]
severidades = ["Leve", "Moderada", "Grave", "Alta"]
posiciones = ["Pilar", "Hooker", "Segunda línea", "Ala", "Octavo", "Medio scrum", "Apertura", "Centro", "Wing", "Fullback"]
medicos = [fake.name() for _ in range(3)]
categorias = ["Infantil", "Juvenil", "M15", "M17", "M19", "Plantel Superior", "Veteranos"]

consultas = []

# ...existing code...

for i in range(70):
    nombre = fake.first_name()
    apellido = fake.last_name()
    nombre_apellido = f"{nombre} {apellido}"
    dni = str(random.randint(20000000, 49999999))
    categoria = random.choice(categorias)
    posicion = random.choice(posiciones)
    marca_temporal = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    nombre_doctor = random.choice(medicos)
    fecha_obj = fake.date_between(start_date='-2y', end_date='today')
    fecha = fecha_obj.strftime("%d/%m/%Y")
    tipo_lesion = random.choice(tipos_lesion)
    severidad = random.choice(severidades)
    cuando_ocurrio_obj = fake.date_between(start_date='-2y', end_date=fecha_obj)
    cuando_ocurrio = cuando_ocurrio_obj.strftime("%d/%m/%Y")
    como_ocurrio = fake.sentence(nb_words=10)
    requiere_cirugia = random.choice(["Sí", "No"])
    puede_entrenar = random.choice(["Sí", "No"])
    fecha_prox_eval_obj = fecha_obj + timedelta(days=random.randint(7, 60))
    fecha_prox_eval = fecha_prox_eval_obj.strftime("%d/%m/%Y")
    observaciones = fake.sentence(nb_words=12)
    medicamentos = fake.word().capitalize() if random.random() < 0.5 else ""

    consultas.append([
        marca_temporal,
        nombre_doctor,
        fecha,
        nombre_apellido,
        dni,
        categoria,
        posicion,
        tipo_lesion,
        severidad,
        cuando_ocurrio,
        como_ocurrio,
        requiere_cirugia,
        puede_entrenar,
        fecha_prox_eval,
        observaciones,
        medicamentos
    ])


# Guardar como CSV
with open("consultas_medicas.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Marca temporal", "Nombre de Doctor", "Fecha", "Nombre y Apellido", "Dni", "Categoría",
        "Posición del jugador", "Tipo de lesión", "Severidad de la lesión", "¿Cuándo ocurrió la lesión?",
        "¿Como ocurrió la lesión?", "¿Requiere cirugía?", "¿Puede participar en entrenamientos?",
        "Fecha de próxima evaluación médica", "Observaciones adicionales", "Medicamentos recetados (si corresponde)"
    ])
    writer.writerows(consultas)

print("Archivo consultas_medicas.csv generado con éxito.")