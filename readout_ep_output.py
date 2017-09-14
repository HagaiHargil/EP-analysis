"""
__author__ = Hagai Hargil
"""
from typing import Dict
import h5py
import re
import os
from pathlib import Path
import pandas as pd
import attr
from itertools import chain


def walk_ep_dirs_old(directory: str, file_end: str, list_of_wanted):
    """ Walk through dir, finding files ending with file_end """

    dict_of_data: Dict = {}

    # Find *_with_compiled.mat and load it into memory
    reg_file = re.compile(file_end)
    reg_fov = re.compile(r'(FOV_\d)')
    for root, dirs, files in os.walk(directory):
        for file in files:
            if reg_file.search(file):
                data = h5py.File(os.path.join(root, file), 'r')
                fov = reg_fov.findall(root)[0]
                print(os.path.join(root, file))
                for name, vars_ in data.items():
                    if name == 'compiled':
                        for name in vars_:
                            if name in list_of_wanted:
                                if "HYPO" in root:
                                    key_of_dict = file[:-4] + "_" + name + "_" + fov + "_HYPO"
                                if "HYPER" in root:
                                    key_of_dict = file[:-4] + "_" + name + "_" + fov + "_HYPER"
                                dict_of_data[key_of_dict] = vars_.get(name).value
                                # with open((root + file + name + '.csv'), 'wb') as f:
                                #     np.savetxt(f, vars_.get(name).value, delimiter=',')

    return dict_of_data

def extract_data_from_ep_dirs(directory: str, file_end: str, list_of_wanted):
    """ Simpler iteration over dirs """

    identifiers = ['animalID', 'conditionID', 'daysAfterBaseline', 'FOV']
    df_cols = identifiers + list_of_wanted
    df = pd.DataFrame([], columns=df_cols)
    for file in Path(directory).rglob(file_end):
        print(file)
        data = h5py.File(file, 'r')['compiled']
        data_for_df = [data[field] for field in list_of_wanted]
        id_object = IdentifierExtractor(identifiers.copy(), file)
        id_object.populate_list()
        helper_df = pd.DataFrame([id_object.result + data_for_df], columns=df_cols)
        df = df.append(helper_df, ignore_index=True)

    df.set_index(identifiers, drop=True, inplace=True)
    return df


@attr.s(slots=True)
class IdentifierExtractor(object):
    """ Parse the filename and extract the relevant data """

    identifiers = attr.ib()
    pathobj = attr.ib()
    result = attr.ib(init=False)

    def populate_list(self):
        self.result = []
        for iden in self.identifiers[:]:
            try:
                self.result.append(getattr(IdentifierExtractor, iden)(self))
            except:
                print(f"Method {iden} doesn't exist.")

            self.identifiers.remove(iden)

        if len(self.identifiers) > 0:
            raise UserWarning(f"Items {self.identifiers} are still in the identifier list and were not parsed.")

    def animalID(self):
        reg = re.compile(r"^(\d+)_data")
        return reg.findall(self.pathobj.name)[0]

    def daysAfterBaseline(self):
        reg = re.compile(r"DAY_(\d+)")
        return reg.findall(str(self.pathobj.parent))[0]

    def conditionID(self):
        reg = re.compile(r"(HYPER|HYPO)")
        return reg.findall(str(self.pathobj.parent))[0]

    def FOV(self):
        reg = re.compile(r"FOV_(\d+)")
        return reg.findall(str(self.pathobj.parent))[0]


@attr.s(slots=True)
class DataExtractor(object):
    """ Extract and concatenate data from a nexted list of outputs """

    list_of_data = attr.ib()
    unstacked_data = attr.ib(init=False)

    def unstack_data(self):
        num_of_fields = len(self.list_of_data)
        self.unstacked_data = []
