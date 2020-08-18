import pytest
# TMP
#
# from aiokraken.rest.api import Request, Server
# from aiokraken.rest.client import RestClient
#
#
# def test_request():
#
#     r = Request(url='proto://some/url', headers={}, data={})
#
#     assert hasattr(r, 'url')
#     assert hasattr(r, 'headers')
#     assert hasattr(r, 'data')
#
#
# @pytest.mark.vcr()
# def test_time():
#     response = RestClient(host="api.kraken.com", api = Server()).time()
#     print(response)
#     assert isinstance(response, Time)
#
#
#
#
# if __name__ == '__main__':
#     pytest.main(['-s', __file__])
