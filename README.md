# PopulPy 📊

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)

Herramienta de análisis de tendencias de búsqueda con integración de múltiples motores (Google, Bing, DuckDuckGo) y visualizaciones interactivas.

## 🚀 Características

- 🔍 Búsqueda integrada con múltiples proveedores
- 📈 Análisis de tendencias temporales
- 🗺️ Visualización geográfica de interés
- ☁️ Generación de nubes de palabras
- 📊 Gráficos interactivos con Plotly
- 🎨 Temas claro/oscuro
- 💾 Historial de búsquedas

## 🛠️ Instalación

### Prerrequisitos

1. Python 3.8 o superior
2. Una cuenta de Google Cloud con acceso a la API de búsqueda personalizada
3. Una cuenta de Azure con acceso a la API de Bing
4. Una cuenta de DuckDuckGo (opcional)

### Instalación

1. Clona este repositorio:

```bash
git clone https://github.com/murapa96/populpy
cd populpy
```

2. Instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

### Configuración de Variables de Entorno

Crea un archivo `.env` en el directorio raíz con la siguiente estructura:

```
GOOGLE_API_KEY=TU_API_KEY_DE_GOOGLE
SEARCH_ENGINE_ID=TU_ID_DE_MOTOR_DE_BUSQUEDA
BING_API_KEY=TU_API_KEY_DE_BING
```

Reemplaza `TU_API_KEY_DE_GOOGLE`, `TU_ID_DE_MOTOR_DE_BUSQUEDA` y `TU_API_KEY_DE_BING` con tus credenciales correspondientes.

## 📖 Uso

### Interfaz Web (Streamlit)

Para ejecutar la interfaz web, usa el siguiente comando:

```bash
streamlit run app.py
```

### Línea de Comandos

```bash
python main.py -q "término de búsqueda" -c "código de país" -w "ruta para guardar la imagen"
```

- `-q`: Término de búsqueda.
- `-c`: Código de país (por defecto es `es`).
- `-w`: Ruta para guardar la imagen de la nube de palabras.

## 🗂️ Estructura del Proyecto

```
populpy/
├── app.py
├── main.py
├── README.md
├── requirements.txt
└── .env.example
```

## 📝 ToDo

- [ ] Añadir soporte para más proveedores de búsqueda
- [ ] Implementar exportación de datos en múltiples formatos
- [ ] Mejorar la persistencia de datos
- [ ] Añadir más visualizaciones
- [ ] Implementar caché de resultados

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para más detalles.

## 👤 Autor

Pablo Ramos Muras [@Murapa96](https://github.com/Murapa96)
