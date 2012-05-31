from setuptools import setup

setup(name="netbeacon",
      version="1.1",
      description="Network host discovery.",
      long_description = open("README.txt").read(),
      keywords="network, host, beacon, discovery, UDP, broadcast",
      author="David Siroky",
      author_email="siroky@dasir.cz",
      url="http://www.smallbulb.net",
      license="MIT License",
      classifiers=[
          "Operating System :: OS Independent",
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Topic :: System :: Networking",
          "Topic :: System :: Distributed Computing",
          "Topic :: Communications",
          "Topic :: Software Development :: Libraries"
        ],
      install_requires=["netifaces"],
      py_modules=["beacon"],
      scripts=["beacon_example_srv.py", "beacon_example_cli.py"]
    )
