import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

with open("LICENSE", "r") as fh:
    license_file = fh.read()

setuptools.setup(
    name="risky_code_hunter",
    version="0.3.0",
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
        "aiohttp~=3.8.1",
        # We are using current commit, because it is much fresher commit with updated whois servers (9 month newer)
        # And it seems that author currently decided not to maintain his package (version 0.7.3 as of 10 May 2022)
        "python-whois @ git+https://github.com/nicopapamichael/whois@939e05d#egg=python-whois",
        "aiodns~=3.0.0"
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
