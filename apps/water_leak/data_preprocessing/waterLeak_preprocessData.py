from os.path import split
from convert2Pandas import read_raw_to_signals
import pandas as pd
import os, sys, re
import shutil
import numpy as np
import glob
from numpy.lib.stride_tricks import as_strided

"""
    Change name folder
"""


# change the name of the folders
def rename_folders(start_path):
    # list old_names and new name
    old_names = [
        "Accelerometer",
        "Dynamic Pressure Sensor",
        "Hydrophone",
        "Branched",
        "Looped",
        "Circumferential Crack",
        "Gasket Leak",
        "Longitudinal Crack",
        "No-leak",
        "Orifice Leak",
        "Background Noise",
    ]  # Replace with your old folder names
    new_names = [
        "A12",
        "P12",
        "H12",
        "BR",
        "LO",
        "CC",
        "GL",
        "LC",
        "NL",
        "OL",
        "N",
    ]  # Replace with your new folder namels

    for dirpath, dirnames, filenames in os.walk(start_path):
        for i in range(len(old_names)):
            if old_names[i] in dirnames:
                old_dir_path = os.path.join(dirpath, old_names[i])
                new_dir_path = os.path.join(dirpath, new_names[i])
                shutil.move(old_dir_path, new_dir_path)
                print(f"Renamed directory {old_dir_path} to {new_dir_path}")
                # if new_names[i] == "H12" or flag_hydrophone == 1:
                rename_folders(new_dir_path)
                rename_file(new_dir_path)


def rename_file(dirpath):
    # change file csv in Hydrophone
    for filename in os.listdir(dirpath):
        # only process if it's actually a file
        if os.path.isfile(os.path.join(dirpath, filename)) and re.search(
            "0\.\d+", filename
        ):  # replace first occurrence of '.' with '-'
            new_filename = re.sub("..", "-", filename, count=1)
            if new_filename != filename:
                os.rename(
                    os.path.join(dirpath, filename), os.path.join(dirpath, new_filename)
                )
                print(f"Renamed file {filename} to {new_filename}")
        elif os.path.isfile(os.path.join(dirpath, filename)) and re.search(
            "Background Noise", filename
        ):  # replace first occurrence of '.' with '-'
            new_filename = re.sub("Background Noise", "N", filename)
            os.rename(
                os.path.join(dirpath, filename), os.path.join(dirpath, new_filename)
            )
            print(f"Renamed file {filename} to {new_filename}")


# input the starting path
# originData2 folder
# start_path = sys.argv[1] # Replace with your start path
# rename_folders(start_path)

"""
    Hydrophone-convert-to-CSV
"""


# Convert backgroundNoise
def convert_Noise_csv(target_path):
    # last_folder = os.path.basename(target_path)

    # print (last_folder)
    pd_temp = read_raw_to_signals(target_path)
    # file_name = last_folder + ".csv"
    # Get the column names
    features = pd_temp.columns.tolist()

    # Loop through each feature
    for feature in features:
        # Create a new dataframe with only one feature
        new_df = pd_temp[[feature]]
        # Write this dataframe to a new csv
        new_df.to_csv(f"{target_path}/{feature}.csv", index=False)
    #


# Noise folder
# convert_Noise_csv(sys.argv[1])


# Covvert Branched and Looped
def convert_Hydrophone_csv(root_dir):
    # last_folder = target_path.split('/')
    last_folder = os.path.basename(root_dir)
    print("last folder: ", last_folder)

    for target_folder in ["CC", "GL", "LC", "NL", "OL"]:
        target_path = os.path.join(root_dir, target_folder)
        print("Path of target: ", target_path)

        df_hydrophone = pd.DataFrame()
        df_hydrophone = read_raw_to_signals(target_path)

        root_dir.split("/")
        file_name = last_folder + "_" + target_folder + ".csv"
        print("name: ", file_name)
        # Get the column names
        features = df_hydrophone.columns.tolist()

        # Loop through each feature
        for feature in features:
            # Create a new dataframe with only one feature
            new_df = df_hydrophone[[feature]]
            # Write this dataframe to a new csv
            new_df.to_csv(f"{target_path}/{feature}.csv", index=False)
            # df_hydrophone.to_csv(file_name, index=False)
    print("done")


# run noise vs data different from the input
# BR or LO folder in H12
# convert_Hydrophone_csv(sys.argv[1])

"""
    Create background 
    BC1: 0.18 + N + S1 
    BC2: 0.47 + N + S1
    BC3: ND   + NN    + S1

    BC5: Trans+ N + S1

    BC4: ND   + N + S2
    BC6: Trans+ NN    + S2
"""


