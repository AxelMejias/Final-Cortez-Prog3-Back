"""
Script para cargar productos iniciales en la DB via API.
Uso:
  python seed_productos.py                          # contra Render
  python seed_productos.py http://localhost:8000     # contra local
"""

import sys
import requests
import time

# ── Configuración ──────────────────────────────────────────────
API_URL = sys.argv[1] if len(sys.argv) > 1 else "https://final-cortez-prog3-back.onrender.com"
API_URL = API_URL.rstrip("/")
ADMIN_TOKEN = "admin-secret-123"
HEADERS = {"x-admin-token": ADMIN_TOKEN, "Content-Type": "application/json"}

# ── Productos ──────────────────────────────────────────────────
# Formato: (nombre, categoria, precio, stock, descripcion)
# Las imágenes las agregás después desde el panel de admin.

PRODUCTOS = [
    # ─── Cuadernos y Anotadores ───
    ("Cuaderno Rivadavia Tapa Dura 98 hojas", "Cuadernos", 3500, 50, "Cuaderno tapa dura rayado, 98 hojas de calidad premium."),
    ("Cuaderno Rivadavia Tapa Dura 48 hojas", "Cuadernos", 2500, 60, "Cuaderno tapa dura rayado, 48 hojas."),
    ("Cuaderno Rivadavia Tapa Flexible 48 hojas", "Cuadernos", 1800, 70, "Cuaderno económico tapa flexible, 48 hojas rayadas."),
    ("Cuaderno Espiralado A4 80 hojas", "Cuadernos", 4200, 40, "Cuaderno espiralado tamaño A4, hojas cuadriculadas."),
    ("Cuaderno Espiralado A4 120 hojas", "Cuadernos", 5500, 35, "Cuaderno espiralado A4 de 120 hojas cuadriculadas."),
    ("Cuaderno Universitario Ledesma 80 hojas", "Cuadernos", 3800, 45, "Cuaderno universitario rayado, tapa semidura."),
    ("Repuesto Rivadavia Rayado x 480 hojas", "Cuadernos", 4500, 25, "Repuesto de hojas rayadas para carpeta."),
    ("Repuesto Rivadavia Cuadriculado x 480 hojas", "Cuadernos", 4500, 25, "Repuesto de hojas cuadriculadas para carpeta."),
    ("Anotador Espiralado A6", "Cuadernos", 1200, 80, "Mini anotador espiralado de bolsillo, 80 hojas."),
    ("Block de Dibujo Canson A4", "Cuadernos", 3200, 30, "Block de dibujo 20 hojas, papel grueso ideal para técnicas húmedas."),

    # ─── Lápices y Colores ───
    ("Lápiz Negro HB Faber Castell", "Lápices", 400, 200, "Lápiz grafito HB clásico, ideal para escritura y dibujo."),
    ("Lápiz Negro 2B Faber Castell", "Lápices", 450, 150, "Lápiz grafito 2B, trazo suave para dibujo artístico."),
    ("Caja Lápices de Colores Faber Castell x12", "Lápices", 3500, 40, "Set de 12 lápices de colores largos, mina resistente."),
    ("Caja Lápices de Colores Faber Castell x24", "Lápices", 6000, 30, "Set de 24 lápices de colores largos."),
    ("Caja Lápices de Colores Faber Castell x36", "Lápices", 8500, 20, "Set de 36 lápices de colores profesionales."),
    ("Lápices Acuarelables Faber Castell x12", "Lápices", 7500, 15, "Lápices acuarelables de 12 colores, se diluyen con agua."),
    ("Crayones Cera Jovi x12", "Lápices", 2800, 50, "Crayones de cera gruesos, colores intensos."),
    ("Lápiz Mecánico 0.5mm Pentel", "Lápices", 2200, 40, "Portaminas 0.5mm con grip de goma."),
    ("Minas 0.5mm HB Pentel x 12", "Lápices", 600, 100, "Repuesto de minas 0.5mm para portaminas."),
    ("Sacapuntas Metálico Simple", "Lápices", 300, 150, "Sacapuntas de metal de un orificio."),
    ("Sacapuntas Doble con Depósito", "Lápices", 800, 80, "Sacapuntas con depósito para virutas, doble orificio."),

    # ─── Bolígrafos y Marcadores ───
    ("Bolígrafo Bic Cristal Azul", "Bolígrafos", 350, 300, "Bolígrafo clásico punta media 1.0mm, tinta azul."),
    ("Bolígrafo Bic Cristal Negro", "Bolígrafos", 350, 250, "Bolígrafo clásico punta media 1.0mm, tinta negra."),
    ("Bolígrafo Bic Cristal Rojo", "Bolígrafos", 350, 200, "Bolígrafo clásico punta media 1.0mm, tinta roja."),
    ("Pack Bolígrafos Bic x10 Surtidos", "Bolígrafos", 3200, 40, "Pack de 10 bolígrafos en colores surtidos."),
    ("Microfibra Filgo Punta Media Negra", "Bolígrafos", 800, 100, "Microfibra punta 0.5mm, trazo fino y preciso."),
    ("Set Microfibras Filgo x10 Colores", "Bolígrafos", 5500, 25, "Set de 10 microfibras de colores variados."),
    ("Roller Pilot V5 Azul", "Bolígrafos", 3500, 30, "Roller de tinta líquida, punta aguja 0.5mm."),
    ("Marcador Permanente Negro Edding 300", "Bolígrafos", 1500, 60, "Marcador permanente punta redonda 1.5-3mm."),
    ("Resaltador Filgo Amarillo", "Bolígrafos", 900, 100, "Resaltador fluorescente punta biselada."),
    ("Set Resaltadores Filgo x4 Colores", "Bolígrafos", 3200, 40, "Pack de 4 resaltadores: amarillo, verde, rosa y naranja."),

    # ─── Gomas y Correctores ───
    ("Goma de Borrar Staedtler Mars Plastic", "Gomas y Correctores", 600, 120, "Goma blanca de alta calidad, no daña el papel."),
    ("Goma Lapiz/Tinta Staedtler Doble", "Gomas y Correctores", 500, 100, "Goma doble uso: lado azul para tinta, lado blanco para lápiz."),
    ("Corrector Líquido Liquid Paper", "Gomas y Correctores", 1200, 80, "Corrector líquido con pincel aplicador, 20ml."),
    ("Cinta Correctora Pilot 5mm x 6m", "Gomas y Correctores", 1800, 50, "Cinta correctora seca, aplicación inmediata."),

    # ─── Papelería ───
    ("Resma A4 Autor 75g 500 hojas", "Papelería", 8500, 30, "Resma de papel A4 de 75 gramos, 500 hojas blancas."),
    ("Resma A4 Autor 80g 500 hojas", "Papelería", 9500, 25, "Resma de papel A4 de 80 gramos, calidad superior."),
    ("Resma Oficio 75g 500 hojas", "Papelería", 9000, 20, "Resma de papel tamaño oficio, 500 hojas."),
    ("Papel Glasé x10 hojas", "Papelería", 500, 100, "Papel glasé de colores surtidos para manualidades."),
    ("Cartulina Blanca A4 x10", "Papelería", 1200, 60, "Pack de 10 cartulinas blancas tamaño A4."),
    ("Cartulina Color A4 x10", "Papelería", 1400, 50, "Pack de 10 cartulinas de colores surtidos A4."),
    ("Papel Afiche Blanco 70x100cm", "Papelería", 400, 80, "Papel afiche para presentaciones y trabajos prácticos."),
    ("Papel Afiche Color 70x100cm", "Papelería", 450, 70, "Papel afiche de color, varios colores disponibles."),
    ("Papel Crepe Varios Colores", "Papelería", 350, 100, "Papel crepé para decoración y manualidades."),
    ("Sobre Manila A4", "Papelería", 200, 200, "Sobre de papel madera tamaño A4."),

    # ─── Útiles de Geometría ───
    ("Set Geometría Completo (4 piezas)", "Geometría", 2500, 40, "Juego de geometría: regla 30cm, escuadra, cartabón y transportador."),
    ("Regla Plástica 30cm Pizzini", "Geometría", 600, 100, "Regla transparente de 30cm con escala milimétrica."),
    ("Regla Metálica 30cm", "Geometría", 1200, 50, "Regla de aluminio 30cm, resistente y precisa."),
    ("Compás Escolar Pizzini", "Geometría", 1800, 60, "Compás escolar con adaptador para lápiz."),
    ("Compás Técnico Profesional", "Geometría", 4500, 20, "Compás de precisión para dibujo técnico."),
    ("Transportador 180° Plástico", "Geometría", 400, 100, "Transportador semicircular transparente."),
    ("Escuadra 45° 20cm", "Geometría", 700, 70, "Escuadra plástica transparente 45 grados."),
    ("Escuadra 60° 20cm", "Geometría", 700, 70, "Escuadra plástica transparente 60 grados."),

    # ─── Mochilas y Cartucheras ───
    ("Mochila Escolar Negra Básica", "Mochilas", 18000, 15, "Mochila escolar resistente con compartimentos múltiples."),
    ("Mochila Escolar con Carro", "Mochilas", 35000, 10, "Mochila con carro desmontable, ruedas reforzadas."),
    ("Mochila Urbana Gris", "Mochilas", 22000, 12, "Mochila urbana con compartimento para notebook 15 pulgadas."),
    ("Cartuchera de Tela Simple", "Mochilas", 3500, 40, "Cartuchera rectangular de tela con cierre."),
    ("Cartuchera 2 Pisos con Útiles", "Mochilas", 8000, 25, "Cartuchera de 2 pisos equipada con útiles básicos."),
    ("Cartuchera de Silicona", "Mochilas", 4500, 30, "Cartuchera de silicona flexible, fácil de limpiar."),

    # ─── Adhesivos y Cintas ───
    ("Plasticola 40g", "Adhesivos", 600, 150, "Adhesivo vinílico escolar 40 gramos."),
    ("Plasticola 250g", "Adhesivos", 1800, 50, "Adhesivo vinílico escolar 250 gramos, tamaño familiar."),
    ("Barra de Pegamento Pritt 20g", "Adhesivos", 1500, 80, "Barra adhesiva no tóxica, secado rápido."),
    ("Cinta Scotch Transparente 18mm x 25m", "Adhesivos", 900, 100, "Cinta adhesiva transparente multiuso."),
    ("Cinta de Papel (Enmascarar) 18mm x 50m", "Adhesivos", 1200, 60, "Cinta de enmascarar para pintura y trabajos manuales."),
    ("Voligoma 30ml", "Adhesivos", 500, 120, "Adhesivo de contacto escolar en frasco con pico aplicador."),
    ("Cinta Bifaz 12mm x 10m", "Adhesivos", 1000, 50, "Cinta doble faz para pegado limpio."),

    # ─── Tijeras y Corte ───
    ("Tijera Escolar Punta Roma 13cm", "Tijeras y Corte", 1200, 80, "Tijera escolar con punta redondeada, segura para niños."),
    ("Tijera Multiuso Acero 21cm", "Tijeras y Corte", 2500, 40, "Tijera de acero inoxidable para uso general."),
    ("Trincheta Chica 9mm", "Tijeras y Corte", 800, 60, "Cutter/trincheta con hoja retráctil de 9mm."),
    ("Trincheta Grande 18mm", "Tijeras y Corte", 1200, 40, "Cutter/trincheta profesional con hoja de 18mm."),

    # ─── Organización ───
    ("Carpeta Escolar 3 Anillos N3", "Organización", 4500, 30, "Carpeta de 3 anillos tamaño oficio, tapa dura."),
    ("Carpeta Oficio 2 Anillos", "Organización", 3500, 35, "Carpeta de 2 anillos tamaño oficio."),
    ("Bibliorato A4 Lomo Ancho", "Organización", 5500, 20, "Bibliorato A4 con palanca, lomo 75mm."),
    ("Folio A4 Cristal x100", "Organización", 3500, 30, "Pack de 100 folios transparentes tamaño A4."),
    ("Separadores A4 x6 Colores", "Organización", 800, 50, "Juego de 6 separadores de colores para carpeta."),
    ("Clips Metálicos x100", "Organización", 400, 100, "Caja de 100 clips metálicos Nº4."),
    ("Broches Clips Doble x12", "Organización", 600, 80, "Clips mariposa medianos, caja x12 unidades."),
    ("Abrochadora Pinza Metal", "Organización", 3500, 25, "Abrochadora de escritorio para broches 24/6."),
    ("Broches para Abrochadora 24/6 x1000", "Organización", 500, 100, "Caja de 1000 broches 24/6."),
    ("Perforadora 2 Agujeros Metal", "Organización", 4000, 20, "Perforadora de escritorio para hasta 20 hojas."),

    # ─── Arte y Manualidades ───
    ("Témperas Alba x6 Colores", "Arte", 3500, 30, "Set de 6 témperas escolares, colores básicos."),
    ("Témperas Alba x12 Colores", "Arte", 6000, 20, "Set de 12 témperas escolares, paleta completa."),
    ("Acuarelas Acuarelín x12", "Arte", 2800, 35, "Acuarelas secas en pastilla, 12 colores con pincel."),
    ("Pincel Escolar Nº8", "Arte", 600, 80, "Pincel escolar pelo sintético, punta redonda Nº8."),
    ("Set Pinceles Escolares x6", "Arte", 2500, 30, "Set de 6 pinceles de diferentes tamaños."),
    ("Plastilina x12 Colores", "Arte", 2000, 40, "Set de 12 barras de plastilina de colores."),

    # ─── Servicios de Impresión ───
    ("Impresión B/N x hoja", "Servicios", 100, 9999, "Servicio de impresión en blanco y negro por hoja A4."),
    ("Impresión Color x hoja", "Servicios", 300, 9999, "Servicio de impresión a color por hoja A4."),
    ("Fotocopia B/N x hoja", "Servicios", 80, 9999, "Servicio de fotocopia en blanco y negro por hoja."),
    ("Anillado Plástico", "Servicios", 1500, 9999, "Servicio de anillado con espiral plástico, hasta 100 hojas."),
    ("Laminado A4", "Servicios", 1200, 9999, "Servicio de plastificado/laminado de hoja A4."),
]

