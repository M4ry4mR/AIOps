from setuptools import setup, find_packages

setup(
    name="azuredevopsagent",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "flask",
        "openai",
        "httpx",
        "requests",
        "python-dotenv",
        "google-generativeai",
    ],
    python_requires=">=3.8",
) 