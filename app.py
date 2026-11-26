import importlib
import os

from nucleo import app, init_db

MODULOS = ["rotas_acesso", "rotas_agendamento", "rotas_odonto_materiais", "rotas_atendimento"]
for _m in MODULOS:
    try:
        importlib.import_module(_m)
    except ModuleNotFoundError as e:
        if e.name != _m:
            raise
        print(f"[ATLAS IF] Aviso: {_m}.py ainda não foi adicionado ao projeto.")


def ip_da_rede():
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return None


if __name__ == "__main__":
    init_db()
    porta = int(os.getenv("PORTA", 5000))
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        ip = ip_da_rede()
        print("\n  ATLAS IF rodando:")
        print(f"   - Neste computador:  http://127.0.0.1:{porta}")
        if ip:
            print(f"   - No celular (mesmo Wi-Fi):  http://{ip}:{porta}\n")
    
    app.run(host="0.0.0.0", port=porta, debug=True, use_debugger=False)