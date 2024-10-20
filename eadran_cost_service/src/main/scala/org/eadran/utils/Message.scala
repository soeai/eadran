package org.eadran.utils

case class Message(
                    model_id:       String             = "",
                    run_id:         String               = "1",
                    dataset_id:   String             = "",
                    timestamp:     java.sql.Timestamp = Util.localToGMT(),
                    train_round:   Int            = 0,
                    edge_id:  String  = "",
                    quality_of_model:  QualityOfModel  = new QualityOfModel,
                    resource_monitor: ResourceMonitor = new ResourceMonitor,
                    qom_function: String = "",
                    resource_function: String = "",
                    cost_qod: Double = 0.0,
                    cost_context: Double = 0.0
                  )

case class QualityOfModel(
                           post_train_performance:   Double = -1,
                           pre_train_performance:   Double  = -1,
                           pre_loss_value:   Double = -1,
                           post_loss_value:   Double  =1,
                           test_performance:   Double = -1,
                           test_loss:   Double  =1,
                           train_duration: Double = 0,
//                           evaluate_on_test: Integer = 0
                         )
case class ResourceMonitor(
                            cpu_percentage:   Double = 0,
                            memory_usage:   Double  =0,
//                            gpu:   Double = -1,
//                            network:   Double  =1,
//                            storage:   Double = -1
                          )

case class CostState(
                      modelId: String,
                      runId: String,
                      datasetId: String,
                      trainRound: Int,
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
                      var performanceTest: Double,
                      var edgeId: String,
                      var done: Boolean
                    )