package org.eadran.stream

import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.streaming.{GroupStateTimeout, Trigger}
import org.eadran.utils.{Message, Util}
import org.apache.spark.SparkFiles
//import org.apache.spark.sql.cassandra._

object StreamProcessing {

  /**
   * operation system information
   */
  @transient val sys = System.getProperty("os.name")

  /**
   * application name
   */
  val appName = getClass.getCanonicalName

  /**
   * logger
   */
  //    @transient lazy val log = org.apache.log4j.LogManager.getLogger(getClass.getCanonicalName)

  def main(args: Array[String]) {

          if (args.length < 5){
            println("COMMAND: spark-submit --packages ....")
            println("<jar_file>")
            println("</path/checkpoint>")
            println("kafka-brokers: ip:port")
            println("kafka topic_in")
            println("kafka topic_out")
            println("url of cost formula")
    //        println("cassandra host")
    //        println("cassandra port")
            System.exit(1)
          }

    val checkpoint = args(0)

    /**
     * init kafka broker and topic
     */
    val kafkaBrokers = args(1)
    val kafkaTopic_in = args(2)
    val kafkaTopic_out = args(3)
    val json_url = args(4)

    /**
     * init cassandra host and port
     */
//      val cassandraHost = args(4) // "127.0.0.1"
//      val cassandraPort = args(5) //"9042"
//      val cassandra_keyspace = "eadran"
//      val cassandra_tablename = "tbl_cost_formula_streaming"
//      val cassandra_save_table = "tbl_cost_streaming"

    /**
     * init state management module
     */
    val stateMgmt = new StateMgmt()

    /**
     * get or create sparkSession
     */
    val spark = if (sys.startsWith("Mac")) {
      SparkSession
        .builder
        .appName(appName)
        .master("local[*]")
        .getOrCreate()
    } else {
      SparkSession
        .builder
        .appName(appName)
        .getOrCreate()
    }
    import spark.implicits._

    /**
     * setup spark configuration
     */
    spark.conf.set("spark.sql.shuffle.partitions", 8)
    spark.conf.set("spark.sql.streaming.metricsEnabled", "true")
    spark.conf.set("spark.streaming.stopGracefullyOnShutdown", "true")
    spark.sparkContext.setLogLevel("ERROR")
//    spark.setCassandraConf(Map(
//      "spark.cassandra.connection.host" -> cassandraHost,
//      "spark.cassandra.connection.port" -> cassandraPort
//    ))

//    spark.sparkContext.addFile(url_csv)
    val schema = Util.mesageSchema(spark)

    /**
     * read event stream from Kafka
     */
//    println(kafkaBrokers)
    val eventsStream = spark.readStream
      .format("kafka")
      .option("kafka.bootstrap.servers", kafkaBrokers)
      .option("subscribe", kafkaTopic_in)
      .option("startingOffsets", "latest")
      .option("failOnDataLoss", false)
      .load()
      .selectExpr( /**"timestamp",**/ "CAST(key AS STRING)", "CAST(value AS STRING)")
      .select(from_json($"value", schema).alias("json"))
      .select("json.metadata.name",
        "json.metadata.run_id",
        "json.metadata.functionality",
        "json.metadata.application_name",
        "json.timestamp",
        "json.report.*")

//    eventsStream.writeStream
//      .trigger(Trigger.ProcessingTime("10 seconds"))
//      .format("console")
//      .option("checkpointLocation", checkpoint)
//      .outputMode("update")
//      .start()

//    load static info from json/csv file
    val staticStream = spark.sqlContext.read.option("multiline", "true").json(json_url)
//    val staticStream = spark.sqlContext.read.option("header", true).csv("file://" + SparkFiles.get(csv_file))
//    val staticStream = spark.sqlContext.read.json("file://" + SparkFiles.get(json_url))
      .select($"model_id".alias("model_id"),
        $"data_source_id".alias("dataset_id"),
        $"qom_cost_function",
        to_json($"qom_base_cost").alias("qom_base_cost"),
        $"resource_cost_function",
        to_json($"resource_base_cost").alias("resource_base_cost"),
        $"cost_quantity_quality".cast("double").alias("cost_quantity_quality"),
        $"cost_context".cast("double").alias("cost_context"))

//    load static info from cassandra
//    val staticStream = spark.read
//      .format("org.apache.spark.sql.cassandra")
//      .option("keyspace", cassandra_keyspace)
//      .option("table", cassandra_tablename)
//      .load()

//    join two streams
    val joinStream = eventsStream.join(staticStream,
          eventsStream("application_name")===staticStream("model_id") &&
          eventsStream("functionality")===staticStream("dataset_id"), "leftOuter")
      .select($"model_id",$"run_id",$"dataset_id",$"timestamp",$"name".alias("edge_id"),$"train_round",
        $"quality_of_model",$"resource_monitor", $"qom_cost_function", $"qom_base_cost",
        $"resource_cost_function", $"resource_base_cost",$"cost_quantity_quality",$"cost_context"
      ).as[Message]

//    joinStream.writeStream
//      .trigger(Trigger.ProcessingTime("10 seconds"))
//      .format("console")
//      .option("checkpointLocation", checkpoint)
//      .outputMode("update")
//      .start()

//  Compute the cost using stateful functionality of Spark
    val finalStream = joinStream
      .groupByKey(x => (x.model_id, x.run_id, x.dataset_id, x.train_round))
      .mapGroupsWithState(GroupStateTimeout.ProcessingTimeTimeout())(stateMgmt.computeCost)
      .filter($"done" === "true")
      .select($"modelId".alias("model_id"),
        $"runId".alias("run_id"),
        $"datasetId".alias("dataset_id"),
        $"trainRound".alias("train_round"),
        $"timestamp",
        $"edgeId".alias("edge_id"),
        $"costResource".alias("cost_resource"),
        $"costQoM".alias("cost_qom"),
        $"costQoD".alias("cost_qod"),
        $"costContext".alias("cost_context"),
        $"improvementDiff".alias("improvement_diff"),
        $"performancePost".alias("performance_post"),
        $"performanceTest".alias("performance_test"),
        )


//    ========= TO KAFKA ========
//    finalStream
//      .selectExpr("to_json(struct(*)) AS value")
//      .writeStream
//      .trigger(Trigger.ProcessingTime("10 seconds"))
//      .format("kafka")
//      .option("checkpointLocation", checkpoint)
//      .option("kafka.bootstrap.servers", kafkaBrokers)
//      .option("topic", kafkaTopic_out)
//      .outputMode("update")
//      .start()

//    ========= TO CONSOLE ========
    finalStream
      .writeStream
      .trigger(Trigger.ProcessingTime("10 seconds"))
      .format("console")
      .option("checkpointLocation", checkpoint)
      .outputMode("update")
      .start()

//    ========= TO CASSANDRA ========
//    finalStream
//        .writeStream
//        .trigger(Trigger.ProcessingTime("60 seconds"))
//        .foreachBatch { (batchDF: DataFrame, batchId: Long) =>
//          batchDF.write       // Use Cassandra batch data source to write streaming out
//            .cassandraFormat(cassandra_save_table, cassandra_keyspace)
//            .mode("append")
//            .save()
//        }
//        .outputMode("update")
//        .start()

//    ========= TO ELASTICSEARCH ========
//    finalStream.writeStream
//      .foreachBatch{(batchDF: DataFrame, batchId: Long) =>
//      batchDF.write.format("org.elasticsearch.spark.sql")
//        .option(ConfigurationOptions.ES_NODES, es_host)
//        .option(ConfigurationOptions.ES_PORT, es_port)
//        .mode("append")
//        .save(ES_keystore)
//    }.outputMode("update")
//      .start()

    /**
     * Wait until any of the queries on the associated SQLContext has terminated
     */
    spark.streams.awaitAnyTermination()

    spark.stop()
  }
}
