from setuptools import setup


setup(
    name="pydcomm",
    description="Bugatone's infrastructure for communication with android devices",
    py_modules=['pydcomm'],
    install_requires=['mock', 'nose', 'parameterized', 'timeout-decorator', 'subprocess32', 'netifaces']
)
