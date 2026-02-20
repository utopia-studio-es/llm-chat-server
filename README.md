# 🤖 LLM Chat Server

Servidor de chat con IA multimodal usando modelos LLM locales con soporte para visión e internet.

## ✨ Características

- ✅ **Modelo multimodal** - Qwen2-VL-7B-Instruct (soporta imágenes)
- ✅ **Búsqueda inteligente en internet** - El modelo decide automáticamente cuándo buscar
- ✅ **Autenticación JWT** - Login seguro con sesiones
- ✅ **Streaming** - Respuestas en tiempo real
- ✅ **Historial de chats** - Múltiples conversaciones guardadas
- ✅ **Interfaz moderna** - UI responsive con diseño Utopia Labs
- ✅ **API OpenAI-compatible** - Usa vLLM como backend

## 📋 Requisitos

- **GPU**: NVIDIA con 24GB VRAM (L4, RTX 4090, A100, etc.)
- **RAM**: 16GB mínimo
- **Disco**: 50GB libres
- **SO**: Ubuntu 20.04+ / Debian 11+
- **Python**: 3.11+
- **CUDA**: 11.8+ / 12.1+

## 🚀 Instalación Rápida

```bash
# 1. Clonar repositorio
git clone https://github.com/utopia-studio-es/llm-chat-server.git
cd llm-chat-server

# 2. Configurar
cp .env.example .env
nano .env  # Edita tus credenciales

# 3. Instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt  # Tarda 5-10 min

# 4. Iniciar servicios
./start_all.sh

# 5. Esperar 2-3 minutos a que vLLM cargue el modelo
tail -f server.log  # Monitorear progreso

# 6. Acceder
# Abre http://localhost en tu navegador
```

## 🎯 Inicio Rápido

```bash
# Iniciar todo
./start_all.sh

# Ver logs
tail -f server.log  # vLLM
tail -f auth.log    # Auth API

# Detener todo
pkill -f vllm
pkill -f uvicorn
service nginx stop
```

## 📁 Estructura

```
llm-chat-server/
├── auth/
│   ├── main.py           # Backend FastAPI
│   ├── smart_tools.py    # Herramientas inteligentes
│   └── auto_tools.py     # Búsqueda web y fecha
├── frontend/
│   ├── index.html        # Login
│   ├── chat.html         # Chat
│   └── logo.png          # Logo Utopia Labs
├── .env                  # Configuración (crear desde .env.example)
├── requirements.txt      # Dependencias
├── start_server.sh       # Inicia vLLM
├── start_all.sh          # Inicia todo
└── nginx-http-only.conf  # Config Nginx
```

## ⚙️ Configuración

Edita `.env`:

```bash
API_KEY=tu-api-key-segura
MODEL_NAME=Qwen/Qwen2-VL-7B-Instruct
LOGIN_USER=admin
LOGIN_PASSWORD=tu-password-segura
```

## 🔒 Credenciales por Defecto

- **Usuario**: `admin`
- **Contraseña**: La que configures en `.env`

⚠️ **Cámbialas antes de usar en producción**

## 🌐 Despliegue

### RunPod
```bash
# Template: PyTorch 2.1
# GPU: L4 (24GB) o superior
# Seguir instalación rápida
```

### Vast.ai / Lambda Labs
Similar a RunPod

### Bare Metal
Necesitas instalar CUDA primero:
```bash
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
sh cuda_12.1.0_530.30.02_linux.run
```

## 🎮 Uso

1. Abre el navegador en tu servidor
2. Login con tus credenciales
3. Escribe mensajes
4. Adjunta imágenes con 📎 o Ctrl+V
5. Pregunta sobre noticias actuales - buscará automáticamente

## 🔧 Troubleshooting

### vLLM no inicia
```bash
# Ver logs
tail -f server.log

# Verificar GPU
nvidia-smi
```

### Auth no responde
```bash
# Ver logs
tail -f auth.log

# Reiniciar
pkill -f uvicorn
cd /workspace/llm-chat
.venv/bin/uvicorn auth.main:app --host 0.0.0.0 --port 9000
```

### Nginx error
```bash
nginx -t
service nginx restart
```

## 📚 Documentación

- [Herramientas Inteligentes](HERRAMIENTAS-INTELIGENTES.md)
- [Acceso a Internet](ACCESO-INTERNET.md)
- [Funcionalidades](FUNCIONALIDADES.md)

## 🙏 Créditos

- vLLM - Motor LLM
- FastAPI - Framework web
- Qwen - Modelos multimodales

---

**Desarrollado por Utopia Labs** - https://utopialabs.es
