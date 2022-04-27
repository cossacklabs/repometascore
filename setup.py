import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

with open("LICENSE", "r") as fh:
    license = fh.read()

setuptools.setup(
    name="risky_code_hunter",
    version="0.9.0",
    author="Cossack Labs",
    author_email="dev@cossacklabs.com",
    description="Package to detect risky contributors into repository",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cossacklabs/risky-code-hunter",
    project_urls={
        "Bug Tracker": "https://github.com/cossacklabs/risky-code-hunter/issues",
    },
    install_requires=[
        "requests~=2.27.1",
        "aiohttp~=3.8.1"
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    include_package_data=True,
    license='Apache Software License',
    platforms=['OS Independent']
)
