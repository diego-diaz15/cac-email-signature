# Signature Builder

Generador de firmas de email para la Cámara Argentina de Comercio y Servicios (Gmail y Outlook).

El usuario final solo completa sus datos. El dominio `@cac.com.ar` es fijo. Solo se pide LinkedIn. El logo corporativo ya viene en la aplicación.

## Cómo usarlo

1. Abrí `SignatureBuilder.exe` (o `python -m signature_builder` en desarrollo).
2. Completá nombre, cargo, teléfono, email (solo la parte antes de `@cac.com.ar`), web y LinkedIn si aplica.
3. Pulsá **Copiar firma** y en Gmail (Configuración → Firma) pegá con Ctrl+V.

Nada más: no hay que buscar archivos ni subir imágenes. El logo de la firma copiada sale del sitio público de la CAC.

## Limitaciones

- Outlook clásico de Windows muestra el GIF quieto (solo el primer frame). Outlook nuevo, Outlook web y la vista previa de la app sí muestran el brillo.
- La app de Gmail en el teléfono usa una firma de texto aparte.

## Desarrollo

```powershell
cd "C:\Users\Diego Diaz\Desktop\firma cac"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m signature_builder --build-assets
pytest
python -m signature_builder
```

## Página estática (sin servidor — recomendada para el equipo)

El archivo `docs/index.html` es completamente independiente: no necesita Python ni ningún servidor. Cualquiera puede abrirlo con doble clic o compartirlo vía URL.

**Opciones para publicarlo:**

1. **GitHub Pages** (gratis, URL pública permanente):
   En el repo → Settings → Pages → Source: `main` / `docs/`.
   La URL queda en `https://diego-diaz15.github.io/cac-email-signature/`.

2. **Netlify Drop**: arrastrar la carpeta `docs/` en [app.netlify.com/drop](https://app.netlify.com/drop). Genera una URL en segundos, sin cuenta.

3. **Compartir el archivo** `docs/index.html` por OneDrive/SharePoint y abrirlo desde el navegador.

## Firmador web (con servidor local)

```powershell
python -m signature_builder --web
```

Se abre `http://127.0.0.1:8765/`. El HTML que copia es el mismo que el de la app de escritorio (logo público + iconos embebidos).

`--build-assets` recorta el logo, genera `assets/brand/logo-animated.gif` y los iconos. No corre cada vez que un empleado arma su firma.

## Rebuild del .exe

```powershell
.\scripts\build_exe.ps1
```

El ejecutable queda en `dist\SignatureBuilder\SignatureBuilder.exe` (carpeta onedir: hay que copiar toda la carpeta, no solo el .exe).

## Arquitectura

- `src/signature_builder/ui` — formulario y preview de escritorio
- `src/signature_builder/web` — firmador en el navegador (`--web`)
- `src/signature_builder/core` — datos, plantillas, HTML, clipboard, export
- `src/signature_builder/animation` — recorte del logo y GIF (logo estático + brillo)
- `src/signature_builder/templates` — corporate / modern / minimal
- `brand.json` — marca, colores, URL pública del logo, tamaño
