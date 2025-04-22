package org.eadran.cost

import org.eadran.utils.{QualityOfModel, ResourceMonitor}
import org.json4s._
import org.json4s.jackson.JsonMethods._
object Functions {

  implicit val formats: Formats = DefaultFormats

  val functionMap: Map[String, Seq[Any] => Double] = Map(
    "ucc_qom_cost_eval" -> { args =>
      val model = args(0).asInstanceOf[QualityOfModel]
      val str = args(1).asInstanceOf[String]
      ucc_qom_cost_eval(model, str)
    },
    "ucc_resource_cost_eval" -> { args =>
      val model = args(0).asInstanceOf[ResourceMonitor]
      val time = args(1).asInstanceOf[Double]
      val cost = args(2).asInstanceOf[String]
      ucc_resource_cost_eval(model, time, cost)
    }
  )

  def ucc_qom_cost_eval(input: QualityOfModel, unit_costs: String) ={
    var ucosts: JValue = parse(unit_costs)
    val value = math.max(0.0,
      (ucosts\"performance").extract[Double] * (input.post_train_performance - input.pre_train_performance) * input.pre_train_performance)
    value
  }

  def ucc_resource_cost_eval(input: ResourceMonitor, time_duration: Double, unit_cost: String) ={
    val ucosts = parse(unit_cost)
    val value = (ucosts\"time").extract[Double] * time_duration * ((ucosts\"cpu").extract[Double] * input.cpu_percentage
      + (ucosts\"ram").extract[Double] * input.memory_usage)
    value
  }
}
