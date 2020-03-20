import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="trio-irc", # Replace with your own username
    version="0.0.1",
    author="han-solo",
    author_email="hanish0019@gmail.com",
    description="A simple IRC framework using trio",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/millefalcon/TrioIRCClient",
    py_modules=['irc'],
    #packages=setuptools.find_packages(),
    install_requires=[
        'trio'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
