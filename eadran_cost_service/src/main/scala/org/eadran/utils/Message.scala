package org.eadran.utils

case class Message(
                    model_id:       String             = "",
                    run_id:         String               = "1",
                    dataset_id:   String             = "",
                    timestamp:     java.sql.Timestamp = Util.localToGMT(),
                    train_round:   Long            = 0,
                    edge_id:  String  = "",
                    quality_of_model:  QualityOfModel  = new QualityOfModel,
                    resource_monitor: ResourceMonitor = new ResourceMonitor,
                    qom_function: String = "",
                    resource_function: String = "",
                    cost_qod: Double = 0.0,
                    cost_context: Double = 0.0
                  )

case class QualityOfModel(
                           train_performance_before:   Double = -1,
                           train_performance_after:   Double  = -1,
                           loss_value_before:   Double = -1,
                           loss_value_after:   Double  =1,
                           test_performance_before:   Double = -1,
                           test_performance_after:   Double  =1,
                           duration: Double = 0
                         )
case class ResourceMonitor(
                            cpu:   Double = 0,
                            memory:   Long  =0,
                            gpu:   Double = -1,
                            network:   Double  =1,
                            storage:   Long = -1
                          )

case class CostState(
                      modelId: String,
                      runId: String,
                      datasetId: String,
                      trainRound: Long,
                      var timestamp: java.sql.Timestamp,
                      var resourceDuration: Double,
                      var maxCpu: Double,
                      var maxMemory: Double,
                      var msgCount: Long,
                      var costResource: Double,
                      var costQoM: Double,
                      var costQoD: Double,
                      var costContext: Double,
                      var improvementDiff: Double,
                      var performancePost: Double,
                      var edgeId: String,
                      var done: Boolean
                    )