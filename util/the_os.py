import os


def package_path():
    """获取 affinity-model 包路径

    :return str: /***/affinity-model
    """
    return os.path.dirname(os.path.dirname(__file__))



def test_package_path():
    print(package_path())