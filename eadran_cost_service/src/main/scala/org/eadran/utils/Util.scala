package org.eadran.utils

import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.types.StructType

import java.sql.Timestamp
import java.time.{LocalDateTime, ZoneOffset}
import scala.reflect.runtime.currentMirror
import scala.tools.reflect.ToolBox
import java.lang.Double

object Util {
  val toolbox = currentMirror.mkToolBox()
  def uuid = java.util.UUID.randomUUID.toString
  def localToGMT() = {

    val utc = LocalDateTime.now(ZoneOffset.UTC)
    Timestamp.valueOf(utc)

  }
  def eval(exp: String) ={
    val compe = toolbox.eval(toolbox.parse(exp))
    val value = math.max(0.0, Double.parseDouble(compe.toString))
    value
  }

  def mesageSchema(spark: SparkSession) = {

    import spark.implicits._

    val qom = new StructType()
      .add($"report.quality_of_model.post_train_performance".double)
      .add($"report.quality_of_model.pre_train_performance".double)
      .add($"report.quality_of_model.pre_loss_value".double)
      .add($"report.quality_of_model.post_loss_value".double)
      .add($"report.quality_of_model.train_round".long)
      .add($"report.quality_of_model.train_duration".double)
      .add($"report.quality_of_model.test_performance".double)
      .add($"report.quality_of_model.test_loss".double)
      .add($"report.quality_of_model.evaluate_on_test".boolean)

    val resource = new StructType()
      .add($"report.resource_monitor.cpu_percentage".double)
      .add($"report.resource_monitor.memory_usage".double)

    val message = new StructType()
      .add($"metadata.name".string)  //edge_id
      .add($"metadata.run_id".string)
      .add($"metadata.functionality".string) //dataset_id
      .add($"metadata.application_name".string) // model_id
      .add($"train_round".long) //???
      .add($"timestamp".timestamp)
      .add("quality_of_model", qom)
      .add("resource_monitor", resource)

    message
  }
}
