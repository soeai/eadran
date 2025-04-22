package org.eadran.stream

import org.apache.spark.sql.streaming.GroupState
import org.eadran.utils.{CostState, Message, Util, ResourceMonitor, QualityOfModel}
import org.eadran.cost.Functions

class StateMgmt() extends Serializable {

  //    @transient lazy val log = org.apache.log4j.LogManager.getLogger(getClass.getCanonicalName)

  val interval = 60 * 1000 * 5 //5 minutes

  //    log.info("spot interval set to " + interval)

  def computeCost( keyId: (String, String, String, Int),
                   inputs:    Iterator[Message],
                   oldState:  GroupState[CostState]): CostState = {

    if (oldState.hasTimedOut) {
      val s = oldState.get
      oldState.remove

      s

    } else {

      var state: CostState = if (oldState.exists) oldState.get else CostState(
        keyId._1,
        keyId._2,
        keyId._3,
        keyId._4,
        null,
        0.0,
        0.0,
        0.0,
        0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        null,
        false
      )
      // we simply specify an old date that we can compare against and
      // immediately update based on the values in our data

      for (input <- inputs) {
        //          Resource Notify
        state.msgCount += 1
        if (state.timestamp == null) {
          state.timestamp = input.timestamp
        }
//        val avgCpu = (state.avgCpu * state.msgCount + input.resource_monitor.cpu) / (state.msgCount + 1)
//        val avgMem = (state.avgMemory * state.msgCount + input.resource_monitor.memory)/(state.msgCount + 1)

        //          store duration in miliseconds
//        state.resourceDuration += (input.timestamp.getTime - state.timestamp.getTime)
        if (input.resource_monitor != null) {
          if (state.maxCpu < input.resource_monitor.cpu_percentage) {
            state.maxCpu = input.resource_monitor.cpu_percentage
          }
          if (state.maxMemory < input.resource_monitor.memory_usage) {
            state.maxMemory = input.resource_monitor.memory_usage
          }
        }

        if (state.costQoD == 0.0 && input.cost_qod != null){
          state.costQoD = input.cost_qod
        }

        if (state.costContext == 0.0 && input.cost_context != null){
          state.costContext = input.cost_context
        }

        if (state.edgeId == null){
          state.edgeId=input.edge_id
        }

        if (input.timestamp.after(state.timestamp)) {
          state.timestamp = input.timestamp
        }

        if (input.quality_of_model != null) {
          //        compute memory by Mb
          if (input.unit_cost_resource != null) {
            var resource_m: ResourceMonitor = ResourceMonitor(state.maxCpu,
                                                              state.maxMemory / 1024 / 1024)
            state.costResource = Functions.functionMap(input.resource_function_name)(Seq(resource_m,
                                                                  input.quality_of_model.train_duration / 60,
                                                                  input.unit_cost_resource))
          }

          if (input.unit_cost_qom != null) {
            state.costQoM = Functions.functionMap(input.qom_function_name)(Seq(input.quality_of_model,
                                                        input.unit_cost_qom))
          }
          state.improvementDiff = input.quality_of_model.post_train_performance - input.quality_of_model.pre_train_performance
          state.performancePost = input.quality_of_model.post_train_performance
          state.performanceTest = input.quality_of_model.test_performance
          state.done = true
        }
        oldState.update(state)
        oldState.setTimeoutDuration(interval)
      }
      state

    }
  }
}
