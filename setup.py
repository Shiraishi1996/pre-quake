from setuptools import setup, find_packages

def load_requires_from_file(filepath):
    with open(filepath) as fp:
        return [pkg_name.strip() for pkg_name in fp.readlines()]

setup(
    # その他の項目は省略
    install_requires=load_requires_from_file("requirements.txt")
)
