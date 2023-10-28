class Pipeline:
    def __init__(self, task_list, params):
        self.data = [params]
        self.objs = task_list

    def exec(self):
        for m in self.objs:
            self.data.append(m.exec(self.data[-1]))