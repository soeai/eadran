from cloud.orchestrator.commons.modules import StartFedServer, BuildDocker
from cloud.orchestrator.commons.pipeline import Pipeline
from cloud.orchestrator.orchestrator import Orchestrator

params = {}
conf = {}
orchestrator = Orchestrator(conf)
# orchestrator.start()

pipeline = Pipeline(task_list=[StartFedServer(orchestrator),
                               BuildDocker()],
                    params=params)
pipeline.exec()
