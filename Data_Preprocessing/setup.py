"""
GenBFKit Data Preprocessing Module - Setup Script

这个脚本用于将 Data_Preprocessing 目录安装为独立的 Python 包
"""

from setuptools import setup, find_packages
import os

# 读取 README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# 读取 requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="genbfkit-preprocessing",
    version="1.0.0",
    author="GenBFKit Team",
    author_email="support@genbfkit.org",
    description="A comprehensive data preprocessing module for time-series sensor data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/genbfkit",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    keywords="data-preprocessing, missing-value, outlier-detection, normalization, time-series, sensor-data",
)