def split_data_condition(directory_path, output_path):
    sensor_1 = ["A1.csv", "A2.csv", "P1.csv", "P2.csv"]
    sensor_2 = ["H1.csv", "H2.csv"]

    # clean folder
    # folder_names = ["BC1", "BC2", "BC3", "BC4", "BC5", "BC6"]

    # Define your conditions inside your CSV files loop
    csv_files = glob.glob(os.path.join(directory_path, "**/*.csv"), recursive=True)

    # Loop over all csv files
    for csv_file in csv_files:
        # Use os.path to get the filename without the directory
        csv_filename = os.path.basename(csv_file)

        # Split the filename by underscore
        name_parts = csv_filename.split("_")

        # flowcondition Check the parts of the name
        for part in name_parts:
            if len(name_parts) == 2:
                if "N" and name_parts[-1] in sensor_2:
                    shutil.copy2(csv_file, output_path + "condition-based/BC1")
                    shutil.copy2(csv_file, output_path + "condition-based/BC2")
                    shutil.copy2(csv_file, output_path + "condition-based/BC4")
                    shutil.copy2(csv_file, output_path + "condition-based/BC5")
            else:
                if (part == "0-18 LPS" and name_parts[-1] in sensor_1) or (
                    part == "0-18 LPS" and "N" and name_parts[-1] in sensor_2
                ):
                    shutil.copy2(csv_file, output_path + "condition-based/BC1")

                if (part == "0-47 LPS" and name_parts[-1] in sensor_1) or (
                    part == "0-47 LPS" and "N" and name_parts[-1] in sensor_2
                ):
                    shutil.copy2(csv_file, output_path + "condition-based/BC2")

                if (part == "ND" and name_parts[-1] in sensor_1) or (
                    part == "ND" and "NN" in name_parts and name_parts[-1] in sensor_2
                ):
                    shutil.copy2(csv_file, output_path + "condition-based/BC3")

                if part == "ND" and "N" in name_parts and name_parts[-1] in sensor_2:
                    shutil.copy2(csv_file, output_path + "condition-based/BC4")

                if (part == "Transient" and name_parts[-1] in sensor_1) or (
                    part == "Transient"
                    and "N" in name_parts
                    and name_parts[-1] in sensor_2
                ):
                    shutil.copy2(csv_file, output_path + "condition-based/BC5")

                if (
                    part == "Transient"
                    and "NN" in name_parts
                    and name_parts[-1] in sensor_2
                ):
                    shutil.copy2(csv_file, output_path + "condition-based/BC6")


# originData tri-data
# split_data_condition(sys.argv[1], sys.argv[2])
"""
    sum all csv_files
"""


def possible_csv(data):
    # set_topo = ["BR", "LO"]
    set_leak = ["CC", "GL", "LC", "NL", "OL"]
    set_sensorDic = ["A12", "P12", "H12"]

    set_dic = []

    # add data['dataPath'] with each sensor with topology
    if data["topology"] == None:
        for sensor in set_sensorDic:
            set_dic.append(os.path.join(data["dataPath"], sensor, "BR"))
            set_dic.append(os.path.join(data["dataPath"], sensor, "LO"))

    else:
        for sensor in set_sensorDic:
            set_dic.append(os.path.join(data["dataPath"], sensor, data["topology"]))

    # add data['dataPath'] with leak types
    if data["leakType"] == None:
        for dic in set_dic[:]:
            for leak in set_leak:
                set_dic.append(os.path.join(dic, leak))
            set_dic.remove(dic)
    else:
        for dic in set_dic:
            set_dic.append(os.path.join(dic, data["leakType"]))
            set_dic.remove(dic)
    set_dic.append(os.path.join(data["dataPath"], "H12", "N"))

    return set_dic


"""
    Sampling
"""


def generate_feature_sampling_overlap(
    directory, second, number_features, overlapping_size
):
    sensor_1 = ["A1.csv", "A2.csv", "P1.csv", "P2.csv"]
    sensor_2 = ["H1.csv", "H2.csv"]

    all_files = glob.glob(directory + "/*.csv")

    df_ = pd.DataFrame()

    df_topology = None
    df_target = None
    df_condition = None
    # add features from the consider file
    for filename in all_files:
        df_temp = pd.DataFrame()
        # splitting file name
        splitted_filename = filename.split("_")
        print(filename)

        # A12 or P12 - return dictionary
        if splitted_filename[-1] in sensor_1:
            df_temp = generate_features_A12P12(
                filename,
                splitted_filename[-1],
                second,
                number_features,
                overlapping_size,
            )

            df_topology = os.path.basename(splitted_filename[0])
            df_target = splitted_filename[1]
            df_condition = splitted_filename[2]

        # H12 - return dictionary
        if splitted_filename[-1] in sensor_2 and len(splitted_filename) > 2:
            df_temp = generate_features_H12(
                filename,
                splitted_filename[-1],
                second,
                number_features,
                overlapping_size,
            )

        print("split_filename: ", splitted_filename)

        df_ = pd.concat([df_, df_temp], axis=1)

    df_["topology"] = df_topology
    df_["target"] = df_target
    df_["condition"] = df_condition

    return df_


def windowed_view_df(df, window, overlap):
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Input should be a pandas DataFrame")

    arr = df.values
    window_step = window - overlap
    num_windows = (arr.shape[0] - overlap) // window_step

    if num_windows < 1 or arr.shape[0] < window:
        raise ValueError("Window size or overlap is invalid for the given DataFrame")

    # Generate windows using as_strided
    new_shape = (num_windows, window, arr.shape[1])
    new_strides = (window_step * arr.strides[0], arr.strides[0], arr.strides[1])
    windows_arr = as_strided(arr, shape=new_shape, strides=new_strides)

    # Convert each window back to a DataFrame
    windows_df = [
        pd.DataFrame(windows_arr[i], columns=df.columns) for i in range(num_windows)
    ]

    return windows_df


