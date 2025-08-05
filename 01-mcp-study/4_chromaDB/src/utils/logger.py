import logging
from typing import Optional
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Mapeamento de níveis de log
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Nível de log padrão
DEFAULT_LOG_LEVEL = 'INFO'

# Obtém o nível de log do ambiente ou usa o padrão
LOG_LEVEL = os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL).upper()
LOG_LEVEL = LOG_LEVEL if LOG_LEVEL in LOG_LEVELS else DEFAULT_LOG_LEVEL

class ColoredFormatter(logging.Formatter):
    """Custom formatter para adicionar cores aos logs no terminal."""
    
    # Cores ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Ciano
        'INFO': '\033[32m',      # Verde
        'WARNING': '\033[33m',   # Amarelo
        'ERROR': '\033[31m',     # Vermelho
        'CRITICAL': '\033[41m',  # Fundo vermelho
        'RESET': '\033[0m',      # Reset
    }
    
    # Ícones para cada nível
    ICONS = {
        'DEBUG': '🐛',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥',
    }

    def format(self, record):
        # Adiciona o ícone ao início da mensagem
        icon = self.ICONS.get(record.levelname, '')
        if icon:
            record.msg = f"{icon} {record.msg}"
            
        # Formata a mensagem
        formatted_msg = super().format(record)
        
        # Adiciona cores se estiver em um terminal
        if sys.stderr.isatty():
            color = self.COLORS.get(record.levelname, '')
            if color:
                formatted_msg = f"{color}{formatted_msg}{self.COLORS['RESET']}"
                
        return formatted_msg

def setup_logger(name: str, log_level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configura e retorna um logger personalizado.
    
    Args:
        name: Nome do logger
        log_level: Nível de log (opcional, usa o padrão se não informado)
        log_file: Arquivo para salvar os logs (opcional)
        
    Returns:
        logging.Logger: Instância do logger configurado
    """
    # Cria o logger
    logger = logging.getLogger(name)
    
    # Define o nível de log
    level = LOG_LEVELS.get(log_level or LOG_LEVEL, logging.INFO)
    logger.setLevel(level)
    
    # Evita logs duplicados se o logger já estiver configurado
    if logger.handlers:
        return logger
    
    # Formato do log
    log_format = "[%(asctime)s] [%(levelname)s] %(message)s"
    formatter = ColoredFormatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    # Handler para saída no terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo, se especificado
    if log_file:
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

# Logger global para ser usado em todo o projeto
logger = setup_logger('chatbot')

def log_info(message: str):
    """Registra uma mensagem de informação."""
    logger.info(message)

def log_warning(message: str):
    """Registra uma mensagem de aviso."""
    logger.warning(message)

def log_error(message: str, exc_info=None):
    """Registra uma mensagem de erro."""
    logger.error(message, exc_info=exc_info)

def log_debug(message: str):
    """Registra uma mensagem de depuração."""
    logger.debug(message)

def log_critical(message: str):
    """Registra uma mensagem crítica."""
    logger.critical(message)

def log_tool_call(tool_name: str, tool_input: dict):
    """Registra a chamada de uma ferramenta de forma padronizada."""
    input_str = ', '.join(f"{k}={v}" for k, v in tool_input.items())
    logger.info(f"🔧 Chamando ferramenta: {tool_name}({input_str})")

def log_tool_result(tool_name: str, result: str, max_length: int = 300):
    """Registra o resultado de uma ferramenta de forma padronizada."""
    result_str = str(result)
    if len(result_str) > max_length:
        result_str = result_str[:max_length] + "..."
    logger.info(f"✅ {tool_name} retornou: {result_str}")

def log_context_found(context: str, max_length: int = 300):
    """Registra o contexto encontrado."""
    if not context:
        logger.info("ℹ️  Nenhum contexto relevante encontrado.")
        return
        
    context_str = str(context)
    if len(context_str) > max_length:
        context_str = context_str[:max_length] + "..."
    logger.info(f"📚 Contexto encontrado: {context_str}")

def log_model_response(response: str, max_length: int = 300):
    """Registra a resposta do modelo."""
    if not response:
        return
        
    response_str = str(response)
    if len(response_str) > max_length:
        response_str = response_str[:max_length] + "..."
    logger.debug(f"🤖 Resposta do modelo: {response_str}")

def log_success(message: str):
    """Registra uma mensagem de sucesso."""
    logger.info(f"✅ {message}")
