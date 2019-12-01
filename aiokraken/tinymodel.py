import contextlib
import datetime
from collections import Mapping, OrderedDict

import pytz
from tinydb import TinyDB, Query


class TinyModel(Mapping):

    def __init__(self, class_name, persist_db):
        self._persist = persist_db
        self._name = class_name
        self.table = persist_db.table(class_name, )
        self.idx = OrderedDict()  # some kind of cache ??

    def __getitem__(self, item):
        if item in self.idx:
            item_val = self.table.get(doc_id=self.idx[item])
        else:  # search
            q = Query()
            item_res = self.table.search(q.name == item)
            assert isinstance(item_res, list)
            if not item_res:
                raise KeyError(f"{item} not found")
            else:
                item_val = item_res[0]  # get the first result
                # TODO : should be unique...
                self.idx[item] = item_val.doc_id
        return item_val

    def __iter__(self):
        return iter([e.get('name', 'UNKNOWN') for e in self.table])

    def __len__(self):
        return len(self.table)


class TinyMutableModel(TinyModel):

    def __init__(self, class_name, persist_db):
        super(TinyMutableModel, self).__init__(class_name=class_name, persist_db=persist_db)
        self.past = persist_db.table("Past")
        #TODO : mergeable ?? CRDT ?? distributed DAG ?

    def __setitem__(self, key, value):
        name_pair = {'name': key}  # AKA "the indexing problem"
        data = {k: v for k, v in value.items()}
        data.update(name_pair)

        if key in self and self[key] != data:
            # tracking past events if there is a difference...
            self.past.insert({
                'table': self.table.name,
                'until': datetime.datetime.now(tz=pytz.utc).isoformat(),
                key: self[key]  # get the current version
            })

        # By default we do not track time. Present is now.
        docid = self.table.insert(data)

        self.idx[key] = docid


@contextlib.contextmanager
def mutate(model: TinyModel):

    yield TinyMutableModel(class_name=model._name, persist_db=model._persist)

    return model



if __name__ == '__main__':

    class DataModel:
        def __init__(self, value):
            self.myvalue = value

    m = TinyMutableModel("DataModel", persist_db=TinyDB('tinymodel.json'))

    m['test1'] = vars(DataModel(value = 42))
    m['test2'] = vars(DataModel(value=51))

    assert m['test1'] == {'name': 'test1', 'myvalue': 42}, print(m.get('test1'))
    assert m['test2'] == {'name': 'test2', 'myvalue': 51}, print(m.get('test2'))