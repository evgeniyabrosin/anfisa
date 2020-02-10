#  Copyright (c) 2019. Partners HealthCare and other members of
#  Forome Association
#
#  Developed by Sergey Trifonov based on contributions by Joel Krier,
#  Michael Bouzinier, Shamil Sunyaev and other members of Division of
#  Genetics, Brigham and Women's Hospital
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import sys, codecs, json, os, shutil, re, time, logging
from argparse import ArgumentParser

import utils.json_conf as json_conf
from app.prepare.druid_adm import DruidAdmin
from app.prepare.html_report import reportDS
from app.prepare.doc_works import prepareDocDir
from app.prepare.ds_create import createDS
from app.config.solutions import readySolutions
from app.model.mongo_db import MongoConnector
#=====================================
try:
    sys.stdin  = codecs.getreader('utf8')(sys.stdin.detach())
    sys.stderr = codecs.getwriter('utf8')(sys.stderr.detach())
    sys.stdout = codecs.getwriter('utf8')(sys.stdout.detach())
except Exception:
    pass

if sys.version_info < (3, 7):
    from backports.datetime_fromisoformat import MonkeyPatch
    MonkeyPatch.patch_fromisoformat()

#===============================================
sID_Pattern = re.compile('^\\S+$', re.U)

def checkDSName(name, kind):
    global sID_Pattern
    if not sID_Pattern.match(name) or not name[0].isalpha():
        print("Incorrect dataset name:", name, file=sys.stderr)
        assert False
    if kind == "ws":
        if name.lower().startswith("xl_"):
            print("Improper WS name:", name, file = sys.stderr)
            print("(Should not have prefix XL_)", file = sys.stderr)
            assert False
    elif kind == "xl":
        if not name.lower().startswith("xl_"):
            print("Improper XL-dataset name:", name, file = sys.stderr)
            print("(Should have prefix XL_ or xl_)", file = sys.stderr)
            assert False
    else:
        print("Wrong dataset kind:", kind)
        assert False

#===============================================
def createDataSet(app_config, ds_entry, force_drop, druid_adm, report_lines):
    readySolutions()

    if not ds_entry.getSource():
        print("Improper creation datset",  ds_entry.getName(),  ": no source")
        sys.exit()

    vault_dir = app_config["data-vault"]
    if force_drop:
        dropDataSet(app_config, ds_entry, druid_adm, True)

    if not os.path.isdir(vault_dir):
        os.mkdir(vault_dir)
        print("Create (empty) vault directory:", vault_dir, file = sys.stderr)

    checkDSName(ds_entry.getName(), ds_entry.getDSKind())
    ds_dir = os.path.abspath(vault_dir + "/" + ds_entry.getName())
    if os.path.exists(ds_dir):
        print("Dataset exists:", ds_dir, file = sys.stderr)
        assert False
    os.mkdir(ds_dir)

    mongo_conn = MongoConnector(app_config["mongo-db"],
        app_config.get("mongo-host"), app_config.get("mongo-port"))

    createDS(ds_dir, mongo_conn, druid_adm,
        ds_entry.getName(), ds_entry.getSource(), ds_entry.getDSKind(),
        ds_entry.getInv(), report_lines)

#===============================================
def pushDruid(app_config, ds_entry, druid_adm):
    vault_dir = app_config["data-vault"]
    if not os.path.isdir(vault_dir):
        print("No vault directory:", vault_dir, file = sys.stderr)
        assert False
    if ds_entry.getDSKind() != "xl":
        print("Druid dataset %s has unexpected kind %s" %
            (ds_entry.getName(),  ds_entry.getDSKind()),
            file = sys.stderr)
        sys.exit()
    checkDSName(ds_entry.getName(), "xl")

    druid_datasets = druid_adm.listDatasets()
    if ds_entry.getName() in druid_datasets:
        druid_adm.dropDataset(ds_entry.getName())

    ds_dir = os.path.abspath(vault_dir + "/" + ds_entry.getName())
    with open(ds_dir + "/dsinfo.json",
            "r", encoding = "utf-8") as inp:
        ds_info = json.loads(inp.read())
    is_ok = druid_adm.uploadDataset(ds_entry.getName(),
        ds_info["flt_schema"],
        os.path.abspath(ds_dir + "/fdata.json.gz"),
        os.path.abspath(ds_dir + "/druid_rq.json"))
    if is_ok:
        print("Druid dataset %s pushed" % ds_entry.getName())
    else:
        print("Process failed")

