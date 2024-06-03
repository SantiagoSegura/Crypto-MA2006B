# streamlit run main.py
# https://crypto-ma2006b-casamonarca.streamlit.app/

import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
import base64
from Crypto.Util.Padding import unpad
from PIL import Image
import io
import pandas as pd
import plotly.express as px
import mysql.connector


# Función genérica para establecer conexión a la base de datos
def conectar_bd():
    endpoint = "usersview.cbyy8g222bry.us-east-2.rds.amazonaws.com"
    port = 3306
    user = "admin"
    password_db = "123Segurita."
    database = "formularios"
    try:
        connection = mysql.connector.connect(
            host=endpoint,
            port=port,
            user=user,
            password=password_db,
            database=database
        )
        return connection
    except mysql.connector.Error as error:
        st.error(f"Error al conectarse a la base de datos: {error}")
        return None

# Función para verificar credenciales contra la base de datos
def verificar_credenciales(username, password):
    connection = conectar_bd()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT password, rol FROM usuarios WHERE username = %s", (username,))
            result = cursor.fetchone()
            if result and result[0] == password:
                return result[1]
        finally:
            connection.close()
    return None

# Función para crear el usuario administrador si no existe
def crear_usuario_admin():
    connection = conectar_bd()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
            result = cursor.fetchone()
            if result[0] == 0:
                cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (%s, %s, %s)", ('admin', 'admin123', 'jerarquia_mayor'))
                connection.commit()
        finally:
            connection.close()

def login():
    # Crear el usuario administrador si no existe
    crear_usuario_admin()

    # Crear barra lateral para la selección de la opción
    # Variable de sesión para el estado de inicio de sesión
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.rol = None

    # Mostrar formulario de inicio de sesión si no está logueado
    if not st.session_state.logged_in:
        st.title("Inicio de Sesión")
        username = st.text_input("Nombre de usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Iniciar sesión"):
            rol = verificar_credenciales(username, password)
            if rol:
                st.session_state.logged_in = True
                st.session_state.rol = rol
                st.session_state.username = username
                st.success("Inicio de sesión exitoso")
                st.rerun()
            else:
                st.error("Nombre de usuario o contraseña incorrectos")
    else:
        # Crear barra lateral para la selección de la opción
        with st.sidebar:
            opciones_menu = ['Cuestionario']
            if st.session_state.rol in ["jerarquia_mayor", "jerarquia_media"]:
                opciones_menu.extend(['Consulta de información', 'Dashboard'])
            if st.session_state.rol == "jerarquia_mayor":
                opciones_menu.append('Administrar usuarios')
            option = option_menu(
                menu_title="Menu",
                options=opciones_menu
            )
            
            if st.button("Cerrar sesión"):
                st.session_state.logged_in = False
                st.session_state.rol = None
                st.rerun()
        
        main(option)


