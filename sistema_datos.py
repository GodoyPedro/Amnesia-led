from modulos import *
from imagenes_ascii import *

class sistema_datos:

    def __init__(self):
        self.diccionario_pedidos = {}
        self.diccionario_pedidos_json = {}
        self.ids_nombres_pedido_lista = []
        self.ids_nombres_pedido_parsed = []
        self.direccion_csv_pedidos = ""
        self.direccion_csv_paneles = ""
        self.direccion_csv_requerimientos = ""
        self.direccion_csv_correo = ""
        self.diccionario_pedidos = {
            "exitosos":[],
            "fallidos":[]
        }

    def comparador_fechas(self, fecha_diccionario_1, fecha_diccionario_2):

        dia_1,mes_1 = list(map(int,fecha_diccionario_1["fecha"].split("/")))
        dia_2,mes_2 = list(map(int,fecha_diccionario_2["fecha"].split("/")))
        if mes_1 < mes_2:
            return 1
        elif mes_1 == mes_2:
            if dia_1 < dia_2:
                return 1
            elif dia_1 > dia_2:
                return -1
            else:
                return 0
        elif mes_1 > mes_2:
            return -1
        else:
            return 0

    def obtener_json_desde_archivo(self, nombre_json):
        try:
            with open(nombre_json, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
    
        except FileNotFoundError:
            raise FileNotFoundError

    def sacar_tildes(self, texto):
        return ''.join(x for x in unicodedata.normalize('NFD', texto) if unicodedata.category(x) != 'Mn')

    def limpiar_texto(self, texto):
        return self.sacar_tildes("".join([x for x in texto if x==" " or x in "0123456789" or x.isalpha()]))
    
    def dejar_solo_numeros(self, texto):
        return "".join([x for x in texto if x in "0123456789"])

    def decidir_texto_a_escribir(self, codigo_salida, dato):
        texto_a_escribir = ""
        if codigo_salida == 0:
            texto_a_escribir = dato
        elif codigo_salida == 1:
            texto_a_escribir = "error"
        
        return texto_a_escribir

    def obtener_diccionario_datos(self, numero_pedido, datos_usuario, datos_pedido_nombre, datos_pedido_cantidad, fecha_pedido, datos_numero_calle):

        datos_usuario_dict = {
            "id_pedido":"",
            "facturacion":{
                "nombre": "",
                "direccion":"",
                "ciudad":"",
                "provincia":"",
                "cp":"",
                "numero_casa":""
            },
            "datos":{
                "email":"",
                "telefono":""
            },
            "envio":{
                "nombre":"",
                "direccion":"",
                "ciudad":"",
                "provincia":"",
                "cp":"",
                "numero_casa":""
            },
            "nota":"",
            "fecha":"",
            "productos":[]
        }

        # Si el envio tiene mas de 5 elementos entonces no lo voy a cargar
        # En el metodo escribir_csv_lista_pedidos el nombre lo tendria que sacar desde facturacion, no desde envio
        # En todas las asignaciones de facturacion y envio tengo que limpiar la string
        facturacion = datos_usuario[0]
        email = datos_usuario[1][-1]
        telefono = datos_usuario[2][-1]
        envio = datos_usuario[3]
        nota = datos_usuario[4][1] if len(datos_usuario) == 5 else "Sin nota"
        numero_calle = datos_numero_calle if len(datos_numero_calle) > 0 else ["0","0"]

        # 0 si salio bien
        # 1 si salio mal
        codigo_salida = 0

        if len(envio) > 5:
            print("@"*50)
            print("@"*50)
            print("@"*50)
            codigo_salida = 1

        datos_usuario_dict["id_pedido"] = numero_pedido

        datos_usuario_dict["facturacion"]["nombre"] = self.limpiar_texto(facturacion[0])
        datos_usuario_dict["facturacion"]["direccion"] = self.limpiar_texto(facturacion[1])
        datos_usuario_dict["facturacion"]["ciudad"] = self.limpiar_texto(facturacion[2].replace(",","").replace('"',""))
        datos_usuario_dict["facturacion"]["provincia"] = self.limpiar_texto(facturacion[3])
        datos_usuario_dict["facturacion"]["cp"] = facturacion[4]
        datos_usuario_dict["facturacion"]["numero_casa"] = numero_calle[0]

        datos_usuario_dict["datos"]["email"] = email
        datos_usuario_dict["datos"]["telefono"] = telefono
        
        datos_usuario_dict["envio"]["nombre"] = self.limpiar_texto(self.decidir_texto_a_escribir(codigo_salida,envio[0]))
        datos_usuario_dict["envio"]["direccion"] = self.limpiar_texto(self.decidir_texto_a_escribir(codigo_salida,envio[1]))
        datos_usuario_dict["envio"]["ciudad"] = self.limpiar_texto(self.decidir_texto_a_escribir(codigo_salida,envio[2]))
        datos_usuario_dict["envio"]["provincia"] = self.limpiar_texto(self.decidir_texto_a_escribir(codigo_salida,envio[3]))
        datos_usuario_dict["envio"]["cp"] = self.dejar_solo_numeros(self.decidir_texto_a_escribir(codigo_salida,envio[4]))
        datos_usuario_dict["envio"]["numero_casa"] = self.decidir_texto_a_escribir(codigo_salida, numero_calle[1] if len(numero_calle) == 2 else numero_calle[0])

        datos_usuario_dict["nota"] = nota
        datos_usuario_dict["fecha"] = fecha_pedido

        for nombre, cantidad in zip(datos_pedido_nombre, datos_pedido_cantidad):
            datos_usuario_dict["productos"].append([self.sacar_tildes(nombre), "x"+cantidad])

        return [codigo_salida,datos_usuario_dict]

        # En vez de 2 listas, un diccionario con 2 claves "exitosos", "fallidos", dependiendo del codigo_salida que esta en [0]
        # guardo el diccionario de [1] en el diccionario de dos claves

    def sumar_requerimientos(self, lista_requerimientos, diccionario_plantilla):
        diccionario_suma_requerimientos = diccionario_plantilla
        del diccionario_suma_requerimientos["id_panel"]

        for c,v in diccionario_suma_requerimientos.items():
            for requerimiento in lista_requerimientos:
                diccionario_suma_requerimientos[c] += requerimiento[c]

        return diccionario_suma_requerimientos

    def escribir_archivos_csv(self, diccionario_pedidos, datos_productos):

        encabezado_columnas_pedidos = ["Id_Pedido", "Fecha", "Nombre", "Datos_pedido"]
        encabezado_columnas_paneles = ["Cantidades", "Full Specturm", "Mixto", "Calido"]

        fecha_actual = date.today().strftime("%d-%m-%y")
        direccion_desde_directorio_local = os.path.join(r"archivos\csv\historial", fecha_actual)
        direccion_a_comprobar = os.path.join(os.getcwd(),direccion_desde_directorio_local)
        fecha = f'{date.today().strftime("%d-%m")}_{datetime.now().strftime("%H.%M.%S")}'

        self.direccion_csv_paneles_ultimo = os.path.join(r"archivos\csv\ultimo", f'lista_paneles_{fecha}.csv')
        self.direccion_csv_requerimientos_ultimo = os.path.join(r"archivos\csv\ultimo", f'lista_requerimientos_{fecha}.csv')
        self.direccion_csv_pedidos_ultimo = os.path.join(r"archivos\csv\ultimo", f'lista_pedidos_{fecha}.csv')

        self.direccion_csv_paneles = os.path.join(direccion_desde_directorio_local, f'lista_paneles_{fecha}.csv')
        self.direccion_csv_requerimientos = os.path.join(direccion_desde_directorio_local, f'lista_requerimientos_{fecha}.csv')
        self.direccion_csv_pedidos = os.path.join(direccion_desde_directorio_local, f'lista_pedidos_{fecha}.csv')
        
        if not os.path.exists(direccion_a_comprobar):   
            os.makedirs(direccion_a_comprobar)

        ## Borro los archivos de la carpeta ultimo
        folder = r'archivos\csv\ultimo'
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

        tiempo_espera_maximo = 10

        while any([f for f in listdir(r"archivos\csv\ultimo") if isfile(join(r"archivos\csv\ultimo", f))]) and tiempo_espera_maximo > 0:
            time.sleep(1)
            print("Esperando")
            tiempo_espera_maximo -= 1

        #Full-Spectrum, Mixto, Calido
        diccionario_indices_tipos = {
            "f":0,
            "m":1,
            "c":2
        }
        diccionario_cantidad_paneles = {
            "100":[0,0,0],
            "200":[0,0,0],
            "300":[0,0,0],
            "400":[0,0,0],
            "500":[0,0,0],
            "ctz":[0,0,0],
            "sam":[0,0,0],
            "0":[0,0,0]
        }
        diccionario_a_escribir = {
            "Cantidades":"",
            "Full Specturm":"",
            "Mixto":"",
            "Calido":""
        }
        claves_importantes = [
            "led_full",
            "led_calido",
            "chapa_atras",
            "chapa_adelante",
            "ficha_macho",
            "cooler",
            "chapa_canaleta_100_200",
            "chapa_canaleta_300",
            "chapa_canaleta_400_500",
            "chapa_doble",
            "remaches",
            "conector_doble",
            "prensacable",
            "timer",
            "poleas",
            "carpa_60x60",
            "carpa_80x80",
            "carpa_100x100",
            "carpa_120x120"
        ]
        lista_requerimientos_productos = []
        claves = list(diccionario_cantidad_paneles.keys())[:-1]

        lista_pedidos_completa = [elemento for sub_lista in diccionario_pedidos.values() for elemento in sub_lista]

        for diccionario in lista_pedidos_completa:
            for producto in diccionario["productos"]:
                nombre = producto[0]
                lista_requerimientos_productos.append(datos_productos[nombre])
                codigo, cantidad = datos_productos[nombre]["id_panel"].split(" x ")
                if codigo != "ctz" and codigo != "sam" and codigo != "0" and codigo != "error":
                    diccionario_cantidad_paneles[codigo[:-1]][diccionario_indices_tipos[codigo[-1]]] += int(cantidad) 
                else:
                    diccionario_cantidad_paneles[codigo][0] += int(cantidad) 

        diccionario_suma_requerimientos = self.sumar_requerimientos(lista_requerimientos_productos, datos_productos["plantilla"])

        try:
            with open(self.direccion_csv_pedidos, 'w', newline='') as archivo_historial, open(self.direccion_csv_pedidos_ultimo, 'w', newline='') as archivo_ultimo:
                escritor_csv_historial = csv.DictWriter(archivo_historial, fieldnames=encabezado_columnas_pedidos)
                escritor_csv_ultimo = csv.DictWriter(archivo_ultimo, fieldnames=encabezado_columnas_pedidos)
                escritor_csv_historial.writeheader()
                escritor_csv_ultimo.writeheader()

                fecha_anterior = ""
                fecha_a_escribir = ""

                lista_pedidos_completa = [elemento for sub_lista in diccionario_pedidos.values() for elemento in sub_lista]
                
                lista_pedidos_completa.sort(key=cmp_to_key(self.comparador_fechas),reverse=True)

                for diccionario in lista_pedidos_completa:
                    
                    fecha_actual = diccionario["fecha"]
                    if fecha_anterior != fecha_actual:
                        fecha_a_escribir = fecha_actual
                    elif fecha_anterior == fecha_actual:
                        fecha_a_escribir = " "

                    fecha_anterior = fecha_actual

                    diccionario_a_escribir = {
                        "Id_Pedido": diccionario["id_pedido"],
                        "Fecha": fecha_a_escribir,
                        "Nombre": diccionario["facturacion"]["nombre"],
                        "Datos_pedido": " --- ".join([" ".join(x) for x in diccionario["productos"]])
                    }

                    self.ids_nombres_pedido_lista.append([diccionario["id_pedido"],diccionario["facturacion"]["nombre"]])

                    escritor_csv_historial.writerow(diccionario_a_escribir)
                    escritor_csv_ultimo.writerow(diccionario_a_escribir)

            self.ids_nombres_pedido_parsed = list(map(" ".join,self.ids_nombres_pedido_lista))

        except IOError:
            print("I/O error")


        try:
            with open(self.direccion_csv_paneles, 'w', newline='') as archivo_historial, open(self.direccion_csv_paneles_ultimo, 'w', newline='') as archivo_ultimo:
                escritor_csv_historial = csv.DictWriter(archivo_historial, fieldnames=encabezado_columnas_paneles)
                escritor_csv_ultimo = csv.DictWriter(archivo_ultimo, fieldnames=encabezado_columnas_paneles)
                escritor_csv_historial.writeheader()
                escritor_csv_ultimo.writeheader()

                for clave in claves:
                    diccionario_a_escribir = {
                        "Cantidades":clave,
                        "Full Specturm":diccionario_cantidad_paneles[clave][0],
                        "Mixto":diccionario_cantidad_paneles[clave][1],
                        "Calido":diccionario_cantidad_paneles[clave][2]
                    }
                    escritor_csv_historial.writerow(diccionario_a_escribir)
                    escritor_csv_ultimo.writerow(diccionario_a_escribir)
        except IOError:
            print("I/O error")

        try:
            with open(self.direccion_csv_requerimientos, 'w', newline='') as archivo_historial, open(self.direccion_csv_requerimientos_ultimo, 'w', newline='') as archivo_ultimo:
                escritor_csv_historial = csv.DictWriter(archivo_historial, fieldnames=claves_importantes)
                escritor_csv_ultimo = csv.DictWriter(archivo_ultimo, fieldnames=claves_importantes)
                escritor_csv_historial.writeheader()
                escritor_csv_ultimo.writeheader()

                escritor_csv_historial.writerow({clave:diccionario_suma_requerimientos[clave] for clave in claves_importantes})
                escritor_csv_ultimo.writerow({clave:diccionario_suma_requerimientos[clave] for clave in claves_importantes})
        except IOError:
            print("I/O error")

    def escribir_excel(self):
        
        tiempo_espera_maximo = 10

        while len([f for f in listdir(r"archivos\csv\ultimo") if isfile(join(r"archivos\csv\ultimo", f))]) != 3 and tiempo_espera_maximo > 0:
            time.sleep(1)
            print("Esperando")
            tiempo_espera_maximo -= 1

        tk.Frame().destroy()

        fuente_calibri_11 = tkFont.Font(family='Calibri', size=11, weight='normal')
        excel = openpyxl.Workbook()
        excel.create_sheet(index=0, title="Lista_pedidos")
        libro_actual = excel.active
        largo_maximo_nombre = []

        with open(self.direccion_csv_pedidos_ultimo,'r',encoding="utf-8") as f:
            lector_csv = csv.reader(f, delimiter=',')

            for fila in lector_csv:
                largo_maximo_nombre.append(fuente_calibri_11.measure(fila[2]))
                libro_actual.append(fila)

        #excel deja 3 pixeles delante de la palabra y 5 detras
        #la funcion para convertir pixeles a la unidad de excel es unidad_excel(pixeles) = (pixeles - 5) / 7
        libro_actual.column_dimensions["c"].width = math.ceil(((max(largo_maximo_nombre)+3+5)-5)/7)+2

        excel.active = 1
        excel.active.title = "Lista_paneles"
        libro_actual = excel.active

        with open(self.direccion_csv_paneles_ultimo,'r',encoding="utf-8") as f:
            lector_csv = csv.reader(f, delimiter=',')
            for fila in lector_csv:
                libro_actual.append(fila)

        excel.create_sheet()
        excel.active = 2
        excel.active.title = "Lista_requerimientos"
        libro_actual = excel.active

        largo_maximo_requerimiento = []

        with open(self.direccion_csv_requerimientos_ultimo,'r',encoding="utf-8") as f:
            lector_csv = csv.DictReader(f, delimiter=",")

            for par_clave_valor in dict(*lector_csv).items():
                largo_maximo_requerimiento.append(fuente_calibri_11.measure(par_clave_valor[0]))
                libro_actual.append(par_clave_valor)

        libro_actual.column_dimensions["a"].width = math.ceil(((max(largo_maximo_requerimiento)+3+5)-5)/7)+3

        direccion_desde_directorio_local = r"archivos\excel"

        direccion_excel = os.path.join(direccion_desde_directorio_local, f'planilla_completa_{date.today().strftime("%d-%m")}_{datetime.now().strftime("%H.%M.%S")}.xlsx')

        excel.save(direccion_excel)

    def escribir_json_lista_diccionarios(self, diccionario_pedidos):

        with open(r'archivos\json\datos_pedidos.json', 'w', encoding='utf-8') as f:
            lista_pedidos_completa = [elemento for sub_lista in diccionario_pedidos.values() for elemento in sub_lista]
            diccionario_a_escribir = {diccionario["id_pedido"]:diccionario for diccionario in lista_pedidos_completa}
            self.diccionario_pedidos_json = diccionario_a_escribir
            json.dump(diccionario_a_escribir, f, ensure_ascii=False, indent=4)
            
    def escribir_archivo_correo(self, lista_elementos_seleccionables):
        
        diccionarios_a_escribir = []

        lista_seleccion_list_box = lista_elementos_seleccionables.curselection()
        for seleccion in lista_seleccion_list_box:
            # self.ids_nombres_pedido_lista[y][0] me da el id Ej: "3921"
            diccionarios_a_escribir.append(self.diccionario_pedidos_json[self.ids_nombres_pedido_lista[seleccion][0]])
        
        csv_columns = ["tipo_producto",
            "largo",
            "ancho",
            "altura",
            "peso",
            "valor_del_contenido",
            "provincia_destino",
            "sucursal_destino",
            "localidad_destino",
            "calle_destino",
            "altura_destino",
            "piso",
            "dpto",
            "codpostal_destino",
            "destino_nombre",
            "destino_email",
            "cod_area_tel",
            "tel",
            "cod_area_cel",
            "cel"]

        codigos_ciudades_correo = {
            "buenos aires":"B",
            "ciudad autonoma de buenos aires":"C",
            "catamarca":"K",
            "chaco":"H",
            "chubut":"U",
            "cordoba":"X",
            "corrientes":"W",
            "entre rios":"E",
            "formosa":"P",
            "jujuy":"Y",
            "la pampa":"L",
            "la rioja":"F",
            "mendoza":"M",
            "misiones":"N",
            "neuquen":"Q",
            "rio negro":"R",
            "salta":"A",
            "san juan":"J",
            "san luis":"D",
            "santa cruz":"Z",
            "santa fe":"S",
            "santiago del estero":"G",
            "tierra del fuego":"V",
            "tucuman":"T"}

        fecha = f'{date.today().strftime("%d-%m")}_{datetime.now().strftime("%H.%M.%S")}'
        self.direccion_csv_correo = os.path.join(r"archivos\correo", f'correo_{fecha}.csv')

        try:
            with open(self.direccion_csv_correo, 'w', newline='',encoding="utf-8",) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=";")
                writer.writeheader()

                for datos in diccionarios_a_escribir:
                    diccionario_a_escribir = {
                        "tipo_producto":"CP",
                        "largo":20,
                        "ancho":20,
                        "altura":20,
                        "peso":2,
                        "valor_del_contenido":2000,
                        "provincia_destino":codigos_ciudades_correo[datos["envio"]["provincia"].lower()],
                        "sucursal_destino":"",
                        "localidad_destino":datos["envio"]["ciudad"],
                        "calle_destino":datos["envio"]["direccion"],
                        "altura_destino":datos["envio"]["numero_casa"],
                        "piso":"",
                        "dpto":"",
                        "codpostal_destino":datos["envio"]["cp"],
                        "destino_nombre":datos["envio"]["nombre"],
                        "destino_email":datos["datos"]["email"],
                        "cod_area_tel":"",
                        "tel":"",   ""
                        "cod_area_cel":self.dejar_solo_numeros(datos["datos"]["telefono"])[-10:-8],
                        "cel":self.dejar_solo_numeros(datos["datos"]["telefono"])[-8:]
                    }
                    writer.writerow(diccionario_a_escribir)
            print("\n"*5)
            print(ascii_correo)
            print("Se escribio el archivo del correo")
        except IOError:
            print("I/O error")

    def obtener_datos_desde_html(self, html):

        meses = {
            "enero":"1",
            "febrero":"2",
            "marzo":"3",
            "abril":"4",
            "mayo":"5",
            "junio":"6",
            "julio":"7",
            "agosto":"8",
            "septiembre":"9",
            "octubre":"10",
            "noviembre":"11",
            "diciembre":"12",
        }

        numero_pedido = html.find("h2", class_="woocommerce-order-data__heading").text.split("#")[-1].strip("\t")
                
        fecha_pedido_raw = html.find("p", class_="woocommerce-order-data__meta order_number").text.split("Pagado el ")[1].split(", ")[0].split(" ")
        fecha_pedido_parsed = f"{fecha_pedido_raw[0]}/{meses[fecha_pedido_raw[1]]}"
        
        datos_usuario_raw = [x.find_all('p') for x in html.find_all(class_="address")]
        datos_usuario_parsed = [re.split("\n|\r",p.get_text("\n")) for x in datos_usuario_raw for p in x]

        dato_numero_calle_raw = [x.find_all('p') for x in html.find_all(class_="order_data_column")]
        dato_numero_calle_parsed = [x[-1].text.split(": ")[1] for x in dato_numero_calle_raw if "Numero de calle" in str(x)]

        datos_pedido_nombre = [x.text for x in html.find_all(class_="wc-order-item-name")]
        
        fila_tabla_datos_productos = html.find_all("tbody", id="order_line_items")
        datos_pedido_cantidad_raw = [x.find("div",class_="view") for x in fila_tabla_datos_productos[0].find_all("td", class_="quantity")]
        datos_pedido_cantidad_parsed = [x.text.strip().split(" ")[-1] for x in datos_pedido_cantidad_raw]

        return numero_pedido, datos_usuario_parsed, datos_pedido_nombre, datos_pedido_cantidad_parsed, fecha_pedido_parsed, dato_numero_calle_parsed

    def descargar_datos(self, barra_progreso):

        print(ascii_amnesia)
        
        credenciales = self.obtener_json_desde_archivo(r"archivos\datos\credenciales.json")
        urls = self.obtener_json_desde_archivo(r"archivos\datos\urls.json")

        payload = {'log': credenciales["usuario"],'pwd':credenciales["contrasenia"]}

        try:
            sesion = requests.session()
            print("Sesion abierta correctamente")
        except:
            print("Problema al abrir la sesion")

        try:
            sesion.get(urls["url_login"])
            sesion.post(urls["url_login"], data=payload)
            print("Login completado correctamente")
        except:
            print("Problema al logearse")

        numero_pagina_actual = 1
        cantidad_paginas = numero_pagina_actual

        porcentaje_descarga_total = 0
        porcentaje_descarga_actual = 0

        diccionario_codigo_salida = {
            0:"exitosos",
            1:"fallidos"
        }

        diccionario_pedidos = {
            "exitosos":[],
            "fallidos":[]
        }

        while cantidad_paginas >= numero_pagina_actual:

            try:
                pagina_pedidos_web = sesion.get(urls["url_pagina_pedidos"]+str(numero_pagina_actual))
                print("Pagina obtenida correctamente")        
            except: 
                print("Problema al obtener la pagina") 

            numero_pagina_actual += 1

            html_pagina_pedidos_parseado = BeautifulSoup(pagina_pedidos_web.content, features="html.parser")

            cantidad_pedidos = int(html_pagina_pedidos_parseado.find(class_="displaying-num").text.split(" ")[0].strip())
            porcentaje_descarga_total = cantidad_pedidos
            cantidad_paginas = math.ceil(cantidad_pedidos/20)
            lista_pedidos = [x["href"] for x in html_pagina_pedidos_parseado.find_all(class_="order-view")]
            print(f"Pedidos totales: {cantidad_pedidos}")

            for i in range(len(lista_pedidos)):
                
                pedido_web = sesion.get(lista_pedidos[i])
                html_pedido_individual_parseado = BeautifulSoup(pedido_web.content, features="html.parser")

                numero_pedido, datos_usuario, datos_pedido_nombre, datos_pedido_cantidad, fecha_pedido, dato_numero_calle = self.obtener_datos_desde_html(html_pedido_individual_parseado)
         
                codigo_salida, diccionario_usuario = self.obtener_diccionario_datos(numero_pedido, 
                                                                                    datos_usuario, 
                                                                                    datos_pedido_nombre, 
                                                                                    datos_pedido_cantidad, 
                                                                                    fecha_pedido, 
                                                                                    dato_numero_calle)
                
                diccionario_pedidos[diccionario_codigo_salida[codigo_salida]].append(diccionario_usuario)

                porcentaje_descarga_actual += 1

                self.mover_barra_progreso(porcentaje_descarga_actual*100//porcentaje_descarga_total, barra_progreso)
                print(f"Pedidos restantes: {cantidad_pedidos - porcentaje_descarga_actual}")

        return diccionario_pedidos

    def copiar_csv_a_ultimo(self):

        tiempo_espera_maximo = 10

        folder = r'archivos\csv\ultimo'
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

        print([self.direccion_csv_pedidos, self.direccion_csv_paneles, self.direccion_csv_requerimientos])

        for archivo in [self.direccion_csv_pedidos, self.direccion_csv_paneles, self.direccion_csv_requerimientos]:
            shutil.copyfile(archivo, os.path.join(r'archivos\csv\ultimo',archivo.split("\\")[-1]))
        
        while not any([f for f in listdir(r"archivos\csv\ultimo") if isfile(join(r"archivos\csv\ultimo", f))]) and tiempo_espera_maximo > 0:
            time.sleep(1)
            tiempo_espera_maximo -= 1

    def asignar_texto_pedidos_fallidos(self, etiqueta_pedidos_fallidos):
        texto_pedidos_fallidos = "No hay pedidos fallidos" if not bool(self.diccionario_pedidos["fallidos"]) else f"Pedidos fallidos: {', '.join([pedido['id_pedido'] for pedido in self.diccionario_pedidos['fallidos']])}"
        etiqueta_pedidos_fallidos["text"] = texto_pedidos_fallidos

    def iniciar_descarga_datos(self, barra_progreso, etiqueta_pedidos_fallidos):
        
        self.diccionario_pedidos = self.descargar_datos(barra_progreso)
        self.escribir_json_lista_diccionarios(self.diccionario_pedidos)
        self.escribir_archivos_csv(self.diccionario_pedidos,self.obtener_json_desde_archivo(r"archivos\json\cantidades.json"))
        self.escribir_excel()
        self.asignar_texto_pedidos_fallidos(etiqueta_pedidos_fallidos)

    def escribir_archivo_correo_tk(self, diccionario_datos_exitosos, ids_nombres_pedido_lista, list_box):
        pass

    def mover_barra_progreso(self, valor, barra_progreso):
        if valor == 100:
            barra_progreso["value"] = 99.9
        else:
            barra_progreso["value"] = valor 

    def al_cerrar_ventana(self, ventana, barra_progreso):
        ventana.destroy()
        barra_progreso["mode"] = "determinate"
        barra_progreso.stop()

    def crear_ventana_correo_tk(self, ventana_principal ,barra_progreso):
        barra_progreso["mode"] = "indeterminate"
        barra_progreso.start(10)

        nueva_ventana = Toplevel(ventana_principal)
        nueva_ventana.title("Correo")
        nueva_ventana.geometry("")
        nueva_ventana.grid()
        barra_desplazamiento = tk.Scrollbar(nueva_ventana, orient=tk.VERTICAL)
        lista_elementos_seleccionables = Listbox(nueva_ventana, height=24,width=max(map(len, self.ids_nombres_pedido_parsed)), selectmode=tk.EXTENDED)
        boton_escribir_correo = Button(nueva_ventana, text="Escribir archivo correo", command=lambda: self.escribir_archivo_correo(lista_elementos_seleccionables))
        lista_elementos_seleccionables.insert(tk.END, *self.ids_nombres_pedido_parsed)
        barra_desplazamiento.config(command=lista_elementos_seleccionables.yview)

        lista_elementos_seleccionables.grid(pady=5, padx=5, row=0, column=0, sticky="WE")
        barra_desplazamiento.grid(sticky="NS", row=0, column=1)
        boton_escribir_correo.grid(pady=5,padx=5,row=1, column=0, columnspan=2, sticky="NSWE")
        
        nueva_ventana.protocol("WM_DELETE_WINDOW", lambda: self.al_cerrar_ventana(nueva_ventana, barra_progreso))

    def crear_ventana_principal_tk(self):
        ventana = tk.Tk()
        ventana.geometry('310x135')
        ventana.title('Aplicacion pedidos - AML')
        ventana.iconbitmap("amnesia_icono.ico")
        ventana.grid()

        texto_pedidos_fallidos = "No hay pedidos fallidos" if not bool(self.diccionario_pedidos["fallidos"]) else f"Pedidos fallidos: {', '.join(self.diccionario_pedidos['fallidos'].keys())}"
        etiqueta_pedidos_fallidos = Label(ventana, text = texto_pedidos_fallidos)
        barra_progreso = Progressbar(ventana, orient='horizontal', mode='determinate', length=300)
        boton_datos = tk.Button(text="Descargar datos", command=lambda: self.iniciar_descarga_datos(barra_progreso,etiqueta_pedidos_fallidos))
        boton_correo = tk.Button(text="Escribir archivo correo", command=lambda: self.crear_ventana_correo_tk(ventana,barra_progreso))
        boton_datos.grid(pady=5, padx=5, row=0, column=1, columnspan=1, sticky="NSWE")
        boton_correo.grid(pady=5, padx=5, row=1, column=1, columnspan=1, sticky="NSWE")
        etiqueta_pedidos_fallidos.grid(pady=5, padx=5, row=2, column=1, columnspan=1,sticky="N")
        barra_progreso.grid(pady=5, padx=5, row=3, column=0, columnspan=3, sticky="NSWE")
        

        ventana.mainloop()

sistema = sistema_datos()
sistema.crear_ventana_principal_tk()


# Crear una ventana de tk con 2 botones y una barra de carga en una funcion
# Boton 1: Descargar datos
#   Paso 1:
#   diccionario_pedidos_global = self.descargar_datos()
#   diccionario_pedidos = {
#       "exitosos":[],
#       "fallidos":[]
#   }
#   Sale un diccionario con este formato, los elementos de las listas tienen este formato
#   datos_usuario_dict = {
#       "id_pedido":"",
#       "facturacion":{
#           "nombre": "",
#           "direccion":"",
#           "ciudad":"",
#           "provincia":"",
#           "cp":"",
#           "numero_casa":""
#       },
#       "datos":{
#           "email":"",
#           "telefono":""
#       },
#       "envio":{
#           "nombre":"",
#           "direccion":"",
#           "ciudad":"",
#           "provincia":"",
#           "cp":"",
#           "numero_casa":""
#       },
#       "nota":"",
#       "fecha":"",
#       "productos":[]
#   }
#   #
#   Paso 2:
#   self.escribir_json_lista_diccionarios(diccionario_pedidos_global)
#   Escribo un .json llamado "datos_pedidos.json". Este contiene diccionarios,
#   la clave es el id del pedido y el valor es el diccionario "datos_usuario_dict"
#   
#   Paso 3:
#   nombre_archivo_pedidos = self.escribir_csv_lista_pedidos(diccionario_pedidos_global)
#   nombre_archivos_paneles_requerimientos = self.escribir_csv_requerimientos_paneles(diccionario_pedidos_global,self.obtener_datos_productos(r"archivos\json\cantidades.json"))
#   
#   Escribo los 3 archivos .csv que necesito para conformar un excel.
#   El primero es "lista_pedidos", las columnas son "Id_Pedido, Fecha, Nombre, Datos_pedido"
#   El segundo es "lista_paneles", es una tabla con todos los paneles que hay y sus 3 variantes que muestra 
#   cuantos hacen falta de cada uno
#   El tercero es "lista_requerimientos" aca se suman los materiales que se necesitan para armar cada pedido
#   las columnas son: led_full,led_calido,chapa_atras,chapa_adelante,ficha_macho,cooler,chapa_canaleta_100_200,chapa_canaleta_300....
# 
#   Paso 4:
#   nombre_archivos_paneles_requerimientos.append(nombre_archivo_pedidos)
#   self.copiar_csv_a_ultimo(nombre_archivos_paneles_requerimientos)
#   Junto todos los nombres de los archivos .csv recien creados y los copio a una carpeta llamada "ultimo"
#   esta solo va a contener estos 3 ultimos .csv. Con estos se va a armar el excel
#   
#   Paso 5:
#   self.escribir_excel()
#   Ahora abro los 3 archivos .csv de la carpeta "ultimo" y los copio a una hoja cada uno
#   En este paso ya tengo el excel con 3 hojas creado

# Boton 2: Escribir archivo correo
#   Aca tengo que abrir una nueva ventana que me muestre para que pueda seleccionar, los pedidos que fueron exitosos.
#   Del Paso 1 del boton "Descargar datos" el diccionario que obtengo del metodo "descargar_datos": diccionario_pedidos["exitosos"]
#   Tiene que tener un boton debajo que cree el archivo del correo con los pedidos seleccionados.
#   
#   Paso 1:
#   Abrir el archivo datos_pedidos y crear dos diccionarios, uno con pedidos exitosos y otro con pedidos fallidos
#   
#   Paso 2:
#   Abrir el archivo "lista_pedidos" que esta en la carpeta ultimo
#   Crear una lista que contenga en cada posicion una lista de formato [id, nombre]
#   Voy a agarrar cada elemento y hacerle join para que quede "id nombre".
#   Ese va a ser el que voy a mostrar en la ventana
#   
#   Paso 3:
#   Cuando seleccione los pedidos que quiero usar para armar el archivo y apreto el boton   
#   Agarro los id de los pedidos seleccionados y los busco en el diccionario que arme al abrir 
#   el archivo "datos_pedidos", esto me da el diccionario con todos los datos
# 
#   Paso 4: 
#   Agarrando cada diccionario, con sus datos conformo un diccionario nuevo con los campos
#   que requiere el correo y lo escribo a un .csv
# #



