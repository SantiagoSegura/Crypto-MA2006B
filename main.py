# streamlit run main.py
# https://crypto-ma2006b-casamonarca.streamlit.app/

import json
import sqlite3
import mysql.connector
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
import os
import base64
from Crypto.Util.Padding import unpad
from PIL import Image
import io

def main():
    # Crear barra lateral para la selección de la opción
    link_llaves = "llaves"
    with st.sidebar:
        option = option_menu(
        menu_title = "Menu",
        options = ['Cuestionario', 'Consulta de información', 'Dashboard'] 
    )

    if option == 'Cuestionario':       
        # Función para crear la tabla si no existe
        def crear_tabla():
            # Detalles de la conexión
            endpoint = "usersview.cbyy8g222bry.us-east-2.rds.amazonaws.com"
            port = 3306
            user = "admin"
            password = "123Segurita."
            database = "formularios"  # Reemplaza "nombre_de_tu_base_de_datos" con el nombre de tu base de datos
        
            try:
                # Establecer la conexión
                connection = mysql.connector.connect(
                    host=endpoint,
                    port=port,
                    user=user,
                    password=password,
                    database=database
                )
        
                # Verificar si la conexión fue exitosa
                if connection.is_connected():
                    #print("¡Conexión exitosa!")
        
                    # Crear la tabla si no existe
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
                    #print("Tabla creada o ya existente.")
        
                    # Guardar los cambios en la base de datos
                    connection.commit()
                    #print("Cambios guardados.")
        
                else:
                    print("¡Error de conexión!")
        
            except mysql.connector.Error as error:
                print("Error al conectarse a la base de datos:", error)
        
            finally:
                # Cerrar la conexión
                if 'connection' in locals() and connection.is_connected():
                    connection.close()
                    #print("Conexión cerrada.")
        
        # Función para cifrar datos usando AES
        def cifrar_datos(datos, secret_key):
            iv = get_random_bytes(AES.block_size)
            cipher = AES.new(secret_key, AES.MODE_CBC, iv)
            ciphertext = cipher.encrypt(pad(json.dumps(datos).encode(), AES.block_size))
            return iv, ciphertext
        
        # Función para guardar el JSON cifrado en la base de datos
        def guardar_json_cifrado(iv, ciphertext, nombre_usuario, fecha_atencion,edad, genero,tipo_poblacion):
            # Detalles de la conexión
            endpoint = "usersview.cbyy8g222bry.us-east-2.rds.amazonaws.com"
            port = 3306
            user = "admin"
            password = "123Segurita."
            database = "formularios" 
        
            try:
                # Establecer la conexión
                connection = mysql.connector.connect(
                    host=endpoint,
                    port=port,
                    user=user,
                    password=password,
                    database=database
                )
        
                # Verificar si la conexión fue exitosa
                if connection.is_connected():
                    #print("¡Conexión exitosa!")
        
                    # Insertar los datos en la tabla
                    cursor = connection.cursor()
                    cursor.execute("""
                    INSERT INTO formularios 
                    (nombre_usuario, fecha, genero, iv, formulario_cifrado, edad, tipo_poblacion) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""", (nombre_usuario, fecha_atencion, genero, iv, ciphertext, edad, tipo_poblacion))

                    print("Datos insertados correctamente.")
        
                    # Guardar los cambios en la base de datos
                    connection.commit()
                    print("Cambios guardados.")
        
                else:
                    print("¡Error de conexión!")
        
            except mysql.connector.Error as error:
                print("Error al conectarse a la base de datos:", error)
        
            finally:
                # Cerrar la conexión
                if 'connection' in locals() and connection.is_connected():
                    connection.close()
                    #print("Conexión cerrada.")

    
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
            # Crear el diccionario para almacenar las respuestas
            datos = {
                "fecha_atencion": str(st.date_input('Fecha de atención (yyyy-mm-dd)',
                                     min_value=min_date)),
                "tipo_persona": st.selectbox('Tipo de persona', ['Selecciona una opción'] + ['Adulto', 'Adulto', 'Niña acompañada', 'Niño acompañado', 
                                                                 'Adolescente acompañado', 'Niña no acompañada', 
                                                                 'Niño no acompañado', 'Adolescente no acompañado']),
                "telefono_contacto": st.text_input('Número telefónico de contacto'),
                "sexo": st.selectbox('Sexo', ['Selecciona una opción'] + ['Mujer LGBTTTIQ+', 'Mujer', 'Hombre LGBTTTIQ+', 'Hombre']),
                "fecha_nacimiento": str(st.date_input('Fecha de nacimiento (yyyy-mm-dd)',
                                     min_value=min_date)),
                "edad": st.number_input('Edad', min_value=0, max_value=150),
                "pais_origen": st.selectbox('País de origen', ['Selecciona una opción'] + ['México', 'Estados Unidos de América', 'Guatemala', 'Honduras',
                                                                'El Salvador', 'Venezuela', 'Nicaragua', 'Haití', 'Colombia',
                                                                'Cuba', 'Argentina', 'Afganistan', 'Siria', 'Alemania', 'Brasil',
                                                                'Perú', 'Guayana Francesa', 'Belice', 'Panamá', 'Ecuador']),
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
                "fecha_salida_pais_origen": str(st.date_input('Fecha en que salió de su país de origen')),
                "viajando": st.selectbox('¿Cómo se encuentra viajando?', ['Selecciona una opción'] +['Sola/o', 'Acompañada/o']),
                "viajo_como": st.text_input('¿Cómo viajó?'),
                "motivo_salida": st.text_area('¿Por qué razón tomó la decisión de salir de su país?'),
                "abuso_derechos_humanos_viaje": st.selectbox('Durante su viaje desde que salió de su país hasta antes de llegar a México, ¿Usted sufrió de algún abuso a sus Derechos Humanos?', ['Selecciona una opción'] +['Si', 'No']),
                "abuso_derechos_humanos_mexico": st.selectbox('Cuando usted entró a territorio mexicano, ¿Usted vivió algún abuso o agresión?',['Selecciona una opción'] + ['Si', 'No']),
                "pago_guia": st.selectbox('En algún momento de su camino, ¿Usted le pagó a algún guía para viajar?',['Selecciona una opción'] + ['Si', 'No']),
                "fecha_ingreso_mexico": str(st.date_input('Fecha en que ingresó a México (yyyy-mm-dd)',
                                     min_value=min_date)),
                "donde_ingreso_mexico": st.selectbox('¿Por dónde ingresó a México?', ['Selecciona una opción'] +['Tapachula', 'Tenosoique', 'Chetumal', 'Palenque', 'Matamoros', 'Reynosa', 'Veracruz', 'Tabasco', 'Chiapas']),
                "destino_final": st.selectbox('¿Cuál es su destino final?', ['Selecciona una opción'] +['México', 'Estados Unidos', 'Regresar a mi país de origen']),
                "red_apoyo_monterrey": st.selectbox('¿Cuenta con una red de apoyo en Monterrey?', ['Selecciona una opción'] +['Si', 'No']),
                "intento_ingresar_estados_unidos": st.selectbox('¿Usted ha intentado ingresar a Estados Unidos?', ['Selecciona una opción'] +['Si', 'No']),
                "red_apoyo_estados_unidos": st.selectbox('¿Usted cuenta con una red de apoyo en Estados Unidos?', ['Selecciona una opción'] +['Si', 'No']),
                "descripcion_red_apoyo": st.text_area('Descripción de la red de apoyo en Estados Unidos'),
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
            }
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
                    guardar_json_cifrado(iv, ciphertext, nombre_usuario, datos["fecha_atencion"],datos['edad'], datos["sexo"],datos['tipo_poblacion'])
        
                    # Descargar la llave privada
                    descargar_llave_privada(secret_key, nombre_usuario)
        
                    st.write("¡Formulario enviado y llave privada descargada!")
        
        if __name__ == '__main__':
            main_crypt()
        
        pass
    elif option == 'Consulta de información':
        #
        # Función para decifrar los datos usando la clave secreta AES
        def decifrar_datos(iv, encrypted_data, secret_key):
            cipher = AES.new(secret_key, AES.MODE_CBC, iv)
            decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
            return decrypted_data
        
        # Función para obtener los datos cifrados desde la base de datos
        def obtener_datos_cifrados(nombre_usuario):
            # Detalles de la conexión
            endpoint = "usersview.cbyy8g222bry.us-east-2.rds.amazonaws.com"
            port = 3306
            user = "admin"
            password = "123Segurita."
            database = "formularios"
        
            try:
                # Establecer la conexión
                connection = mysql.connector.connect(
                    host=endpoint,
                    port=port,
                    user=user,
                    password=password,
                    database=database
                )
        
                # Verificar si la conexión fue exitosa
                if connection.is_connected():
                    #print("¡Conexión exitosa!")
        
                    # Obtener los datos cifrados de la base de datos
                    cursor = connection.cursor()
                    cursor.execute("""SELECT iv, formulario_cifrado
                                      FROM formularios
                                      WHERE nombre_usuario = %s
                                      ORDER BY id DESC
                                      LIMIT 1""", (nombre_usuario,))
                    iv, encrypted_data = cursor.fetchone()
                    #print("Datos obtenidos correctamente.")
        
                    return iv, encrypted_data
        
                else:
                    print("¡Error de conexión!")
        
            except mysql.connector.Error as error:
                print("Error al conectarse a la base de datos:", error)
                return None, None
        
            finally:
                # Cerrar la conexión
                if 'connection' in locals() and connection.is_connected():
                    connection.close()
                    #print("Conexión cerrada.")
        
        # Función principal para decifrar los datos
        def decifrar_y_mostrar_datos(nombre_usuario, secret_key):
            try:
                # Obtener los datos cifrados desde la base de datos
                iv, encrypted_data = obtener_datos_cifrados(nombre_usuario)
        
                # Decifrar los datos
                decrypted_data = decifrar_datos(iv, encrypted_data, secret_key)
                formulario_desencriptado = json.loads(decrypted_data.decode())
                mostrar_ficha_tecnica(formulario_desencriptado)
            except Exception as e:
                st.error("Error al decifrar los datos. Asegúrate de haber seleccionado la clave secreta correcta.")
        
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
        
            # Dropdown para seleccionar el usuario
            endpoint = "usersview.cbyy8g222bry.us-east-2.rds.amazonaws.com"
            port = 3306
            user = "admin"
            password = "123Segurita."
            database = "formularios"
            
            try:
                # Establecer la conexión
                connection = mysql.connector.connect(
                    host=endpoint,
                    port=port,
                    user=user,
                    password=password,
                    database=database
                )
            
                # Verificar si la conexión fue exitosa
                if connection.is_connected():
                    #print("¡Conexión exitosa!")
            
                    # Obtener los nombres de usuario de la base de datos
                    cursor = connection.cursor()
                    cursor.execute("SELECT DISTINCT nombre_usuario FROM formularios")
                    nombres_usuarios = [row[0] for row in cursor.fetchall()]
                    #print("Nombres de usuarios obtenidos correctamente.")
            
                    # Cerrar la conexión
                    connection.close()
                    #print("Conexión cerrada.")
            
                else:
                    print("¡Error de conexión!")
            
            except mysql.connector.Error as error:
                print("Error al conectarse a la base de datos:", error)
                nombres_usuarios = []
            
            # Crear el dropdown para seleccionar un nombre de usuario
            nombre_usuario_seleccionado = st.selectbox("Selecciona un nombre de usuario:", ["Seleccione una opción"] + nombres_usuarios)
            
            # Subir la clave secreta
            secret_key = st.file_uploader("Subir clave secreta", type="txt")
        
            if secret_key is not None:
                # Decifrar y mostrar datos
                decifrar_y_mostrar_datos(nombre_usuario_seleccionado, secret_key.read())
        
        if __name__ == "__main__":
            main_decrypt()
        pass
    elif option == 'Consulta de información':
        
        def obtener_dataframe_completo():
            # Datos de conexión
            endpoint = "usersview.cbyy8g222bry.us-east-2.rds.amazonaws.com"
            port = 3306
            user = "admin"
            password = "123Segurita."
            database = "formularios"
            
            try:
                # Establecer la conexión
                connection = mysql.connector.connect(
                    host=endpoint,
                    port=port,
                    user=user,
                    password=password,
                    database=database
                )
                
                # Verificar si la conexión fue exitosa
                if connection.is_connected():
                    print("¡Conexión exitosa!")
                    
                    # Consultar toda la tabla
                    query = "SELECT * FROM formularios"
                    df = pd.read_sql(query, connection)
                    
                    # Cerrar la conexión
                    connection.close()
                    
                    return df
                else:
                    print("No se pudo conectar a la base de datos.")
                    return None
            except mysql.connector.Error as err:
                print(f"Error: {err}")
                return None
            
        def crear_dashboard(df):
            st.title("Dashboard de Formularios")
        
            # Gráfico de pie para género
            st.header("Distribución de Género")
            genero_counts = df['genero'].value_counts()
            fig1, ax1 = plt.subplots()
            ax1.pie(genero_counts, labels=genero_counts.index, autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            st.pyplot(fig1)
        
            # Gráfico de líneas para número de usuarios únicos por día
            st.header("Número de Usuarios Únicos por Día")
            df['fecha'] = pd.to_datetime(df['fecha'])
            usuarios_por_dia = df.groupby(df['fecha'].dt.date)['nombre_usuario'].nunique()
            fig2, ax2 = plt.subplots()
            ax2.plot(usuarios_por_dia.index, usuarios_por_dia.values)
            ax2.set_xlabel('Fecha')
            ax2.set_ylabel('Número de Usuarios Únicos')
            st.pyplot(fig2)
        
            # Gráfico de barras para edades en rangos
            st.header("Distribución de Edades")
            bins = [0, 18, 30, 40, 50, 60, 100]
            labels = ['0-18', '19-30', '31-40', '41-50', '51-60', '60+']
            df['rango_edad'] = pd.cut(df['edad'], bins=bins, labels=labels, right=False)
            rango_edad_counts = df['rango_edad'].value_counts().sort_index()
            fig3, ax3 = plt.subplots()
            ax3.bar(rango_edad_counts.index, rango_edad_counts.values)
            ax3.set_xlabel('Rango de Edad')
            ax3.set_ylabel('Número de Usuarios')
            st.pyplot(fig3)
            
        def main_dash():
            # Uso de las funciones
            df_formularios = obtener_dataframe_formulario()
            if df_formularios is not None:
                st.error("No esta vacio")
                df_formularios
                crear_dashboard(df_formularios)
            else:
                st.error("No se pudo obtener el DataFrame.")
            
            pass
            
        if __name__ == "__main__":
            main_dash()
        

if __name__ == '__main__':
    main()
