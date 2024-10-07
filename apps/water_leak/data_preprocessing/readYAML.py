import yaml, os, glob

import waterLeak_preprocessData
import shutil
import argparse

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

# Clean data? in the INPUTPATH
# Change name folder
full_subdir_path = os.path.join(data["dataPath"], "A12")

# Check if the subdirectory exists
if os.path.isdir(full_subdir_path):
    print(f"sort name exists in '{data['dataPath']}'")
else:
    print(f"sort name does not exist in '{data['dataPath']}'")
    waterLeak_preprocessData.rename_folders(data["dataPath"])


## convert Hydrophone to CSV
full_subdir_path_hydrophone = os.path.join(data["dataPath"], "H12", "N")
csv_hydrophone = glob.glob(full_subdir_path_hydrophone + "/*.csv")
if csv_hydrophone:
    print("Already converted from RAW to CSV")
else:
    print("Not yet convert from RAW to CSV")
    waterLeak_preprocessData.convert_Noise_csv(data["dataPath"] + "H12/N/")
    waterLeak_preprocessData.convert_Hydrophone_csv(data["dataPath"] + "H12/BR/")
    waterLeak_preprocessData.convert_Hydrophone_csv(data["dataPath"] + "H12/LO/")


# Split data - OUTPUTPATH
## collect all csv files satisfy requirements
set_dic = waterLeak_preprocessData.possible_csv(data)


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
    waterLeak_preprocessData.split_data_condition(dic, data["outputPath"])


# Sampling_second
# #
# set_BC = ['BC1', 'BC2', 'BC3', 'BC4', 'BC5', 'BC6']
#
for BC in set_BC:
    directory = os.path.join(data["outputPath"], "condition-based")
    df = waterLeak_preprocessData.generate_feature_sampling_overlap(
        os.path.join(directory, BC),
        data["sampling_second"],
        data["sampling_size"],
        data["overlap"],
    )
    filename = os.path.join(directory, f"{BC}.csv")
    # Save dataframe to CSV
    df.to_csv(filename, index=False)
