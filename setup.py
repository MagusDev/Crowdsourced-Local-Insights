"""
This module set up tools for app.
"""

from setuptools import find_packages, setup

setup(
    name="geodata",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "flask",
        "flask-restful",
        "flask-sqlalchemy",
        "SQLAlchemy",
        "werkzeug",
        "jsonschema",
        "flasgger",
        "rfc3339-validator",
        "flask-caching",
    ],
)