# ── Ejecución ──────────────────────────────────────────────────
def main():
    url = f"{API_URL}/api/productos"
    ok = 0
    errores = []

    print(f"Cargando {len(PRODUCTOS)} productos en {url} ...")
    print("=" * 60)

    for i, (nombre, categoria, precio, stock, descripcion) in enumerate(PRODUCTOS, 1):
        payload = {
            "nombre": nombre,
            "categoria": categoria,
            "precio": precio,
            "stock": stock,
            "descripcion": descripcion,
        }
        try:
            r = requests.post(url, json=payload, headers=HEADERS, timeout=30)
            if r.status_code in (200, 201):
                ok += 1
                print(f"  [{i}/{len(PRODUCTOS)}] ✓ {nombre}")
            else:
                msg = r.text[:120]
                errores.append((nombre, msg))
                print(f"  [{i}/{len(PRODUCTOS)}] ✗ {nombre} → {r.status_code}: {msg}")
        except Exception as e:
            errores.append((nombre, str(e)))
            print(f"  [{i}/{len(PRODUCTOS)}] ✗ {nombre} → {e}")

        # Pequeña pausa para no saturar el servidor free
        if i % 10 == 0:
            time.sleep(0.5)

    print("=" * 60)
    print(f"Resultado: {ok} creados, {len(errores)} errores")
    if errores:
        print("\nErrores:")
        for nombre, msg in errores:
            print(f"  - {nombre}: {msg}")


if __name__ == "__main__":
    main()