#===============================================
def dropDataSet(app_config, ds_entry, druid_adm, calm_mode):
    assert ds_entry.getDSKind() in ("ws", "xl")
    vault_dir = app_config["data-vault"]
    ds_dir = os.path.abspath(vault_dir + "/" + ds_entry.getName())

    if ds_entry.getDSKind() == "xl":
        if calm_mode:
            druid_datasets = druid_adm.listDatasets()
        else:
            druid_datasets = [ds_entry.getName()]
        if ds_entry.getName() in druid_datasets:
            druid_adm.dropDataset(ds_entry.getName())
        elif not calm_mode:
            print("No dataset in Druid to drop:", ds_entry.getName())

    if not os.path.exists(ds_dir):
        if not calm_mode:
            print("No dataset to drop:", ds_dir)
        return
    shutil.rmtree(ds_dir)
    print("Dataset droped:", ds_dir)

#===============================================
def pushDoc(app_config, ds_entry):
    vault_dir = app_config["data-vault"]
    ds_dir = os.path.abspath(vault_dir + "/" + ds_entry.getName())

    with open(ds_dir + "/dsinfo.json",
            "r", encoding = "utf-8") as inp:
        ds_info = json.loads(inp.read())
    ds_doc_dir = ds_dir + "/doc"
    ds_info["doc"] = prepareDocDir(ds_doc_dir, ds_entry.getInv(), reset = True)

    mongo_conn = MongoConnector(app_config["mongo-db"],
        app_config.get("mongo-host"), app_config.get("mongo-port"))
    mongo_agent = mongo_conn.getDSAgent(ds_info["name"], ds_info["kind"])
    with open(ds_dir + "/dsinfo.json", "w", encoding = "utf-8") as outp:
        print(json.dumps(ds_info, sort_keys = True, indent = 4),
            file = outp)

    with open(ds_doc_dir + "/info.html", "w", encoding = "utf-8") as outp:
        reportDS(outp, ds_info, mongo_agent)

    print("Re-doc complete:", ds_dir)

#===============================================
class DSEntry:
    def __init__(self,  ds_name,  ds_kind,  source,  ds_inventory = None,
            entry_data = None):
        self.mName = ds_name
        self.mKind = ds_kind
        self.mSource = source
        self.mInv  = ds_inventory
        self.mEntryData = entry_data

    def getName(self):
        return self.mName

    def getDSKind(self):
        return self.mKind

    def getSource(self):
        return self.mSource

    def getInv(self):
        return self.mInv

    def dump(self):
        return {
            "name": self.mName,
            "kind": self.mKind,
            "source": self.mSource,
            "inv": self.mInv,
            "data": self.mEntryData}

    @classmethod
    def createByDirConfig(cls, ds_name,  dir_config,  dir_fname):
        if ds_name not in dir_config["datasets"]:
            print("Dataset %s not registered in directory file (%s)" %
                (ds_name, dir_fname), file = sys.stderr)
            sys.exit()
        ds_entry_data = dir_config["datasets"][ds_name]
        if "inv" in ds_entry_data:
            ds_inventory = json_conf.loadDatasetInventory(ds_entry_data["inv"])
            return DSEntry(ds_name,
                ds_entry_data["kind"], ds_inventory["a-json"], ds_inventory,
                entry_data = {
                    "arg-dir": ds_entry_data, "arg-inv": ds_inventory})
        if "a-json" in ds_entry_data:
            return DSEntry(ds_name,  ds_entry_data["kind"],
                ds_entry_data["a-json"],
                entry_data = {"arg-dir": ds_entry_data})
        print(("Dataset %s: no correct source or inv registered "
            "in directory file (%s)") % (ds_name, dir_fname),
            file = sys.stderr)
        sys.exit()
        return None


