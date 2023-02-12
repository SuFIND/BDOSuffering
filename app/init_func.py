def init_labels_dic(path):
    """
    用于加载模型标签字典的方法
    :param path:
    :return:
    """
    dic = dict()
    with open(path, "r", encoding="utf8") as fp:
        for idx, line in enumerate(fp.readlines()):
            line = line.strip("\n")
            _, label = line.split(" ", maxsplit=1)
            dic[idx] = label
    return dic

