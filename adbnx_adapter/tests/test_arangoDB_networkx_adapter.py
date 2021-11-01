from conftest import arango_restore, adbnx_adapter


def test_fraud_data():
    arango_restore("fraud_dump")
    assert adbnx_adapter.db.has_collection('account') == True

# def test_dgl_data():
#     # Cannot co-exist with test_fraud_data() at the momment
#     assert adbnx_adapter.db.has_collection('customer') == False
#     arango_restore("dgl_data_dump")

def test_imdb_data():
    arango_restore("imdb_dump")
    assert adbnx_adapter.db.has_collection('Movies') == True