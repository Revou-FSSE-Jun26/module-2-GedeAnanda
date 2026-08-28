def test_get_categories_empty(client):
    response = client.get('/categories')
    assert response.status_code == 200
    assert response.get_json()['data'] == []


def test_get_categories_with_data(client, sample_category):
    response = client.get('/categories')
    assert response.status_code == 200

    data = response.get_json()['data']
    assert len(data) == 1
    assert data[0]['name'] == 'Electronics'


def test_get_category_by_id(client, sample_category):
    response = client.get(f'/categories/{sample_category.id}')
    assert response.status_code == 200

    data = response.get_json()['data']
    assert data['name'] == 'Electronics'
    assert data['products'] == []


def test_get_category_includes_products(client, sample_category, sample_product):
    response = client.get(f'/categories/{sample_category.id}')
    assert response.status_code == 200

    data = response.get_json()['data']
    assert len(data['products']) == 1
    assert data['products'][0]['name'] == 'Laptop'


def test_get_category_not_found(client):
    response = client.get('/categories/9999')
    assert response.status_code == 404
    assert 'error' in response.get_json()


def test_create_category(client, admin_headers):
    response = client.post('/categories', headers=admin_headers, json={
        "name": "Books",
        "description": "Reading material"
    })
    assert response.status_code == 201

    data = response.get_json()['data']
    assert data['name'] == 'Books'
    assert data['description'] == 'Reading material'
    assert 'id' in data


def test_create_category_without_description(client, admin_headers):
    response = client.post('/categories', headers=admin_headers, json={
        "name": "Books"
    })
    assert response.status_code == 201
    assert response.get_json()['data']['description'] is None


def test_create_category_missing_name(client, admin_headers):
    response = client.post('/categories', headers=admin_headers, json={
        "description": "No name here"
    })
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_create_category_blank_name(client, admin_headers):
    response = client.post('/categories', headers=admin_headers, json={
        "name": "   "
    })
    assert response.status_code == 400


def test_create_category_empty_body(client, admin_headers):
    response = client.post('/categories', headers=admin_headers, json={})
    assert response.status_code == 400


def test_create_category_requires_auth(client):
    response = client.post('/categories', json={"name": "Books"})
    assert response.status_code == 401


def test_create_category_forbidden_for_customer(client, customer_headers):
    response = client.post('/categories', headers=customer_headers, json={
        "name": "Books"
    })
    assert response.status_code == 403


def test_update_category(client, admin_headers, sample_category):
    response = client.put(f'/categories/{sample_category.id}',
    headers=admin_headers,
    json={"name": "Updated Electronics"})
    assert response.status_code == 200
    assert response.get_json()['data']['name'] == 'Updated Electronics'


def test_update_category_not_found(client, admin_headers):
    response = client.put('/categories/9999',
    headers=admin_headers,
    json={"name": "Ghost"})
    assert response.status_code == 404


def test_update_category_missing_name(client, admin_headers, sample_category):
    response = client.put(f'/categories/{sample_category.id}',
    headers=admin_headers,
    json={"description": "Only description"})
    assert response.status_code == 400


def test_update_category_forbidden_for_customer(client, customer_headers, sample_category):
    response = client.put(f'/categories/{sample_category.id}',
    headers=customer_headers,
    json={"name": "Hacked"})
    assert response.status_code == 403


def test_delete_category(client, admin_headers, sample_category):
    response = client.delete(f'/categories/{sample_category.id}',
    headers=admin_headers)
    assert response.status_code == 200

    follow_up = client.get(f'/categories/{sample_category.id}')
    assert follow_up.status_code == 404


def test_delete_category_not_found(client, admin_headers):
    response = client.delete('/categories/9999', headers=admin_headers)
    assert response.status_code == 404


def test_delete_category_with_products_blocked(client, admin_headers, sample_category, sample_product):
    response = client.delete(f'/categories/{sample_category.id}',
    headers=admin_headers)
    assert response.status_code == 409
    assert 'error' in response.get_json()


def test_delete_category_forbidden_for_customer(client, customer_headers, sample_category):
    response = client.delete(f'/categories/{sample_category.id}',
    headers=customer_headers)
    assert response.status_code == 403