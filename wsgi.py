from .main import bot  # Assicurati di importare il tuo bot

def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    
    return [b"Bot is running"]
