import typer
from cryptography.fernet import Fernet

app = typer.Typer(help="FastAPI Application CLI")


@app.command()  # type: ignore[misc]
def generate_key() -> None:
    """
    Генерирует новый ключ шифрования для приложения.
    """
    new_key = Fernet.generate_key()
    key_str = new_key.decode("utf-8")

    typer.echo("=" * 50)
    typer.echo("СГЕНЕРИРОВАННЫЙ КЛЮЧ ШИФРОВАНИЯ")
    typer.echo("=" * 50)
    typer.echo(f"Ключ: {key_str}")
    typer.echo("=" * 50)
    typer.echo("\nДобавьте этот ключ в ваши настройки:")
    typer.echo(f"ENCRYPTION_KEY={key_str}")
    typer.echo("\nИли в .env файл:")
    typer.echo(f'ENCRYPTION_KEY="{key_str}"')


@app.command()  # type: ignore[misc]
def start_server(
    host: str = "0.0.0.0", port: int = 8000, reload: bool = False
) -> None:
    """
    Запускает FastAPI сервер.
    """
    import uvicorn

    from core.logger import LOGGING
    from core.settings import settings

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_config=LOGGING,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    app()
