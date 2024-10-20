package org.eadran.utils

import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.types.{StructField, _}

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

    val message = new StructType(Array(
      StructField("metadata", StructType(Array(
        StructField("name", StringType, true),
        StructField("run_id", StringType, true),
        StructField("functionality", StringType, true),
        StructField("application_name", StringType, true)
      ))),
      StructField("timestamp", TimestampType, true),
      StructField("report", StructType(Array(
        StructField("train_round", IntegerType, true),
        StructField("quality_of_model",StructType(Array(
          StructField("post_train_performance", DoubleType, true),
          StructField("pre_train_performance", DoubleType, true),
          StructField("pre_loss_value", DoubleType, true),
          StructField("post_loss_value", DoubleType, true),
          StructField("train_duration", DoubleType, true),
          StructField("test_performance", DoubleType, true),
          StructField("test_loss", DoubleType, true),
//          StructField("evaluate_on_test", IntegerType, true)
        )),true),
        StructField("resource_monitor",StructType(Array(
          StructField("cpu_percentage", DoubleType, true),
          StructField("memory_usage", DoubleType, true),
//          StructField("gpu", DoubleType, true),
//          StructField("network", DoubleType, true),
//          StructField("storage", DoubleType, true),
        )),true)
      ))),
    ))

    message
  }
}
