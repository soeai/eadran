package org.eadran.stream

import org.apache.spark.sql.streaming.GroupState
import org.eadran.utils.{CostState, Message, Util}

class StateMgmt() extends Serializable {

  //    @transient lazy val log = org.apache.log4j.LogManager.getLogger(getClass.getCanonicalName)

  val interval = 60 * 1000 * 5 //5 minutes

  //    log.info("spot interval set to " + interval)

  def computeCost( keyId: (String, String, String, Long),
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
        state.resourceDuration += (input.timestamp.getTime - state.timestamp.getTime)
        state.maxCpu = state.maxCpu > input.resource_monitor.cpu ? state.maxCpu : input.resource_monitor.cpu
        state.maxMemory = state.maxMemory > input.resource_monitor.memory? state.maxMemory: input.resource_monitor.memory

//        compute memory by Mb
        val eval_resource = input.resource_function
          .replace("$cpu",state.maxCpu.toString)
          .replace("$memory",(state.maxMemory/1024/1024).toString)
          .replace("$gpu",input.resource_monitor.gpu.toString)
          .replace("$network",input.resource_monitor.network.toString)
          .replace("$storage",input.resource_monitor.storage.toString)
          .replace("$duration",(state.resourceDuration/60000/60).toString)  // convert duration to hour

        state.costResource = Util.eval(eval_resource)

        if (state.costQoD == 0.0){
          state.costQoD = input.cost_qod
        }

        if (state.costContext == 0.0){
          state.costContext = input.cost_context
        }

        if (state.edgeId == null){
          state.edgeId=input.edge_id
        }

        if (input.timestamp.after(state.timestamp)) {
          state.timestamp = input.timestamp
        }

        if (input.quality_of_model != null) {
          val eval_qom = input.qom_function
            .replace("$train_performance_after",input.quality_of_model.train_performance_after.toString)
            .replace("$train_performance_before", input.quality_of_model.train_performance_before.toString)
            .replace("$test_performance_after",input.quality_of_model.test_performance_after.toString)
            .replace("$test_performance_before",input.quality_of_model.test_performance_before.toString)
            .replace("$loss_value_after",input.quality_of_model.loss_value_after.toString)
            .replace("$loss_value_before",input.quality_of_model.loss_value_before.toString)
            .replace("$duration",input.quality_of_model.duration.toString)

          state.costQoM =  Util.eval(eval_qom)
          state.improvementDiff = input.quality_of_model.train_performance_after - input.quality_of_model.train_performance_before
          state.performancePost = input.quality_of_model.train_performance_after
          state.done = true
        }
        oldState.update(state)
        oldState.setTimeoutDuration(interval)
      }
      state

    }
  }
}
