from os.path import split
import yaml, sys, os, glob
import pandas as pd

# import pre_processData
import dataLeak_preprocessData
import numpy as np
import shutil
import argparse

# from src.dataLeak_preprocessData import split_time_series_data

parser = argparse.ArgumentParser(
    description="""My Description. And what a description it is. """,
    epilog="""All is well that ends well.""",
)

parser.add_argument(
    "--f",
    dest="data",
    metavar="*.yml",
    action="store",
    type=str,
    default="input.yml",
    help="Read an yaml file (default input.yml)",
)

args = parser.parse_args()

print(args.data)

data = args.data

with open(data, "r") as f:
    data = yaml.load(f, Loader=yaml.SafeLoader)

# Print the values as a dictionary
# print(data)

# Clean data? in the INPUTPATH
# Change name folder
full_subdir_path = os.path.join(data["dataPath"], "A12")

# Check if the subdirectory exists
if os.path.isdir(full_subdir_path):
    print(f"sort name exists in '{data['dataPath']}'")
else:
    print(f"sort name does not exist in '{data['dataPath']}'")
    dataLeak_preprocessData.rename_folders(data["dataPath"])


## convert Hydrophone to CSV
full_subdir_path_hydrophone = os.path.join(data["dataPath"], "H12", "N")
csv_hydrophone = glob.glob(full_subdir_path_hydrophone + "/*.csv")
if csv_hydrophone:
    print("Already converted from RAW to CSV")
else:
    print("Not yet convert from RAW to CSV")
    dataLeak_preprocessData.convert_Noise_csv(data["dataPath"] + "H12/N/")
    dataLeak_preprocessData.convert_Hydrophone_csv(data["dataPath"] + "H12/BR/")
    dataLeak_preprocessData.convert_Hydrophone_csv(data["dataPath"] + "H12/LO/")


# Split data - OUTPUTPATH
## collect all csv files satisfy requirements
set_dic = dataLeak_preprocessData.possible_csv(data)

print("print Dic from data yaml", set_dic)

set_BC = ["BC1", "BC2", "BC3", "BC4", "BC5", "BC6"]

old_folder = os.path.join(data["outputPath"], "condition-based/")
if os.path.isdir(old_folder):  # checks if the folder exists
    shutil.rmtree(old_folder)  # removes the directory and all its contents

os.mkdir(old_folder)
for folder in set_BC:
    full_path = os.path.join(data["outputPath"] + "condition-based/", folder)
    os.mkdir(full_path)  # creates the directory again


for dic in set_dic:
    # can change os.path.join(data['outputPath'], 'some/more\ detail/'
    dataLeak_preprocessData.split_data_condition(dic, data["outputPath"])


# Sampling_second
# #
# set_BC = ['BC1', 'BC2', 'BC3', 'BC4', 'BC5', 'BC6']
#
#

all_df = pd.DataFrame()

train_df = pd.DataFrame()
test_df = pd.DataFrame()

for BC in set_BC:
    directory = os.path.join(data["outputPath"], "condition-based", BC)
    print("directory: ", directory)

    BC_folder_set = dataLeak_preprocessData.pattern_for_BC(directory)
    # List all items in the directory
    # items = os.listdir(directory)

    # Filter the list to include only directories

    df_BC = pd.DataFrame()

    print("BC folder: ", BC_folder_set)

    for BC_folder in BC_folder_set:
        df = dataLeak_preprocessData.generate_feature_sampling_overlap(
            os.path.join(directory),
            BC_folder,
            data["sampling_second"],
            data["sampling_size"],
            data["overlap"],
        )
        # Assuming df_BC and df are your DataFrames
        # Check for duplicate index values in df_BC

        filename_BC2 = os.path.join(directory, f"{BC_folder}.csv")
        # # Save dataframe to CSV
        df.to_csv(filename_BC2, index=False)

        train_df, test_df = dataLeak_preprocessData.split_time_series_data(
            df, filename_BC2, data["test_fraction"]
        )

        # filename = os.path.join(directory, f"{pattern}.csv")
        df_BC = pd.concat([df_BC, df], ignore_index=True)
        train_df = pd.concat([train_df, train_df], ignore_index=True)
        test_df = pd.concat([test_df, test_df], ignore_index=True)

    filename_BC = os.path.join(directory, "..", f"{BC}.csv")
    # # Save dataframe to CSV
    df_BC.to_csv(filename_BC, index=False)

    all_df = pd.concat([all_df, df_BC], ignore_index=True)

# # Save dataframe to CSV
# Scenario_1
all_df.to_csv(data["outputPath"] + "ALL.csv", index=False)

# Scenario_3
train_df.to_csv(
    data["outputPath"] + f"{data["test_fraction"]}ALL_train.csv", index=False
)
test_df.to_csv(data["outputPath"] + f"{data["test_fraction"]}ALL_test.csv", index=False)

# Scenario_2
dataLeak_preprocessData.split_data(
    data["outputPath"] + "ALL.csv",
    data["outputPath"],
    data["test_fraction"],
    data["number_provider"],
)
