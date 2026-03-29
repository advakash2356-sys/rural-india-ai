"""Setup configuration for Rural India AI edge node."""

from setuptools import setup, find_packages

setup(
    name="rural-india-ai-edge",
    version="0.1.0",
    description="Edge-native AI system for rural India villages",
    author="Rural India AI Team",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "pydantic==2.4.2",
        "psutil==5.9.6",
        "paho-mqtt==1.6.1",
        "aiofiles==23.2.1",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "black==23.11.0",
            "pylint==3.0.2",
            "mypy==1.7.0",
        ],
        "llm": [
            "llama-cpp-python==0.2.28",
        ]
    },
    entry_points={
        "console_scripts": [
            "rural-ai-edge=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
