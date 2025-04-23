package org.eadran.cost

import org.eadran.utils.{QualityOfModel, ResourceMonitor}
import org.json4s._
import org.json4s.jackson.JsonMethods._
import org.eadran.utils.{BaseCostResource, BaseCostQoM}
object Functions {

  implicit val formats: Formats = DefaultFormats

  val functionMap: Map[String, Seq[Any] => Double] = Map(
    "qom_cost_by_train_performance" -> { args =>
      val qom = args(0).asInstanceOf[QualityOfModel]
      val base_cost_metric = args(1).asInstanceOf[String]
      qom_cost_by_train_performance(qom, base_cost_metric)
    },
    "resource_cost_by_cpu_mem" -> { args =>
      val resource = args(0).asInstanceOf[ResourceMonitor]
      val training_time = args(1).asInstanceOf[Double]
      val base_cost_metric = args(2).asInstanceOf[String]
      resource_cost_by_cpu_memory(resource, training_time, base_cost_metric)
    }
  )

  def qom_cost_by_train_performance(measurement: QualityOfModel, base_cost_metric: String) ={
    var value = 0.0
    try {
      var basecosts = parse(base_cost_metric).extract[BaseCostQoM]
      value = math.max(0.0, (basecosts.performance * (measurement.post_train_performance
          - measurement.pre_train_performance) * measurement.pre_train_performance))
    }catch {
      case e: Exception => println("JSON object of unit cost is not correct!")
    }
    value
  }

  def resource_cost_by_cpu_memory(measurement: ResourceMonitor, training_time: Double, base_cost_metric: String) ={
    var value = 0.0
    try {
      var basecosts = parse(base_cost_metric).extract[BaseCostResource]
      value = basecosts.by_minute * training_time *
        (basecosts.cpu.getOrElse(0.0) * measurement.cpu_percentage
          + basecosts.memory.getOrElse(0.0) * measurement.memory_usage)
    }catch {
      case e: Exception => println("JSON object of unit cost is not correct!")
    }
    value
  }
}