#===============================================
if __name__ == '__main__':
    logging.root.setLevel(logging.INFO)

    parser = ArgumentParser()
    parser.add_argument("-d", "--dir",
        help = "Storage directory control file")
    parser.add_argument("-c", "--config",
        help = "Anfisa configuration file, used only if --dir is unset, "
        "default = anfisa.json")
    parser.add_argument("-m", "--mode",
        help = "Mode: create/drop/druid-push/doc-push")
    parser.add_argument("-k", "--kind",  default = "ws",
        help = "Kind of dataset: ws/xl, default = ws, "
        "actual if --dir is unset")
    parser.add_argument("-s", "--source", help="Annotated json, "
        "actual if --dir is unset and mode = create")
    parser.add_argument("-i", "--inv", help="Annotation inventory")
    parser.add_argument("-f", "--force", action = "store_true",
        help = "Force removal, actual if mode = create")
    parser.add_argument("-C", "--nocoord", action = "store_true",
        help = "Druid: no use coordinator")
    parser.add_argument("--reportlines", type = int, default = 100,
        help = "Portion for report lines, default = 100")
    parser.add_argument("--delay",  type = int,  default = 0,
        help = "Delay between work with multiple datasets, in seconds")
    parser.add_argument("names", nargs = "+", help = "Dataset name(s)")
    args = parser.parse_args()

    if args.dir:
        if args.config or args.source or args.inv:
            print("Incorrect usage: use --dir or "
                "(--config, [--source, --inv])")
            sys.exit()
        dir_config = json.loads(
            json_conf.readCommentedJSon(args.dir))
        service_config_file = dir_config["anfisa.json"]
        if len(set(args.names)) != len(args.names):
            dup_names = args.names[:]
            for ds_name in set(args.names):
                dup_names.remove(ds_name)
            print("Incorrect usage: ds name duplication:", " ".join(dup_names))
            sys.exit()
        entries = [DSEntry.createByDirConfig(ds_name,  dir_config, args.dir)
            for ds_name in args.names]
    else:
        if args.source and args.inv:
            print("Incorrect usage: use either --source or --inv")
        service_config_file = args.config
        if not service_config_file:
            service_config_file = "./anfisa.json"
        if len(args.names) != 1 and (args.source or args.inv):
            print("Incorrect usage: --source applies only to one ds")
            sys.exit()
        if args.inv:
            ds_inventory = json_conf.loadDatasetInventory(args.inv)
            ds_name = args.names[0]
            entries = [DSEntry(ds_name, args.kind, ds_inventory["a-json"],
                ds_inventory, entry_data = {"arg-inv": ds_inventory})]
        else:
            entries = [DSEntry(ds_name,  args.kind,  args.source)
                for ds_name in args.names]

    app_config = json_conf.loadJSonConfig(service_config_file)

    assert os.path.isdir(app_config["data-vault"])

    druid_adm = None
    if any(ds_entry.getDSKind() == "xl" for ds_entry in entries):
        druid_adm = DruidAdmin(app_config, args.nocoord)

    for entry_no,  ds_entry in enumerate(entries):
        if entry_no > 0 and args.delay > 0:
            time.sleep(args.delay)
        if args.mode == "create":
            createDataSet(app_config, ds_entry, args.force,
                druid_adm, args.reportlines)
        elif args.mode == "drop":
            dropDataSet(app_config, ds_entry, druid_adm, False)
        elif args.mode == "druid-push":
            pushDruid(app_config, ds_entry, druid_adm)
        elif args.mode == "doc-push":
            pushDoc(app_config, ds_entry)
        elif args.mode == "debug-info":
            print("Info:", json.dumps(
                ds_entry.dump(), indent = 4, sort_keys = True))
        else:
            print("Bad mode:", args.mode)
            sys.exit()

#===============================================
