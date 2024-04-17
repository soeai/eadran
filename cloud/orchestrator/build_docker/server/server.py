import argparse
from typing import List, Tuple, Dict
import flwr as fl
from flwr.common import Metrics


def fit_config(rnd: int) -> Dict:
    """Send round number to client"""
    return {"fit_round": rnd}


def evaluate_config(rnd: int) -> Dict:
    """Return evaluation configuration dict for each round.
    Perform five local evaluation steps on each client (i.e., use five
    batches) during rounds one to three, then increase to ten local
    evaluation steps.
    """
    return {"val_round": rnd}


# Define metric aggregation function
def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    # Multiply accuracy of each client by number of examples used
    accuracies = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]

    # Aggregate and return custom metric (weighted average)
    return {"accuracy": sum(accuracies) / sum(examples)}


# Legacy mode
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Server Federated Learning")
    parser.add_argument('--port', help='federated server port', default="8080")
    parser.add_argument('--epochs', help='training epochs', default=5)

    params = parser.parse_args()

    # test_file = args.data
    # with open(args.config) as f:
    #     params = json.load(f)

    # Define strategy
    strategy = fl.server.strategy.FedAvg(
        on_fit_config_fn=fit_config,
        on_evaluate_config_fn=evaluate_config,
        evaluate_metrics_aggregation_fn=weighted_average)

    # Start Flower server
    fl.server.start_server(
        server_address="0.0.0.0:" + str(params.port),
        config=fl.server.ServerConfig(num_rounds=params.epochs),
        strategy=strategy
    )
