import requests
import responses

@responses.activate
def test_get_catalog_product():
    # Mock the Catalog Service response
    responses.add(responses.GET, 'http://catalog/products/1',
                  json={'id': 1, 'name': 'Laptop', 'price': 999}, status=200)

    response = requests.get('http://catalog/products/1')
    assert response.status_code == 200
    assert response.json()['name'] == 'Laptop'