def main(option):
    if option == 'Cuestionario':
        
        def crear_tabla():
            connection = conectar_bd()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute('''CREATE TABLE IF NOT EXISTS formularios (
                                        id INT AUTO_INCREMENT PRIMARY KEY,
                                        nombre_usuario VARCHAR(255),
                                        fecha DATE,
                                        edad INT,
                                        genero VARCHAR(50),
                                        tipo_poblacion VARCHAR(255),
                                        iv BLOB,
                                        formulario_cifrado BLOB)''')
                    connection.commit()
                finally:
                    connection.close()
        
        # Función para cifrar datos usando AES
        def cifrar_datos(datos, secret_key):
            iv = get_random_bytes(AES.block_size)
            cipher = AES.new(secret_key, AES.MODE_CBC, iv)
            ciphertext = cipher.encrypt(pad(json.dumps(datos).encode(), AES.block_size))
            return iv, ciphertext
        
        # Función para guardar el JSON cifrado en la base de datos
        def guardar_json_cifrado(iv, ciphertext, nombre_usuario, fecha_atencion, edad, genero, tipo_poblacion):
            connection = conectar_bd()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("""
                    INSERT INTO formularios 
                    (nombre_usuario, fecha, genero, iv, formulario_cifrado, edad, tipo_poblacion) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""", (nombre_usuario, fecha_atencion, genero, iv, ciphertext, edad, tipo_poblacion))
                    connection.commit()
                finally:
                    connection.close()
        
        # Función para descargar la llave privada AES
        def descargar_llave_privada(secret_key, nombre_usuario):
            # Crear el contenido del archivo como bytes
            nombre_archivo = f"llave_privada_{nombre_usuario}.txt"
            contenido_archivo = secret_key
    
            # Crear un botón de descarga en la interfaz web
            st.download_button(
                label="Descargar llave privada",
                data=contenido_archivo,
                file_name=nombre_archivo,
                mime='text/plain'
            )
        
        def preguntas_cuestionario():
                min_date = datetime(1950, 1, 1)
                datos = {
                    "fecha_atencion": str(st.date_input('Fecha de atención (yyyy-mm-dd)', min_value=min_date)),
                    "tipo_persona": st.selectbox('Tipo de persona', ['Selecciona una opción'] + ['Adulto', 'Niña acompañada', 'Niño acompañado', 
                                                                     'Adolescente acompañado', 'Niña no acompañada', 
                                                                     'Niño no acompañado', 'Adolescente no acompañado']),
                    "telefono_contacto": st.text_input('Número telefónico de contacto'),
                    "sexo": st.selectbox('Sexo', ['Selecciona una opción'] + ['Mujer LGBTTTIQ+', 'Mujer', 'Hombre LGBTTTIQ+', 'Hombre']),
                    "fecha_nacimiento": str(st.date_input('Fecha de nacimiento (yyyy-mm-dd)', min_value=min_date)),
                    "edad": st.number_input('Edad', min_value=0, max_value=150),
                    "pais_origen": st.selectbox('País de origen', ['Selecciona una opción'] + ['México', 'Estados Unidos de América', 'Guatemala', 'Honduras',
                                                                    'El Salvador', 'Venezuela', 'Nicaragua', 'Haití', 'Colombia',
                                                                    'Cuba', 'Argentina', 'Afganistan', 'Siria', 'Alemania', 'Brasil',
                                                                    'Perú', 'Guayana Francesa', 'Belice', 'Panamá', 'Ecuador']),
                }

                # Mostrar la pregunta "fecha_salida_pais_origen" solo si "pais_origen" no es "México"
                if datos["pais_origen"] != "México":
                    datos["fecha_salida_pais_origen"] = str(st.date_input('Fecha en que salió de su país de origen'))
                    datos["donde_ingreso_mexico"]= st.selectbox('¿Por dónde ingresó a México?', ['Selecciona una opción'] +['Tapachula', 'Tenosoique', 'Chetumal', 'Palenque', 'Matamoros', 'Reynosa', 'Veracruz', 'Tabasco', 'Chiapas']),
                
                # Continúa con las demás preguntas
                datos.update({
                    "departamento_estado": st.text_input('Departamento / Estado'),
                    "estado_civil": st.selectbox('Estado Civil', ['Selecciona una opción'] + ['Casado / Casado', 'Divorciado / Divorciado', 'Soltera / Soltero',
                                                                   'Separada / Separada', 'Viuda / Viudo', 'Unión Libre']),
                    "tipo_poblacion": st.selectbox('Tipo de población', ['Selecciona una opción'] + ['Tránsito', 'MPP', 'Retornados', 'Refugiados',
                                                                          'Desplazados internos', 'Otra movilidad']),
                    "documento_identidad": st.selectbox('Documento de identidad', ['Selecciona una opción'] +['Tarjeta de identidad de país de origen',
                                                                                     'Certificado de nacionalidad / Acta de Nacimiento',
                                                                                     'Pasaporte', 'CURP', 'Documento Migratorio',
                                                                                     'Ningún documento']),
                    "hijos": st.selectbox('Hijos', ['Selecciona una opción'] +['Si', 'No']),
                    "leer_escribir": st.selectbox('¿Usted sabe leer y escribir?', ['Selecciona una opción'] +['Si', 'No']),
                    "ultimo_grado_estudio": st.selectbox('¿Cuál fue su último grado de estudio?', ['Selecciona una opción'] + ['Preescolar', 'Primaria',
                                                                                                      'Secundaria', 'Preparatoria',
                                                                                                      'Bachillerato técnico',
                                                                                                      'Licenciatura', 'Sin escolarizar']),
                    "ultimo_grado_academico": st.text_input('¿Cuál fue su último grado académico?'),
                    "idiomas": st.multiselect('Idiomas que domina', ['Selecciona una opción'] + ['Inglés', 'Español', 'Frances', 'Criollo haitiano',
                                                                       'Garífona', 'Otro idioma', 'Portugues']),
                    "viajando": st.selectbox('¿Cómo se encuentra viajando?', ['Selecciona una opción'] +['Sola/o', 'Acompañada/o']),
                    "viajo_como": st.text_input('¿Cómo viajó?'),
                    "motivo_salida": st.text_area('¿Por qué razón tomó la decisión de salir de su país?'),
                    "abuso_derechos_humanos_viaje": st.selectbox('Durante su viaje desde que salió de su país hasta antes de llegar a México, ¿Usted sufrió de algún abuso a sus Derechos Humanos?', ['Selecciona una opción'] +['Si', 'No']),
                    "abuso_derechos_humanos_mexico": st.selectbox('Cuando usted entró a territorio mexicano, ¿Usted vivió algún abuso o agresión?',['Selecciona una opción'] + ['Si', 'No']),
                    "pago_guia": st.selectbox('En algún momento de su camino, ¿Usted le pagó a algún guía para viajar?',['Selecciona una opción'] +['Si', 'No']),
                    "destino_final": st.selectbox('¿Cuál es su destino final?', ['Selecciona una opción'] +['México', 'Estados Unidos', 'Regresar a mi país de origen']),
                    "red_apoyo_monterrey": st.selectbox('¿Cuenta con una red de apoyo en Monterrey?', ['Selecciona una opción'] +['Si', 'No']),
                    "intento_ingresar_estados_unidos": st.selectbox('¿Usted ha intentado ingresar a Estados Unidos?', ['Selecciona una opción'] +['Si', 'No']),
                    "red_apoyo_estados_unidos": st.selectbox('¿Usted cuenta con una red de apoyo en Estados Unidos?', ['Selecciona una opción'] +['Si', 'No']),
                })

                if datos["red_apoyo_estados_unidos"] == "Si":
                    datos["descripcion_red_apoyo"] = st.text_area('Descripción de la red de apoyo en Estados Unidos')

                datos.update({
                    "estacion_migratoria": st.selectbox('¿Usted ha estado en alguna estación migratoria?', ['Selecciona una opción'] +['Si', 'No']),
                    "denuncia_formal": st.selectbox('Ante las vivencias de abuso de autoridad, agresiones y vulnerabilidad a Derechos Humanos, ¿Usted interpuso una denuncia formal?',['Selecciona una opción'] +['Si', 'No']),
                    "puede_regresar_pais": st.selectbox('¿Usted puede regresar a su país?', ['Selecciona una opción'] +['Si', 'No']),
                    "enfermedad": st.selectbox('¿Actualmente usted padece alguna enfermedad?', ['Selecciona una opción'] +['Si', 'No']),
                    "tratamiento_medico": st.text_area('¿Se encuentra o encontraba en algún tratamiento médico?'),
                    "alergia": st.selectbox('¿Usted padece algún tipo de alergia?', ['Selecciona una opción'] +['Si', 'No']),
                    "otros_albergues": st.selectbox('En su trayecto por México, ¿Usted se ha estado en algún otro albergue?', ['Selecciona una opción'] +['Si', 'No']),
                    "acceso_casa_monarca": st.selectbox('¿Se le brindó acceso al albergue de Casa Monarca?', ['Selecciona una opción'] +['Si', 'No']),
                    "servicios_brindados": st.multiselect('¿Cuáles servicios se le brindaron a la persona?', ['Selecciona una opción'] +['Agua y alimento', 'Alimento',
                                                                                                                 'Kit de higiene', 'Ropa y calzado',
                                                                                                                 'Acceso a higiene (Regadera)',
                                                                                                                 'Asesoría legal', 'Orientación legal',
                                                                                                                 'Orientación en búsqueda de empleo',
                                                                                                                 'Orientación en el acceso a la educación',
                                                                                                                 'Orientación en la búsqueda de vivienda',
                                                                                                                 'Orientación para acceder a servicios de salud',
                                                                                                                 'Orientación a servicios prisológicos',
                                                                                                                 'Canalización a servicios pricológicos',
                                                                                                                 'Atención psicosocial']),
                    "foto_frente": st.file_uploader('Fotografía de frente'),
                    "foto_perfil_izquierdo": st.file_uploader('Fotografía perfil izquierdo'),
                    "foto_perfil_derecho": st.file_uploader('Fotografía perfil derecho'),
                    "senas_particulares": st.text_area('Señas particulares'),
                    "contacto_emergencia": st.text_input('Contacto de emergencia'),
                    "ubicacion_contacto_emergencia": st.text_area('Geográficamente, ¿Dónde se encuentra su contacto de emergencia?'),
                    "observaciones_finales": st.text_area('Observaciones finales')
                })

                return datos
        
        # Función para preparar los datos antes de cifrarlos
        def preparar_datos(datos):
            datos_preparados = datos.copy()
            # Aquí puedes agregar cualquier transformación necesaria a los datos antes de cifrarlos
            return datos_preparados
        
        # Función para convertir la imagen a bytes en base64
        def imagen_a_base64(image):
            if image is not None:
                return base64.b64encode(image.getvalue()).decode('utf-8')
            return None
        
        # Función principal
        def main_crypt():
            # Agregar imagen en la parte superior izquierda
            st.image("logo_casa_monarca.png", use_column_width=False)
        
            # Crear la tabla si no existe
            crear_tabla()
        
            # Recolectar datos del formulario
            nombre_usuario = st.text_input('Nombre completo')
        
            datos = preguntas_cuestionario()
        
            # Convertir imágenes a bytes en base64 y agregarlas al diccionario de datos
            datos["foto_frente"] = imagen_a_base64(datos["foto_frente"])
            datos["foto_perfil_izquierdo"] = imagen_a_base64(datos["foto_perfil_izquierdo"])
            datos["foto_perfil_derecho"] = imagen_a_base64(datos["foto_perfil_derecho"])
        
            # Preparar datos para cifrar
            datos_preparados = preparar_datos(datos)
        
            
            # Botón para enviar
            if st.button('Enviar'):
                # Validar que no haya respuestas vacías o "Selecciona una opción"
                if any(value == 'Selecciona una opción' or value == '' for value in datos.values()):
                    st.error("Falta información. Por favor complete todas las preguntas.")
                else:
                    # Generar clave secreta AES
                    secret_key = get_random_bytes(32)
        
                    # Cifrar los datos
                    iv, ciphertext = cifrar_datos(datos, secret_key)
        
                    # Guardar JSON cifrado en la base de datos
                    guardar_json_cifrado(iv, ciphertext, nombre_usuario, datos["fecha_atencion"], datos['edad'], datos["sexo"], datos["tipo_poblacion"])
        
                    # Descargar la llave privada
                    descargar_llave_privada(secret_key, nombre_usuario)
        
                    st.write("¡Formulario enviado y llave privada descargada!")
        
        if __name__ == '__main__':
            main_crypt()
        
        pass
    
    elif option == 'Consulta de información':
    # Función para decifrar los datos usando la clave secreta AES
        def decifrar_datos(iv, encrypted_data, secret_key):
            cipher = AES.new(secret_key, AES.MODE_CBC, iv)
            decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
            return decrypted_data
        
        # Función para obtener los datos cifrados desde la base de datos
        def obtener_datos_cifrados(nombre_usuario, fecha_inicio, fecha_fin):
            connection = conectar_bd()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("""SELECT iv, formulario_cifrado
                                      FROM formularios
                                      WHERE nombre_usuario = %s AND fecha BETWEEN %s AND %s
                                      ORDER BY id DESC
                                      LIMIT 1""", (nombre_usuario, fecha_inicio, fecha_fin))
                    result = cursor.fetchone()
                    if result:
                        return result[0], result[1]
                finally:
                    connection.close()
            return None, None
                    
        # Función principal para decifrar los datos
        def decifrar_y_mostrar_datos(nombre_usuario, secret_key, fecha_inicio, fecha_fin):
            try:
                # Obtener los datos cifrados desde la base de datos
                iv, encrypted_data = obtener_datos_cifrados(nombre_usuario, fecha_inicio, fecha_fin)
                if iv and encrypted_data:
                    # Decifrar los datos
                    decrypted_data = decifrar_datos(iv, encrypted_data, secret_key)
                    formulario_desencriptado = json.loads(decrypted_data.decode())
                    mostrar_ficha_tecnica(formulario_desencriptado)
                else:
                    st.error("No se encontraron datos para el usuario y el rango de fechas seleccionados.")
            except Exception as e:
                st.error(f"Error al decifrar los datos: {e}")
        
        # Función para mostrar la información del formulario en formato de ficha técnica
        def mostrar_ficha_tecnica(formulario):
            st.subheader("Ficha Técnica")
            for pregunta, respuesta in formulario.items():
                if pregunta in ["foto_frente", "foto_perfil_izquierdo", "foto_perfil_derecho"] and respuesta is not None:
                    decoded_image_data = base64.b64decode(respuesta)
                    image = Image.open(io.BytesIO(decoded_image_data))
                    st.image(image, caption=f"**{pregunta.capitalize()}:**")
                else:
                    # Si la pregunta no corresponde a una de las preguntas de imágenes, mostrarla normalmente
                    st.write(f"**{pregunta.capitalize()}:** {respuesta}")
        
        # Función principal
        def main_decrypt():
            # Agregar imagen en la parte superior izquierda
            st.image("logo_casa_monarca.png", use_column_width=False)
        
            st.title("Desencriptar Información")

            # Filtro de fecha
            st.sidebar.header("Filtro de Fechas")
            fecha_inicio = st.sidebar.date_input("Fecha de inicio", value=datetime.now())
            fecha_fin = st.sidebar.date_input("Fecha de fin", value=datetime.now())
        
            # Dropdown para seleccionar el usuario
            connection = conectar_bd()
            nombres_usuarios = []
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT DISTINCT nombre_usuario FROM formularios WHERE fecha BETWEEN %s AND %s", (fecha_inicio, fecha_fin))
                    nombres_usuarios = [row[0] for row in cursor.fetchall()]
                finally:
                    connection.close()
            
            # Crear el dropdown para seleccionar un nombre de usuario
            nombre_usuario_seleccionado = st.selectbox("Selecciona un nombre de usuario:", ["Seleccione una opción"] + nombres_usuarios)
            
            # Subir la clave secreta
            secret_key = st.file_uploader("Subir clave secreta", type="txt")
        
            if secret_key is not None and nombre_usuario_seleccionado != "Seleccione una opción":
                # Decifrar y mostrar datos
                decifrar_y_mostrar_datos(nombre_usuario_seleccionado, secret_key.read(), fecha_inicio, fecha_fin)
        
        if __name__ == "__main__":
            main_decrypt()
        pass
    
    
    elif option == 'Dashboard':
        def obtener_dataframe_completo():
            connection = conectar_bd()
            if connection:
                try:
                    query = "SELECT * FROM formularios"
                    df = pd.read_sql(query, connection)
                    return df
                finally:
                    connection.close()
            return None

        def crear_dashboard(df):
            st.title("Dashboard de Formularios")
            
            # Convertir la columna 'fecha' a tipo datetime
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')  # 'coerce' maneja los errores de conversión
            
            # Obtener fechas mínima y máxima del DataFrame
            fecha_min = df['fecha'].min()
            fecha_max = df['fecha'].max()
            
            # Filtro de fecha
            st.sidebar.header("Filtro de Fechas")
            fecha_inicio = st.sidebar.date_input("Fecha de inicio", value=pd.Timestamp(fecha_min).to_pydatetime(), min_value=pd.Timestamp(fecha_min).to_pydatetime(), max_value=pd.Timestamp(fecha_max).to_pydatetime())
            fecha_fin = st.sidebar.date_input("Fecha de fin", value=pd.Timestamp(fecha_max).to_pydatetime(), min_value=pd.Timestamp(fecha_min).to_pydatetime(), max_value=pd.Timestamp(fecha_max).to_pydatetime())
            
            # Filtrar por fechas seleccionadas
            df_filtrado = df[(df['fecha'] >= pd.Timestamp(fecha_inicio)) & (df['fecha'] <= pd.Timestamp(fecha_fin))]
            
            # Número total de usuarios
            st.header(f"Número Total de Usuarios: {df_filtrado['nombre_usuario'].nunique()}")
            
            # Gráfico de líneas para número de usuarios únicos por día
            st.header("Número de Usuarios Únicos por Día")
            usuarios_por_dia = df_filtrado.groupby(df_filtrado['fecha'].dt.date)['nombre_usuario'].nunique().reset_index()
            usuarios_por_dia.columns = ['Fecha', 'Usuarios Únicos']
            fig1 = px.line(usuarios_por_dia, x='Fecha', y='Usuarios Únicos', title='Número de Usuarios Únicos por Día')
            st.plotly_chart(fig1)
            
            # Gráfico de barras para edades en rangos
            st.header("Distribución de Edades")
            bins = [0, 18, 30, 40, 50, 60, 100]
            labels = ['0-18', '19-30', '31-40', '41-50', '51-60', '60+']
            df_filtrado['rango_edad'] = pd.cut(df_filtrado['edad'], bins=bins, labels=labels, right=False)
            rango_edad_counts = df_filtrado['rango_edad'].value_counts().sort_index().reset_index()
            rango_edad_counts.columns = ['Rango de Edad', 'Número de Usuarios']
            fig2 = px.bar(rango_edad_counts, x='Rango de Edad', y='Número de Usuarios', title='Distribución de Edades')
            st.plotly_chart(fig2)
            
            # Gráfico de pie para distribución de género
            st.header("Distribución de Género")
            genero_counts = df_filtrado['genero'].value_counts()
            fig3 = px.pie(values=genero_counts.values, names=genero_counts.index, title='Distribución de Género')
            st.plotly_chart(fig3)
        
        def main_dash():
            # Uso de las funciones
            df_formularios = obtener_dataframe_completo()
            if df_formularios is not None:
                crear_dashboard(df_formularios)
            else:
                st.error("No se pudo obtener la información.")
            
            pass
            
        if __name__ == "__main__":
            main_dash()
    
    elif option == 'Administrar usuarios':
        # Funciones para la administración de usuarios
        def crear_tabla_usuarios():
            connection = conectar_bd()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                                    id INT AUTO_INCREMENT PRIMARY KEY,
                                    username VARCHAR(255) UNIQUE,
                                    password VARCHAR(255),
                                    rol VARCHAR(50))''')
                    connection.commit()
                finally:
                    connection.close()

        def agregar_usuario(username, password, rol):
            connection = conectar_bd()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (%s, %s, %s)", (username, password, rol))
                    connection.commit()
                finally:
                    connection.close()

        def obtener_usuarios():
            connection = conectar_bd()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT username, rol FROM usuarios")
                    usuarios = cursor.fetchall()
                    return {usuario[0]: {"rol": usuario[1]} for usuario in usuarios}
                finally:
                    connection.close()
            return {}

        def actualizar_rol_usuario(username, nuevo_rol):
            connection = conectar_bd()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE usuarios SET rol = %s WHERE username = %s", (nuevo_rol, username))
                    connection.commit()
                finally:
                    connection.close()

        def eliminar_usuario(username):
            connection = conectar_bd()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("DELETE FROM usuarios WHERE username = %s", (username,))
                    connection.commit()
                finally:
                    connection.close()

        crear_tabla_usuarios()
        
        st.header("Administrar usuarios")
        
        # Obtener la lista actual de usuarios
        USUARIOS = obtener_usuarios()
        
        # Sección para actualizar el rol de un usuario existente
        st.subheader("Actualizar Rol de Usuario")
        if USUARIOS:
            usuario_seleccionado = st.selectbox("Seleccionar usuario", list(USUARIOS.keys()))
            nuevo_rol = st.selectbox("Seleccionar nuevo rol", ["jerarquia_mayor", "jerarquia_media", "jerarquia_menor"])
            if st.button("Actualizar rol"):
                actualizar_rol_usuario(usuario_seleccionado, nuevo_rol)
                st.success(f"Rol de {usuario_seleccionado} actualizado a {nuevo_rol}")
        else:
            st.warning("No hay usuarios registrados.")
        
        # Sección para agregar un nuevo usuario
        st.subheader("Agregar Nuevo Usuario")
        nuevo_usuario = st.text_input("Nombre de usuario nuevo")
        nueva_contrasena = st.text_input("Contraseña nueva", type="password")
        nuevo_rol = st.selectbox("Rol del nuevo usuario", ["jerarquia_mayor", "jerarquia_media", "jerarquia_menor"], key='nuevo_rol')
        if st.button("Agregar usuario"):
            if nuevo_usuario in USUARIOS:
                st.error("El nombre de usuario ya existe.")
            else:
                agregar_usuario(nuevo_usuario, nueva_contrasena, nuevo_rol)
                st.success(f"Usuario {nuevo_usuario} agregado con rol {nuevo_rol}")
        
        # Sección para eliminar un usuario existente
        st.subheader("Eliminar Usuario")
        if USUARIOS:
            usuario_a_eliminar = st.selectbox("Seleccionar usuario a eliminar", list(USUARIOS.keys()), key='usuario_a_eliminar')
            if st.button("Eliminar usuario"):
                eliminar_usuario(usuario_a_eliminar)
                st.success(f"Usuario {usuario_a_eliminar} eliminado")
        else:
            st.warning("No hay usuarios registrados.")

if __name__ == '__main__':
    login()

