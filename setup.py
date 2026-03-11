from setuptools import setup, find_packages

setup(
    name="project-nikkei",
    version="0.1.0",
    description="Local Autonomous Agent and Conversational OS",
    author="Project Nikkei",
    packages=find_packages(include=["core", "adapters", "tentacles", "neurons", "ui", "core.*", "adapters.*", "tentacles.*", "neurons.*", "ui.*"]),
    py_modules=["main", "cli"],
    install_requires=[
        "keyring",
        "pydantic",
        "python-telegram-bot",
        "pystray",
        "Flask",
        "pillow",
        "psutil",
        "google-api-python-client",
        "google-auth-httplib2",
        "google-auth-oauthlib",
        "google-genai",
        "watchdog",
        "plyer",
    ],
    entry_points={
        "console_scripts": [
            "nikkei=cli:main",
        ]
    },
)
