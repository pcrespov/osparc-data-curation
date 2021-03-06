import csv
import json
import os
from datetime import date, datetime
from pathlib import Path

from blackfynn import Blackfynn
from blackfynn.models import Collection

import datcore as dc
from dataset_descriptor import DatasetDescriptor
from file_descriptor import FileDescriptors, FileDescriptor

dir_path = os.path.dirname(os.path.realpath(__file__))
api_token = os.environ.get("BF_API_KEY", "none")
api_secret = os.environ.get("BF_API_SECRET", "none")

client = dc.DatcoreClient(api_token=api_token, api_secret=api_secret)

ds = client.create_dataset("Curation")
client.delete_files(ds)

study_name = "osparc-dataset-template"

study_folder = Path(dir_path).parent / Path(study_name)
study_file = Path(study_folder) / Path("study/project.json")
files_folder = study_folder / Path("files")
docs_folder = study_folder / Path("docs")


def submission(root_folder: Path):
    filename = Path(root_folder) / Path("submission.csv")
    with open(str(filename), 'w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(["SPARC Award number", "OT3OD025348"])
        writer.writerow(["Milestone achieved", "Milestone 0.0.1"])
        writer.writerow(["Milestone completion date", date.today()] )
        
def dataset_description(root_folder: Path, study_file: Path):
    filename = Path(root_folder) / Path("dataset_description.csv")
    dd = DatasetDescriptor()
    dd.from_study_file(study_file)
    dd.dump_to_csv(filename)


def files_manifest(study_fle: Path, files_folder: Path):
    # read the study and find all files referenced as outputs
    with open(str(study_file)) as json_file:
        data = json.load(json_file)
        prj_id = data["uuid"]
        workbench = data["workbench"]
        for node in workbench:
            # parse current node and search for outputfiles, add metadata for it in the nodes schema
            n = workbench[node]
            node_id = node
            fd = FileDescriptors()
            outputs = n["outputs"]
            schema = n["schema"]["outputs"]
            manifest_filename = Path(files_folder) / Path(prj_id) / Path(node_id)
            for output in outputs:
                output_port = outputs[output]
                if output in schema.keys():
                    if "data:" in schema[output]["type"]:
                        filename = Path(output_port['path']).name
                        timestamp = str(datetime.now())
                        desc = schema[output]['description']
                        filetype = schema[output]["type"]
                        _fd = FileDescriptor(filename, timestamp, desc, filetype)
                        fd.add_descriptor(_fd)
                        print(output, Path(output_port['path']).name, schema[output]['description'], schema[output]["type"])
            fd.dump_to_csv(manifest_filename)

def docs_manifest(study_fle: Path, docs_folder: Path):
    # read the study and find all files referenced as outputs
    with open(str(study_file)) as json_file:
        data = json.load(json_file)
        fd = FileDescriptors()
        filename = data["example_image_filename"]
        timestamp = str(datetime.now())
        desc = data["example_image_description"]
        filetype = "image/png"
        _fd = FileDescriptor(filename, timestamp, desc, filetype)
        fd.add_descriptor(_fd)
        fd.dump_to_csv(docs_folder)

        
submission(study_folder)
dataset_description(study_folder, study_file)
files_manifest(study_file, files_folder)
docs_manifest(study_file, docs_folder)

def recursive_upload(destination, files):
    dirs = [f for f in files if os.path.isdir(f)]
    files = [f for f in files if os.path.isfile(f)]

    if len(files) > 0:
        client.upload_file(destination, files)
        #print("uploading files: " , files)

    for d in dirs:
        name = os.path.basename(os.path.normpath(d))
        print('Uploading to {}'.format(name))

        new_collection = Collection(name)
        destination.add(new_collection)

        files = [os.path.join(d,f) for f in os.listdir(d) if not f.startswith('.')]
        recursive_upload(new_collection, files)


files = [os.path.join(study_folder, f) for f in os.listdir(str(study_folder))]
recursive_upload(ds, files)
