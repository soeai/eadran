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
      .add($"train_performance_after".double)
      .add($"train_performance_before".double)
      .add($"loss_value_after".double)
      .add($"loss_value_before".double)
      .add($"test_performance_after".double)
      .add($"test_performance_before".double)
      .add($"duration".double)

    val resource = new StructType()
      .add($"cpu".double)
      .add($"memory".long)
      .add($"gpu".double)
      .add($"network".double)
      .add($"storage".long)

    val message = new StructType()
      .add($"model_id".string)
      .add($"run_id".string)
      .add($"dataset_id".string)
      .add($"edge_id".string)
      .add($"train_round".long)
      .add($"timestamp".timestamp)
      .add("quality_of_model", qom)
      .add("resource_monitor", resource)

    message
  }
}