def generate_features_A12P12(filename, sensor, second, num_features, overlap_rate):
    # Initialize a list to store the features for each chunk
    df = pd.read_csv(filename, index_col=None, header=0)

    # Add a column for the integer second part of each sample
    df["Sample"] = df["Sample"].astype(int)

    # [0, 29]
    df = df[df["Sample"] <= 29]

    all_instance_list = df["Sample"].value_counts()
    # print(all_instance_list)
    window_size = (all_instance_list[all_instance_list.index == 0].values).flat[
        0
    ] * second
    overlap_size = int((window_size * overlap_rate).astype(int))

    # counting the all records in a group
    data_split_list = windowed_view_df(df, window_size, overlap_size)

    result = pd.DataFrame()
    for df_chunk in data_split_list:
        # Calculate the group means using the specified number of groups
        grouped_means = calculate_group_means(df_chunk, num_features, sensor)
        grouped_means[sensor + "mean"] = df_chunk["Value"].mean()
        grouped_means[sensor + "std"] = df_chunk["Value"].std()
        grouped_means["time"] = df_chunk["Sample"]
        # print(grouped_means.head())
        result = pd.concat([result, grouped_means], ignore_index=True)
    # Convert the features list to a DataFrame
    return result


def generate_features_H12(filename, sensor, second, num_features, overlap_rate):
    # Initialize a list to store the features for each chunk
    df = pd.read_csv(filename, index_col=None, header=0)
    df.columns = ["Value"]

    name_without_extension = os.path.splitext(os.path.basename(filename))[0]
    splitted_filename = name_without_extension.split("_")

    window_size = 8000 * second

    if splitted_filename[-2] == "N":
        directory_path = os.path.dirname(filename)
        filename_noise = (
            directory_path
            + "/"
            + splitted_filename[-2]
            + "_"
            + splitted_filename[-1]
            + ".csv"
        )
        pd_N_file = pd.read_csv(filename_noise, index_col=None, header=0)
        pd_N_file.columns = ["Value"]

        # Create a grouping variable
        pd_N_file["Block"] = (pd_N_file.index // window_size) + 1

        # Group by the 'Block' column
        pd_N_file.groupby("Block")

        overlap_size = int(window_size * overlap_rate)

        # counting the all records in a group
        N_data_split_list = windowed_view_df(pd_N_file, window_size, overlap_size)

        N_result = pd.DataFrame()
        for N_df_chunk in N_data_split_list:
            # Dynamically get the name of the column
            column_name = N_df_chunk.columns[0]
            # Calculate the group means using the specified number of groups
            N_grouped_means = calculate_group_means(
                N_df_chunk, num_features, "N_" + sensor
            )
            N_grouped_means[sensor + "mean"] = N_df_chunk[column_name].mean()
            N_grouped_means[sensor + "std"] = N_df_chunk[column_name].std()
            N_grouped_means["time"] = N_df_chunk["Block"]

            N_result = pd.concat([N_result, N_grouped_means], ignore_index=True)
        # print(N_result)
    else:
        N_result = None

    # Create a grouping variable
    df["Block"] = (df.index // window_size) + 1

    # Group by the 'Block' column
    df.groupby("Block")
    overlap_size = int(window_size * overlap_rate)
    # counting the all records in a group
    data_split_list = windowed_view_df(df, window_size, overlap_size)

    result = pd.DataFrame()
    for df_chunk in data_split_list:
        column_name = df_chunk.columns[0]
        # Calculate the group means using the specified number of groups
        grouped_means = calculate_group_means(df_chunk, num_features, sensor)
        grouped_means[sensor + "mean"] = df_chunk[column_name].mean()
        grouped_means[sensor + "std"] = df_chunk[column_name].std()
        grouped_means["time"] = df_chunk["Block"]

        result = pd.concat([result, grouped_means], ignore_index=True)

    return pd.concat([result, N_result], axis=1)


def calculate_group_means(df, num_groups, sensor_name):
    # Determine group sizes
    n = len(df)
    group_sizes = np.full(num_groups, n // num_groups)
    group_sizes[: n % num_groups] += 1

    # Assign groups
    group_indices = np.concatenate(
        [np.full(size, i + 1) for i, size in enumerate(group_sizes)]
    )
    df["Group"] = group_indices[:n]

    # Group by the 'Group' column and calculate the mean for each group
    grouped_means = df.groupby("Group")["Value"].mean().reset_index()
    grouped_means_transpose = grouped_means.transpose()

    # Assign new indices (feature names)
    grouped_means_transpose.columns = [
        sensor_name + str(i) for i in range(grouped_means_transpose.shape[1])
    ]

    # Remove the 'Second' record
    grouped_means_transpose = grouped_means_transpose.drop(index="Group")

    # Rename the indices
    grouped_means_transpose.reset_index(drop=True, inplace=True)

    return grouped_means_transpose
