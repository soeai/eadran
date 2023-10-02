class Pipeline:
    def __init__(self, obj_list, params):
        self.data = [params]
        self.objs = obj_list

    def exec(self):
        for m in self.objs:
            self.data.append(m.exec(self.data[-1]))